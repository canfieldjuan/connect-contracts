import base64
import binascii
import hashlib
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "fixtures"
SCHEMA_NAMES = {
    "error.schema.json",
    "job-request.schema.json",
    "job-status.schema.json",
    "manifest.schema.json",
    "registration.schema.json",
}


def semantic_errors(version: str, schema_name: str, instance: dict) -> list[str]:
    if version != "v2":
        return []

    errors: list[str] = []
    if schema_name == "manifest.schema.json":
        capability_keys: set[tuple[str, str]] = set()
        for capability in instance["capabilities"]:
            capability_key = (capability["id"], capability["version"])
            if capability_key in capability_keys:
                errors.append(f"duplicate capability declaration: {capability_key}")
            capability_keys.add(capability_key)

            parameter_names: set[str] = set()
            for parameter in capability["parameters"]:
                name = parameter["name"]
                if name in parameter_names:
                    errors.append(f"duplicate parameter name: {name}")
                parameter_names.add(name)

    if schema_name == "job-status.schema.json" and instance["status"] == "completed":
        for output in instance["result"]["outputs"]:
            try:
                payload = base64.b64decode(output["payload_base64"], validate=True)
            except (binascii.Error, ValueError):
                errors.append("output payload is not canonical base64")
                continue
            if len(payload) != output["byte_size"]:
                errors.append("output payload byte_size does not match")
            if hashlib.sha256(payload).hexdigest() != output["sha256"]:
                errors.append("output payload sha256 does not match")
    return errors


class ConnectContractTests(unittest.TestCase):
    def test_schemas_are_valid_and_fixtures_match_expectations(self) -> None:
        versions = sorted(path.name for path in FIXTURES.iterdir() if path.is_dir())
        self.assertEqual(versions, ["v1", "v2"])

        for version in versions:
            with self.subTest(version=version):
                fixture_dir = FIXTURES / version
                schema_dir = SCHEMAS / version
                cases = json.loads(
                    (fixture_dir / "index.json").read_text(encoding="utf-8")
                )
                self.assertGreater(len(cases), 0)

                schemas = {}
                for path in sorted(schema_dir.glob("*.schema.json")):
                    schema = json.loads(path.read_text(encoding="utf-8"))
                    Draft202012Validator.check_schema(schema)
                    schemas[path.name] = schema

                self.assertEqual(set(schemas), SCHEMA_NAMES)
                self.assertEqual({case["schema"] for case in cases}, SCHEMA_NAMES)

                for case in cases:
                    with self.subTest(version=version, fixture=case["fixture"]):
                        instance = json.loads(
                            (fixture_dir / case["fixture"]).read_text(encoding="utf-8")
                        )
                        validator = Draft202012Validator(
                            schemas[case["schema"]], format_checker=FormatChecker()
                        )
                        schema_errors = list(validator.iter_errors(instance))
                        contract_errors = (
                            []
                            if schema_errors
                            else semantic_errors(version, case["schema"], instance)
                        )
                        errors = (
                            [error.message for error in schema_errors] + contract_errors
                        )
                        if case["valid"]:
                            self.assertEqual(errors, [])
                        else:
                            self.assertNotEqual(
                                errors, [], "invalid fixture unexpectedly passed"
                            )


if __name__ == "__main__":
    unittest.main()
