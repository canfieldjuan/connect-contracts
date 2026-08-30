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


def _parameter_type_matches(value_type: str, value: object) -> bool:
    return (
        (value_type == "string" and isinstance(value, str))
        or (value_type == "integer" and type(value) is int)
        or (value_type == "boolean" and type(value) is bool)
    )


def _job_request_errors(instance: dict, capabilities: list[dict]) -> list[str]:
    reference = (instance["capability"]["id"], instance["capability"]["version"])
    candidates = [
        capability
        for capability in capabilities
        if (capability["id"], capability["version"]) == reference
    ]
    if not candidates:
        return [f"job request capability is not declared: {reference}"]

    candidate_errors: list[list[str]] = []
    for capability in candidates:
        errors: list[str] = []
        input_artifact = instance["inputs"][0]
        accepted = next(
            (
                item
                for item in capability["accepts"]
                if item["media_type"] == input_artifact["media_type"]
            ),
            None,
        )
        if accepted is None:
            errors.append("job request input media type is not accepted")
        elif input_artifact["byte_size"] > accepted["max_bytes"]:
            errors.append("job request input exceeds the declared size limit")

        declared_parameters = {
            parameter["name"]: parameter for parameter in capability["parameters"]
        }
        supplied_parameters = instance["parameters"]
        for name, parameter in declared_parameters.items():
            if parameter["required"] and name not in supplied_parameters:
                errors.append(f"required job parameter is missing: {name}")
        for name, value in supplied_parameters.items():
            declaration = declared_parameters.get(name)
            if declaration is None:
                errors.append(f"job parameter is undeclared: {name}")
            elif not _parameter_type_matches(declaration["value_type"], value):
                errors.append(f"job parameter has the wrong type: {name}")

        if not errors:
            return []
        candidate_errors.append(errors)
    return min(candidate_errors, key=len)


def semantic_errors(
    version: str,
    schema_name: str,
    instance: dict,
    capabilities: list[dict] | None = None,
) -> list[str]:
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

            accepted_media_types: set[str] = set()
            for accepted in capability["accepts"]:
                media_type = accepted["media_type"]
                if media_type in accepted_media_types:
                    errors.append(f"duplicate accepted media type: {media_type}")
                accepted_media_types.add(media_type)

            parameter_names: set[str] = set()
            for parameter in capability["parameters"]:
                name = parameter["name"]
                if name in parameter_names:
                    errors.append(f"duplicate parameter name: {name}")
                parameter_names.add(name)

    if schema_name == "job-request.schema.json":
        errors.extend(_job_request_errors(instance, capabilities or []))

    if schema_name == "job-status.schema.json" and instance["status"] == "completed":
        artifact_ids: set[str] = set()
        for output in instance["result"]["outputs"]:
            artifact_id = output["artifact_id"]
            if artifact_id in artifact_ids:
                errors.append(f"duplicate output artifact_id: {artifact_id}")
            artifact_ids.add(artifact_id)
            try:
                payload = base64.b64decode(output["payload_base64"], validate=True)
            except (binascii.Error, ValueError):
                errors.append("output payload is not canonical base64")
                continue
            if base64.b64encode(payload).decode("ascii") != output["payload_base64"]:
                errors.append("output payload is not canonical base64")
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

                provider_manifests: dict[str, dict] = {}
                if version == "v2":
                    for case in cases:
                        if case["valid"] and case["schema"] == "manifest.schema.json":
                            manifest = json.loads(
                                (fixture_dir / case["fixture"]).read_text(encoding="utf-8")
                            )
                            provider_manifests[case["fixture"]] = manifest

                for case in cases:
                    with self.subTest(version=version, fixture=case["fixture"]):
                        instance = json.loads(
                            (fixture_dir / case["fixture"]).read_text(encoding="utf-8")
                        )
                        validator = Draft202012Validator(
                            schemas[case["schema"]], format_checker=FormatChecker()
                        )
                        schema_errors = list(validator.iter_errors(instance))
                        capabilities = None
                        if (
                            version == "v2"
                            and case["schema"] == "job-request.schema.json"
                        ):
                            provider_fixture = case.get("provider_manifest")
                            self.assertIsInstance(provider_fixture, str)
                            self.assertIn(provider_fixture, provider_manifests)
                            capabilities = provider_manifests[provider_fixture][
                                "capabilities"
                            ]
                        contract_errors = (
                            []
                            if schema_errors
                            else semantic_errors(
                                version,
                                case["schema"],
                                instance,
                                capabilities,
                            )
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

    def test_valid_v2_job_statuses_match_a_declared_provider_capability(self) -> None:
        fixture_dir = FIXTURES / "v2"
        cases = json.loads((fixture_dir / "index.json").read_text(encoding="utf-8"))
        declarations: dict[tuple[str, str, str, str], set[str]] = {}
        for case in cases:
            if not case["valid"] or case["schema"] != "manifest.schema.json":
                continue
            manifest = json.loads((fixture_dir / case["fixture"]).read_text(encoding="utf-8"))
            for capability in manifest["capabilities"]:
                attribution = (
                    manifest["app"]["id"],
                    manifest["instance_id"],
                    capability["id"],
                    capability["version"],
                )
                declarations.setdefault(attribution, set()).update(capability["produces"])

        for case in cases:
            if not case["valid"] or case["schema"] != "job-status.schema.json":
                continue
            status = json.loads((fixture_dir / case["fixture"]).read_text(encoding="utf-8"))
            attribution = (
                status["provider"]["app_id"],
                status["provider"]["instance_id"],
                status["capability"]["id"],
                status["capability"]["version"],
            )
            self.assertIn(attribution, declarations, case["fixture"])
            if status["status"] == "completed":
                for output in status["result"]["outputs"]:
                    self.assertIn(
                        output["media_type"],
                        declarations[attribution],
                        case["fixture"],
                    )


if __name__ == "__main__":
    unittest.main()
