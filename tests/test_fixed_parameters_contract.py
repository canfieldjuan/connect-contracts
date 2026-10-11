"""Static ADR-0013 conformance; never claims an application runtime proof."""

from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator
from tests import fixed_parameters as feature

MUTATION_KILLS = {}

VECTORS = feature.load(feature.FIXTURE_DIR / "golden-fixtures.json")["vectors"]


def mismatch(vector):
    errors, actual = feature.vector_result(vector)
    return bool(errors) == vector["valid"] or (
        not errors
        and not feature.frozen_json_equal(actual, vector.get("expected_outcome"))
    )


class FixedParameterContractTests(unittest.TestCase):
    def test_quoted_header_character_classes(self):
        source = next(v["input"] for v in VECTORS if v["name"] == "exchange-legacy")
        for role in ("producer_conformance", "consumer_admission"):
            for escaped in (False, True):
                for code in range(257):
                    permitted = (
                        (code == 9 or 32 <= code <= 126 or 128 <= code <= 255)
                        if escaped
                        else (
                            code in (9, 32, 33)
                            or 35 <= code <= 91
                            or 93 <= code <= 126
                            or 128 <= code <= 255
                        )
                    )
                    with self.subTest(role=role, escaped=escaped, code=code):
                        exchange = deepcopy(source)
                        exchange["validation_role"] = role
                        text = ("\\" if escaped else "") + chr(code)
                        exchange["response_headers"]["Cache-Control"] = (
                            f'no-store, ext="{text}"'
                        )
                        self.assertEqual(
                            permitted, not feature.exchange_errors(exchange)
                        )

    def test_token_character_classes_in_both_fields(self):
        source = next(v["input"] for v in VECTORS if v["name"] == "exchange-legacy")
        tchar = "!#$%&'*+-.^_`|~0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        for role in ("producer_conformance", "consumer_admission"):
            for code in range(257):
                for field in ("Cache-Control", "Vary"):
                    with self.subTest(role=role, code=code, field=field):
                        exchange = deepcopy(source)
                        exchange["validation_role"] = role
                        char = chr(code)
                        value = (
                            f"no-store, a{char}b=ok"
                            if field == "Cache-Control"
                            else f"Accept-Encoding, Local-Connect-Manifest-Features, a{char}b"
                        )
                        exchange["response_headers"][field] = value
                        self.assertEqual(
                            char in tchar or char == ",",
                            not feature.exchange_errors(exchange),
                        )

    def test_quoted_header_tabs_in_both_roles(self):
        source = next(v["input"] for v in VECTORS if v["name"] == "exchange-legacy")
        for role in ("producer_conformance", "consumer_admission"):
            for text in ("a\tb", "a\\\tb"):
                with self.subTest(role=role, text=text):
                    exchange = deepcopy(source)
                    exchange["validation_role"] = role
                    exchange["response_headers"]["Cache-Control"] = (
                        f'no-store, ext="{text}"'
                    )
                    self.assertEqual([], feature.exchange_errors(exchange))

    def test_consumer_legacy_without_freshness_headers(self):
        exchange = deepcopy(
            next(
                v["input"]
                for v in VECTORS
                if v["name"] == "exchange-missing-ack-legacy"
            )
        )
        exchange["validation_role"] = "consumer_admission"
        exchange["response_headers"] = {}
        self.assertEqual([], feature.exchange_errors(exchange))

    def test_exchange_roles_and_malformed_freshness_mutations(self):
        original_exchange = feature.exchange_errors
        original_freshness = feature.freshness_fields

        def force_role(role):
            def mutant(exchange, current_manifest=None):
                exchange = deepcopy(exchange)
                exchange["validation_role"] = role
                return original_exchange(exchange, current_manifest)

            return mutant

        def omit_malformed(response):
            errors, directives, vary = original_freshness(response)
            return [], directives, vary

        for name, owner, mutant in (
            (
                "consumer_as_producer",
                "exchange_errors",
                force_role("producer_conformance"),
            ),
            (
                "producer_as_consumer",
                "exchange_errors",
                force_role("consumer_admission"),
            ),
            ("ignore_malformed_freshness", "freshness_fields", omit_malformed),
        ):
            with self.subTest(mutation=name), patch.object(feature, owner, mutant):
                killed = [
                    v["name"]
                    for v in VECTORS
                    if v["kind"] == "exchange" and mismatch(v)
                ]
                MUTATION_KILLS[name] = killed
                self.assertTrue(killed)

    def test_fixed_declaration_schema_accepts_required_value(self):
        manifest = feature.load(feature.ROOT / "fixtures/v2/valid/manifest.json")
        parameter = manifest["capabilities"][0]["parameters"][0]
        parameter.update(required=True, fixed_value="")
        errors = list(
            Draft202012Validator(feature.derive_manifest_schema()).iter_errors(manifest)
        )
        self.assertEqual([], [error.message for error in errors])

    def test_schema_derivation_has_only_the_owned_extension(self):
        emitted = feature.load(feature.SCHEMA_DIR / "manifest.schema.json")
        self.assertEqual(feature.derive_manifest_schema(), emitted)
        legacy = feature.load(feature.ROOT / "schemas/v2/manifest.schema.json")
        restored = deepcopy(emitted)
        for key in ("$id", "title"):
            restored[key] = legacy[key]
        restored["$defs"]["parameter"]["properties"].pop("fixed_value")
        restored["$defs"]["parameter"].pop("allOf")
        self.assertEqual(legacy, restored)
        request = feature.load(feature.ROOT / "schemas/v2/job-request.schema.json")
        self.assertEqual(
            request["properties"]["parameters"]["additionalProperties"],
            emitted["$defs"]["parameter"]["properties"]["fixed_value"],
        )
        # Deliberately alter inherited behavior: derivation equality must detect it.
        changed = deepcopy(emitted)
        changed["additionalProperties"] = True
        self.assertNotEqual(feature.derive_manifest_schema(), changed)

    def test_legacy_decoder_still_rejects_fixed_member(self):
        vector = next(v for v in VECTORS if v["name"] == "manifest-string-boundary-0")
        errors = feature.schema_errors(
            feature.BASE + "manifest.schema.json", vector["input"]
        )
        self.assertTrue(any("fixed_value" in error for error in errors))
        self.assertEqual([], feature.manifest_errors(vector["input"]))

    def test_refusal_vectors_validate_directly_against_schema(self):
        for vector in VECTORS:
            if vector["kind"] != "refusal":
                continue
            with self.subTest(vector=vector["name"]):
                errors = feature.schema_errors(
                    feature.FEATURE_BASE + "refusal.schema.json", vector["input"]
                )
                self.assertEqual(vector["valid"], not errors, errors)

    def test_refusal_schema_mutations_are_falsifiable_directly(self):
        original_load = feature.load
        path = feature.SCHEMA_DIR / "refusal.schema.json"
        for member in ("code", "retryable"):
            changed = deepcopy(original_load(path))
            changed["properties"]["body"]["allOf"][1]["properties"]["error"][
                "properties"
            ].pop(member)

            def mutant_load(candidate):
                return changed if candidate == path else original_load(candidate)

            with (
                self.subTest(member=member),
                patch.object(feature, "load", mutant_load),
            ):
                killed = [
                    v["name"]
                    for v in VECTORS
                    if v["kind"] == "refusal"
                    and bool(
                        feature.schema_errors(
                            feature.FEATURE_BASE + "refusal.schema.json", v["input"]
                        )
                    )
                    == v["valid"]
                ]
                MUTATION_KILLS["refusal_without_" + member] = killed
                self.assertTrue(killed, member)

    def test_all_feature_schemas_are_valid(self):
        for path in feature.SCHEMA_DIR.glob("*.schema.json"):
            with self.subTest(schema=path.name):
                Draft202012Validator.check_schema(feature.load(path))

    def test_all_golden_vectors(self):
        self.assertEqual(len(VECTORS), len({v["name"] for v in VECTORS}))
        for vector in VECTORS:
            with self.subTest(vector=vector["name"]):
                errors, outcome = feature.vector_result(vector)
                self.assertEqual(vector["valid"], not errors, errors)
                if not errors:
                    self.assertTrue(
                        feature.frozen_json_equal(
                            vector.get("expected_outcome"), outcome
                        )
                    )

    def test_legacy_inventory_remains_byte_identical(self):
        inventory = feature.load(feature.FIXTURE_DIR / "legacy-inventory.json")
        for name, expected in inventory["files"].items():
            with self.subTest(file=name):
                actual = hashlib.sha256((feature.ROOT / name).read_bytes()).hexdigest()
                self.assertEqual(expected, actual)

    def test_schema_mutation_oracles_are_falsifiable(self):
        original_load = feature.load
        for mutation in (
            "open_parameter",
            "optional_fixed",
            "type_blind",
            "unbounded_fixed",
        ):
            changed = deepcopy(
                original_load(feature.SCHEMA_DIR / "manifest.schema.json")
            )
            parameter = changed["$defs"]["parameter"]
            if mutation == "open_parameter":
                parameter["additionalProperties"] = True
            elif mutation == "optional_fixed":
                parameter["allOf"].pop(0)
            elif mutation == "type_blind":
                parameter["allOf"] = parameter["allOf"][:1]
            else:
                for scalar in parameter["properties"]["fixed_value"]["oneOf"] + [
                    branch["then"]["properties"]["fixed_value"]
                    for branch in parameter["allOf"][1:]
                ]:
                    for key in ("minimum", "maximum", "maxLength"):
                        scalar.pop(key, None)

            def mutant_load(path):
                return (
                    changed
                    if path == feature.SCHEMA_DIR / "manifest.schema.json"
                    else original_load(path)
                )

            with (
                self.subTest(mutation=mutation),
                patch.object(feature, "load", mutant_load),
            ):
                killed = [v["name"] for v in VECTORS if mismatch(v)]
                MUTATION_KILLS[mutation] = killed
                self.assertTrue(killed, mutation)

    def test_context_mutation_oracles_are_falsifiable(self):
        original_exchange = feature.exchange_errors
        original_admission = feature.admission_outcome
        original_sequence = feature.sequence_result
        original_fixed = feature.fixed_values_match
        mutations = []
        for name, message in (
            ("ignore_no_store", "manifest response must forbid storage"),
            (
                "ignore_vary",
                "manifest Vary must include feature and preserve existing fields",
            ),
        ):

            def ignore_error(value, current_manifest=None, message=message):
                return [
                    e
                    for e in original_exchange(value, current_manifest)
                    if e != message
                ]

            mutations.append((name, "exchange_errors", ignore_error))

        def allow_cached(value, current_manifest=None):
            value = deepcopy(value)
            value["from_cache"] = False
            return original_exchange(value, current_manifest)

        mutations.append(("reuse_cache", "exchange_errors", allow_cached))

        def implicit_ack(value, current_manifest=None):
            value = deepcopy(value)
            if (
                feature.header_values(value["request_headers"]).get(feature.HEADER)
                == feature.FEATURE
            ):
                value["response_headers"][feature.HEADER] = feature.FEATURE
            return original_exchange(value, current_manifest)

        mutations.append(("implicit_ack", "exchange_errors", implicit_ack))

        def stale_rediscovery(value, current_manifest=None):
            return original_exchange(value)

        mutations.append(("stale_rediscovery", "exchange_errors", stale_rediscovery))

        def truthy_fixed(request, manifest):
            manifest = deepcopy(manifest)
            for capability in manifest["capabilities"]:
                for parameter in capability["parameters"]:
                    if "fixed_value" in parameter and not parameter["fixed_value"]:
                        parameter.pop("fixed_value")
            return original_fixed(request, manifest)

        mutations.append(("truthy_fixed", "fixed_values_match", truthy_fixed))

        def current_before_replay(context):
            if not feature.fixed_values_match(context["request"], context["manifest"]):
                return feature.decision("fixed_mismatch")
            return original_admission(context)

        mutations.append(
            ("current_before_replay", "admission_outcome", current_before_replay)
        )
        mutations.append(("ignore_conflict", "same_request", lambda left, right: True))
        mutations.append(
            (
                "collapse_bool_int_identity",
                "same_request",
                lambda left, right: left == right,
            )
        )

        def normalize_replay_output(context):
            result = original_admission(context)
            if result["decision"] == "replay":
                result["bound_parameters"] = {
                    name: float(value) if type(value) is int else value
                    for name, value in result["bound_parameters"].items()
                }
            return result

        mutations.append(
            ("normalize_replay_output", "admission_outcome", normalize_replay_output)
        )

        def rebind_replay(context):
            result = original_admission(context)
            if result["decision"] == "replay":
                result["bound_parameters"] = {
                    p["name"]: p["fixed_value"]
                    for c in context["manifest"]["capabilities"]
                    for p in c["parameters"]
                    if "fixed_value" in p
                }
            return result

        mutations.append(("rebind_replay", "admission_outcome", rebind_replay))

        def reversed_order(sequence):
            sequence = deepcopy(sequence)
            events = sequence["events"]
            if len(events) >= 2 and {events[0]["kind"], events[1]["kind"]} == {
                "rotate",
                "submit",
            }:
                events[0], events[1] = events[1], events[0]
            return original_sequence(sequence)

        mutations.append(
            ("reverse_admission_rotation", "sequence_result", reversed_order)
        )
        for name, owner, mutant in mutations:
            with self.subTest(mutation=name), patch.object(feature, owner, mutant):
                killed = [v["name"] for v in VECTORS if mismatch(v)]
                MUTATION_KILLS[name] = killed
                self.assertTrue(killed, name)

    def test_frozen_request_identity_is_not_fixed_value_equality(self):
        self.assertTrue(feature.wire_equal(1, 1.0))
        self.assertFalse(feature.same_request({"value": 1}, {"value": 1.0}))

    def test_replay_output_preserves_frozen_numeric_form(self):
        vector = deepcopy(
            next(v for v in VECTORS if v["name"] == "replay-frozen-integer")
        )
        vector["input"]["request"]["parameters"]["value"] = 1
        with patch.object(
            feature,
            "admission_outcome",
            return_value={
                "decision": "replay",
                "starts_work": False,
                "bound_parameters": {"value": 1.0},
            },
        ):
            self.assertTrue(mismatch(vector))

    def test_typed_wire_equality_boundaries(self):
        self.assertFalse(feature.wire_equal(False, 0))
        self.assertFalse(feature.wire_equal(True, 1))
        self.assertTrue(feature.wire_equal(1, 1.0))
        self.assertTrue(feature.wire_equal([{"value": False}], [{"value": False}]))
        self.assertFalse(feature.wire_equal([{"value": False}], [{"value": 0}]))
        self.assertFalse(feature.wire_equal({"value": 0}, {}))
        self.assertFalse(feature.wire_equal("", 0))

    def test_boolean_bound_output_must_not_equal_integer_zero(self):
        vector = next(v for v in VECTORS if v["name"] == "admit-boolean-boundary-0")
        with patch.object(
            feature,
            "admission_outcome",
            return_value={
                "decision": "accept",
                "starts_work": True,
                "bound_parameters": {"value": 0},
            },
        ):
            self.assertTrue(mismatch(vector))

    def test_feature_oracle_delegates_inherited_semantics(self):
        vector = next(v for v in VECTORS if v["name"] == "admit-current-bundle")
        original = feature.semantic_errors
        with patch.object(feature, "semantic_errors", wraps=original) as owner:
            errors, outcome = feature.vector_result(vector)
            self.assertEqual([], errors)
            self.assertEqual("accept", outcome["decision"])
            self.assertTrue(
                any(
                    call.args[:2] == ("v2", "job-request.schema.json")
                    for call in owner.call_args_list
                )
            )


if __name__ == "__main__":
    unittest.main()
