import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas" / "v1"
FIXTURES = ROOT / "fixtures" / "v1"


class ConnectContractTests(unittest.TestCase):
    def test_schemas_are_valid_and_fixtures_match_expectations(self) -> None:
        cases = json.loads((FIXTURES / "index.json").read_text(encoding="utf-8"))
        self.assertGreater(len(cases), 0)

        schemas = {}
        for path in sorted(SCHEMAS.glob("*.schema.json")):
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            schemas[path.name] = schema

        self.assertEqual(
            set(schemas),
            {
                "error.schema.json",
                "job-request.schema.json",
                "job-status.schema.json",
                "manifest.schema.json",
                "registration.schema.json",
            },
        )

        for case in cases:
            with self.subTest(fixture=case["fixture"]):
                instance = json.loads(
                    (FIXTURES / case["fixture"]).read_text(encoding="utf-8")
                )
                validator = Draft202012Validator(
                    schemas[case["schema"]], format_checker=FormatChecker()
                )
                errors = list(validator.iter_errors(instance))
                if case["valid"]:
                    self.assertEqual(errors, [], [error.message for error in errors])
                else:
                    self.assertNotEqual(errors, [], "invalid fixture unexpectedly passed")


if __name__ == "__main__":
    unittest.main()
