"""Offline v3 metadata conformance, not a runtime streaming implementation."""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from tests.test_contracts import semantic_errors


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures/v3"
MAX_OUTPUT_BYTES = 37_748_736


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def errors_for(schema_name, document, manifest=None, request=None):
    schema = load(ROOT / "schemas/v3" / schema_name)
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            document
        )
    )
    if not errors:
        errors.extend(semantic_errors("v3", schema_name, document, manifest, request))
    return errors


class StreamedContractTests(unittest.TestCase):
    def test_v3_contract_is_published_separately(self):
        self.assertTrue(
            (ROOT / "schemas/v3/job-status.schema.json").is_file(),
            "v3 descriptor schema must be separate from the frozen inline v2 schema",
        )

    def test_schema_documents_are_valid(self):
        for name in ("registration", "manifest", "job-request", "job-status", "error"):
            with self.subTest(name=name):
                schema = load(ROOT / "schemas/v3" / f"{name}.schema.json")
                Draft202012Validator.check_schema(schema)
                self.assertEqual(schema["properties"]["protocol_version"], {"const": 3})

    def test_fixture_inventory_is_complete(self):
        index = load(FIXTURES / "index.json")
        listed = {case["fixture"] for case in index}
        present = {
            str(path.relative_to(FIXTURES)) for path in FIXTURES.glob("*/*.json")
        }
        self.assertEqual(listed, present)
        self.assertEqual(len(index), len(listed))

    def test_output_size_boundaries_and_falsy_values(self):
        original = load(FIXTURES / "valid/job-completed-generic.json")
        for size, valid in (
            (0, True),
            (1, True),
            (MAX_OUTPUT_BYTES - 1, True),
            (MAX_OUTPUT_BYTES, True),
            (MAX_OUTPUT_BYTES + 1, False),
            (-1, False),
            (False, False),
            ("", False),
            (None, False),
        ):
            with self.subTest(size=repr(size)):
                document = copy.deepcopy(original)
                document["result"]["outputs"][0]["byte_size"] = size
                self.assertEqual(
                    not errors_for("job-status.schema.json", document), valid
                )

    def test_ocr_pair_boundaries(self):
        original = load(FIXTURES / "valid/job-completed-ocr-large.json")
        for index, cap in ((0, MAX_OUTPUT_BYTES), (1, 262_144)):
            for size in (0, 1, cap - 1, cap, cap + 1):
                with self.subTest(output=index, size=size):
                    document = copy.deepcopy(original)
                    document["result"]["outputs"][index]["byte_size"] = size
                    self.assertEqual(
                        not errors_for("job-status.schema.json", document),
                        0 < size <= cap,
                    )

    def test_output_count_boundaries(self):
        original = load(FIXTURES / "valid/job-completed-generic.json")
        template = original["result"]["outputs"][0]
        for count in (0, 1, 8, 9):
            with self.subTest(count=count):
                document = copy.deepcopy(original)
                document["result"]["outputs"] = [
                    dict(
                        template, artifact_id=f"{index:08x}-1111-4111-8111-111111111111"
                    )
                    for index in range(count)
                ]
                self.assertEqual(
                    not errors_for("job-status.schema.json", document), 1 <= count <= 8
                )

    def test_cross_protocol_metadata_is_rejected(self):
        document = load(FIXTURES / "valid/job-completed-ocr-large.json")
        manifest = load(FIXTURES / "valid/manifest-ocr.json")
        request = load(FIXTURES / "valid/job-request-ocr.json")
        for field in (manifest, request):
            field["protocol_version"] = 2
            self.assertTrue(
                errors_for("job-status.schema.json", document, manifest, request)
            )
            field["protocol_version"] = 3

    def test_canonical_ids_cannot_supply_routes(self):
        original = load(FIXTURES / "valid/job-completed-generic.json")
        for value in (
            "../private",
            "%2e%2e",
            "http://127.0.0.1/",
            "",
            False,
            "dddddddd-dddd-4ddd-8ddd-dddddddddddd\n",
        ):
            with self.subTest(value=repr(value)):
                document = copy.deepcopy(original)
                document["result"]["outputs"][0]["artifact_id"] = value
                self.assertTrue(errors_for("job-status.schema.json", document))

    def test_retrieval_errors_are_standalone_not_job_failures(self):
        failed = load(FIXTURES / "valid/job-failed-budget.json")
        self.assertFalse(errors_for("job-status.schema.json", failed))
        for code in (
            "MALFORMED_REQUEST",
            "JOB_NOT_FOUND",
            "OUTPUT_NOT_READY",
            "OUTPUT_NOT_FOUND",
            "OUTPUT_BUSY",
            "OUTPUT_UNAVAILABLE",
        ):
            with self.subTest(code=code):
                envelope = load(FIXTURES / f"valid/error-{code.lower()}.json")
                self.assertFalse(errors_for("error.schema.json", envelope))
                document = copy.deepcopy(failed)
                document["error"] = envelope["error"]
                self.assertTrue(errors_for("job-status.schema.json", document))

    def test_ocr_budget_error_requires_exact_profile_message(self):
        valid = load(FIXTURES / "valid/job-failed-budget.json")
        self.assertFalse(errors_for("job-status.schema.json", valid))
        invalid = load(FIXTURES / "invalid/status-budget-wrong-message.json")
        self.assertTrue(errors_for("job-status.schema.json", invalid))

        # Other capabilities retain their own failure messages.
        invalid["capability"] = {"id": "document.summarize", "version": "1.0"}
        self.assertFalse(errors_for("job-status.schema.json", invalid))

    def test_digests_are_exact_lowercase_sha256(self):
        for schema, source, path in (
            ("job-request.schema.json", "job-request-generic.json", ("inputs", 0)),
            (
                "job-status.schema.json",
                "job-completed-generic.json",
                ("input_artifacts", 0),
            ),
            (
                "job-status.schema.json",
                "job-completed-generic.json",
                ("result", "outputs", 0),
            ),
        ):
            for digest, valid in (
                ("f" * 64, True),
                ("f" * 63, False),
                ("f" * 65, False),
                ("F" * 64, False),
                ("g" * 64, False),
                ("f" * 64 + "\n", False),
                ("", False),
                (False, False),
                (None, False),
            ):
                with self.subTest(schema=schema, path=path, digest=repr(digest)):
                    document = load(FIXTURES / "valid" / source)
                    artifact = document
                    for key in path:
                        artifact = artifact[key]
                    artifact["sha256"] = digest
                    self.assertEqual(not errors_for(schema, document), valid)

        # One valid descriptor cannot hide a malformed sibling in the OCR pair.
        document = load(FIXTURES / "valid/job-completed-ocr-large.json")
        document["result"]["outputs"][1]["sha256"] = "f" * 63
        self.assertTrue(errors_for("job-status.schema.json", document))

    def test_descriptor_is_rejected_by_frozen_v2(self):
        document = load(FIXTURES / "valid/job-completed-ocr-large.json")
        document["protocol_version"] = 2
        document["capability"]["version"] = "1.0"
        validator = Draft202012Validator(
            load(ROOT / "schemas/v2/job-status.schema.json")
        )
        self.assertFalse(validator.is_valid(document))

    def test_v2_inline_response_is_rejected_by_v3(self):
        document = load(ROOT / "fixtures/v2/valid/job-completed-ocr.json")
        document["protocol_version"] = 3
        document["capability"]["version"] = "1.1"
        self.assertTrue(errors_for("job-status.schema.json", document))


if __name__ == "__main__":
    unittest.main()
