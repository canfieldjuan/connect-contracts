import base64
import binascii
import hashlib
import json
import unittest
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "fixtures"
ENTITLEMENTS = ROOT / "entitlements"
SCHEMA_NAMES = {
    "error.schema.json",
    "job-request.schema.json",
    "job-status.schema.json",
    "manifest.schema.json",
    "registration.schema.json",
}
ENTITLEMENT_FEATURE = "connect.capability_exchange"


def _base64url_decode(value: str) -> bytes:
    if "=" in value:
        raise ValueError("base64url padding is not canonical")
    try:
        decoded = base64.b64decode(
            value + "=" * (-len(value) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid base64url") from exc
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise ValueError("base64url is not canonical")
    return decoded


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if "T" not in value or parsed.tzinfo is None:
        raise ValueError("timestamp must include time and UTC offset")
    return parsed


def _verify_entitlement(
    envelope: dict,
    *,
    key_id: str,
    public_key: bytes,
    now: datetime,
) -> tuple[bool, bool]:
    if envelope["key_id"] != key_id:
        return False, False
    try:
        payload = _base64url_decode(envelope["payload_base64url"])
        signature = _base64url_decode(envelope["signature_base64url"])
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, payload)
    except (InvalidSignature, ValueError):
        return False, False
    claims = json.loads(payload)
    claims_schema = json.loads(
        (ENTITLEMENTS / "v1/claims.schema.json").read_text(encoding="utf-8")
    )
    Draft202012Validator(
        claims_schema,
        format_checker=FormatChecker(),
    ).validate(claims)
    issued_at = _timestamp(claims["issued_at"])
    not_before = _timestamp(claims["not_before"])
    expires_at = _timestamp(claims["expires_at"])
    entitled = (
        issued_at <= not_before <= now < expires_at
        and ENTITLEMENT_FEATURE in claims["features"]
    )
    return True, entitled


def _parameter_type_matches(value_type: str, value: object) -> bool:
    return (
        (value_type == "string" and isinstance(value, str))
        or (
            value_type == "integer"
            and not isinstance(value, bool)
            and isinstance(value, (int, float))
            and (isinstance(value, int) or value.is_integer())
        )
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


def _job_status_errors(instance: dict, provider_manifest: dict) -> list[str]:
    provider = instance["provider"]
    if (
        provider["app_id"] != provider_manifest["app"]["id"]
        or provider["instance_id"] != provider_manifest["instance_id"]
    ):
        return ["job status provider does not match the selected manifest"]
    reference = (instance["capability"]["id"], instance["capability"]["version"])
    capability = next(
        (
            candidate
            for candidate in provider_manifest["capabilities"]
            if (candidate["id"], candidate["version"]) == reference
        ),
        None,
    )
    if capability is None:
        return [f"job status capability is not declared: {reference}"]

    errors: list[str] = []
    accepted_limits = {
        accepted["media_type"]: accepted["max_bytes"] for accepted in capability["accepts"]
    }
    for input_artifact in instance["input_artifacts"]:
        limit = accepted_limits.get(input_artifact["media_type"])
        if limit is None:
            errors.append("job status input media type is not accepted")
        elif input_artifact["byte_size"] > limit:
            errors.append("job status input exceeds the declared size limit")
    if instance["status"] == "completed":
        produced_types = set(capability["produces"])
        for output in instance["result"]["outputs"]:
            if output["media_type"] not in produced_types:
                errors.append("job status output media type is not declared")
    return errors


def _registration_manifest_errors(registration: dict, manifest: dict) -> list[str]:
    errors: list[str] = []
    if registration["app_id"] != manifest["app"]["id"]:
        errors.append("registration app does not match the fetched manifest")
    if registration["instance_id"] != manifest["instance_id"]:
        errors.append("registration instance does not match the fetched manifest")
    return errors


def _job_status_request_errors(status: dict, request: dict) -> list[str]:
    errors: list[str] = []
    if status["job_id"] != request["job_id"]:
        errors.append("job status identity does not match its request")
    if status["capability"] != request["capability"]:
        errors.append("job status capability does not match its request")
    expected_inputs = [
        {
            key: input_artifact[key]
            for key in ("artifact_id", "media_type", "byte_size", "sha256")
        }
        for input_artifact in request["inputs"]
    ]
    if status["input_artifacts"] != expected_inputs:
        errors.append("job status input provenance does not match its request")
    return errors


def semantic_errors(
    version: str,
    schema_name: str,
    instance: dict,
    provider_manifest: dict | None = None,
    job_request: dict | None = None,
) -> list[str]:
    if version != "v2":
        return []

    errors: list[str] = []
    if schema_name == "registration.schema.json":
        try:
            port = urlsplit(instance["transport"]["base_url"]).port
        except ValueError:
            port = None
        if port is None or not 1 <= port <= 65_535:
            errors.append("registration loopback port is out of range")
        if provider_manifest is not None:
            errors.extend(_registration_manifest_errors(instance, provider_manifest))

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
        errors.extend(
            _job_request_errors(
                instance,
                provider_manifest["capabilities"] if provider_manifest else [],
            )
        )

    if schema_name == "job-status.schema.json" and provider_manifest is not None:
        errors.extend(_job_status_errors(instance, provider_manifest))
    if schema_name == "job-status.schema.json" and job_request is not None:
        errors.extend(_job_status_request_errors(instance, job_request))

    if schema_name == "job-status.schema.json" and instance["status"] == "completed":
        artifact_ids = {
            input_artifact["artifact_id"] for input_artifact in instance["input_artifacts"]
        }
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
    def test_entitlement_v1_fixtures_match_schema_signature_and_time_contract(self) -> None:
        root = ENTITLEMENTS / "v1"
        envelope_schema = json.loads(
            (root / "envelope.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(envelope_schema)
        claims_schema = json.loads((root / "claims.schema.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(claims_schema)
        keyring_schema = json.loads(
            (root / "keyring.schema.json").read_text(encoding="utf-8")
        )
        Draft202012Validator.check_schema(keyring_schema)
        keyring = json.loads(
            (root / "fixtures/test-keyring.json").read_text(encoding="utf-8")
        )
        Draft202012Validator(keyring_schema).validate(keyring)
        self.assertEqual(
            len({key["key_id"] for key in keyring["keys"]}),
            len(keyring["keys"]),
        )
        index = json.loads((root / "fixtures/index.json").read_text(encoding="utf-8"))
        key_fixture = keyring["keys"][0]
        public_key = _base64url_decode(key_fixture["public_key_base64url"])
        now = _timestamp(index["evaluated_at"])

        for case in index["cases"]:
            with self.subTest(fixture=case["fixture"]):
                envelope = json.loads(
                    (root / "fixtures" / case["fixture"]).read_text(encoding="utf-8")
                )
                schema_errors = list(
                    Draft202012Validator(envelope_schema).iter_errors(envelope)
                )
                self.assertEqual(not schema_errors, case["schema_valid"])
                if schema_errors:
                    self.assertFalse(case["signature_valid"])
                    self.assertFalse(case["entitled"])
                    continue
                signature_valid, entitled = _verify_entitlement(
                    envelope,
                    key_id=key_fixture["key_id"],
                    public_key=public_key,
                    now=now,
                )
                self.assertEqual(signature_valid, case["signature_valid"])
                self.assertEqual(entitled, case["entitled"])

    def test_entitlement_v1_time_boundaries_are_exact_and_claims_are_strict(self) -> None:
        root = ENTITLEMENTS / "v1"
        claims_schema = json.loads((root / "claims.schema.json").read_text(encoding="utf-8"))
        envelope = json.loads(
            (root / "fixtures/valid/active.json").read_text(encoding="utf-8")
        )
        key_fixture = json.loads(
            (root / "fixtures/test-keyring.json").read_text(encoding="utf-8")
        )["keys"][0]
        public_key = _base64url_decode(key_fixture["public_key_base64url"])
        claims = json.loads(_base64url_decode(envelope["payload_base64url"]))
        issued_at = _timestamp(claims["issued_at"])
        not_before = _timestamp(claims["not_before"])
        expires_at = _timestamp(claims["expires_at"])

        self.assertLessEqual(issued_at, not_before)
        self.assertEqual(
            _verify_entitlement(
                envelope,
                key_id=key_fixture["key_id"],
                public_key=public_key,
                now=not_before,
            ),
            (True, True),
        )
        self.assertEqual(
            _verify_entitlement(
                envelope,
                key_id=key_fixture["key_id"],
                public_key=public_key,
                now=expires_at,
            ),
            (True, False),
        )

        duplicate = {**claims, "features": [ENTITLEMENT_FEATURE, ENTITLEMENT_FEATURE]}
        errors = list(Draft202012Validator(claims_schema).iter_errors(duplicate))
        self.assertTrue(errors)
        unknown = {**claims, "unexpected": True}
        errors = list(Draft202012Validator(claims_schema).iter_errors(unknown))
        self.assertTrue(errors)
        offset_timestamp = {**claims, "expires_at": "2027-01-01T00:00:00+00:00"}
        errors = list(Draft202012Validator(claims_schema).iter_errors(offset_timestamp))
        self.assertTrue(errors)

    def test_v2_registration_port_boundaries(self) -> None:
        registration = json.loads(
            (FIXTURES / "v2/valid/registration.json").read_text(encoding="utf-8")
        )
        registration["transport"]["base_url"] = "http://127.0.0.1:65535/"
        self.assertEqual(
            semantic_errors("v2", "registration.schema.json", registration), []
        )
        registration["transport"]["base_url"] = "http://127.0.0.1:65536/"
        self.assertEqual(
            semantic_errors("v2", "registration.schema.json", registration),
            ["registration loopback port is out of range"],
        )

    def test_v2_cross_document_identity_boundaries(self) -> None:
        fixture_dir = FIXTURES / "v2/valid"
        registration = json.loads(
            (fixture_dir / "registration.json").read_text(encoding="utf-8")
        )
        manifest = json.loads((fixture_dir / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(_registration_manifest_errors(registration, manifest), [])
        registration["app_id"] = "different-app"
        self.assertEqual(
            _registration_manifest_errors(registration, manifest),
            ["registration app does not match the fetched manifest"],
        )

        request = json.loads((fixture_dir / "job-request.json").read_text(encoding="utf-8"))
        status = json.loads((fixture_dir / "job-completed.json").read_text(encoding="utf-8"))
        self.assertEqual(_job_status_request_errors(status, request), [])
        for field, value, expected in (
            ("job_id", "99999999-9999-4999-8999-999999999999", "job status identity"),
            ("capability", {"id": "document.translate", "version": "1.0"}, "capability"),
            (
                "input_artifacts",
                [{**status["input_artifacts"][0], "sha256": "b" * 64}],
                "input provenance",
            ),
        ):
            changed = {**status, field: value}
            self.assertTrue(
                any(expected in error for error in _job_status_request_errors(changed, request))
            )

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
                job_requests: dict[str, dict] = {}
                if version == "v2":
                    for case in cases:
                        if case["valid"] and case["schema"] == "manifest.schema.json":
                            manifest = json.loads(
                                (fixture_dir / case["fixture"]).read_text(encoding="utf-8")
                            )
                            provider_manifests[case["fixture"]] = manifest
                        if case["valid"] and case["schema"] == "job-request.schema.json":
                            request = json.loads(
                                (fixture_dir / case["fixture"]).read_text(encoding="utf-8")
                            )
                            job_requests[case["fixture"]] = request

                for case in cases:
                    with self.subTest(version=version, fixture=case["fixture"]):
                        instance = json.loads(
                            (fixture_dir / case["fixture"]).read_text(encoding="utf-8")
                        )
                        validator = Draft202012Validator(
                            schemas[case["schema"]], format_checker=FormatChecker()
                        )
                        schema_errors = list(validator.iter_errors(instance))
                        provider_manifest = None
                        if (
                            version == "v2"
                            and case["schema"]
                            in {
                                "registration.schema.json",
                                "job-request.schema.json",
                                "job-status.schema.json",
                            }
                        ):
                            provider_fixture = case.get("provider_manifest")
                            self.assertIsInstance(provider_fixture, str)
                            self.assertIn(provider_fixture, provider_manifests)
                            provider_manifest = provider_manifests[provider_fixture]
                        job_request = None
                        if version == "v2" and case["schema"] == "job-status.schema.json":
                            request_fixture = case.get("request_fixture")
                            self.assertIsInstance(request_fixture, str)
                            self.assertIn(request_fixture, job_requests)
                            job_request = job_requests[request_fixture]
                        contract_errors = (
                            []
                            if schema_errors
                            else semantic_errors(
                                version,
                                case["schema"],
                                instance,
                                provider_manifest,
                                job_request,
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
        declarations: dict[tuple[str, str, str, str], dict[str, object]] = {}
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
                declarations[attribution] = {
                    "accepts": {
                        accepted["media_type"]: accepted["max_bytes"]
                        for accepted in capability["accepts"]
                    },
                    "produces": set(capability["produces"]),
                }

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
            accepted_limits = declarations[attribution]["accepts"]
            self.assertIsInstance(accepted_limits, dict)
            for input_artifact in status["input_artifacts"]:
                self.assertIn(input_artifact["media_type"], accepted_limits, case["fixture"])
                self.assertLessEqual(
                    input_artifact["byte_size"],
                    accepted_limits[input_artifact["media_type"]],
                    case["fixture"],
                )
            if status["status"] == "completed":
                for output in status["result"]["outputs"]:
                    self.assertIn(
                        output["media_type"],
                        declarations[attribution]["produces"],
                        case["fixture"],
                    )


if __name__ == "__main__":
    unittest.main()
