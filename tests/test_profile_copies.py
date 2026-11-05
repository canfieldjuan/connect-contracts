"""Original-byte migration checks; no native runtime or model execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.verify_profile_copies import verify_profile_copies


class ProfileCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.roots = [root / name for name in ("contracts", "client", "host")]
        self.paths = [
            self.roots[0] / "runtime/v1/profile.json",
            self.roots[1] / "crates/model-primitives/assets/profile.json",
            self.roots[2] / "vendor/local-connect-model-client/crates/model-primitives/assets/profile.json",
            self.roots[2] / "vendor/connect-contracts/profile.json",
        ]
        self.raw = b'{"a":1,"b":2}\n'
        self.pin = hashlib.sha256(self.raw).hexdigest()
        for path in self.paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.raw)

    def verify(self, pin=None):
        return verify_profile_copies(*self.roots, self.pin if pin is None else pin)

    def test_identical_bytes_pass_with_all_roles(self):
        receipt = self.verify()
        self.assertEqual(receipt["expected_sha256"], self.pin)
        self.assertEqual(set(receipt["copies"]), {
            "contracts", "client", "host_client", "host_contracts"})
        for item in receipt["copies"].values():
            self.assertEqual(item, {"sha256": self.pin, "size_bytes": len(self.raw)})

    def test_every_copy_must_match_even_if_json_is_equivalent(self):
        changed = b'{ "a": 1, "b": 2 }\n'
        self.assertEqual(json.loads(changed), json.loads(self.raw))
        for index, path in enumerate(self.paths):
            with self.subTest(copy=index):
                path.write_bytes(changed)
                with self.assertRaisesRegex(ValueError, "profile digest mismatch"):
                    self.verify()
                path.write_bytes(self.raw)

    def test_all_copies_drifting_together_do_not_redefine_expected_identity(self):
        for path in self.paths:
            path.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, "contracts: profile digest mismatch"):
            self.verify()

    def test_each_missing_copy_fails_without_path_or_contents_in_error(self):
        for path in self.paths:
            with self.subTest(copy=path.name):
                path.unlink()
                with self.assertRaisesRegex(ValueError, "cannot read profile") as caught:
                    self.verify()
                self.assertNotIn(str(path), str(caught.exception))
                path.write_bytes(self.raw)

    def test_pin_is_required_and_exact_lowercase_sha256(self):
        for pin in ("", "0", "0" * 63, "0" * 65, "g" * 64, self.pin.upper()):
            with self.subTest(pin=pin):
                with self.assertRaisesRegex(ValueError, "expected digest must be"):
                    self.verify(pin)
        with self.assertRaisesRegex(ValueError, "profile digest mismatch"):
            self.verify("0" * 64)

    def test_cli_success_and_failure_have_distinct_exit_codes(self):
        script = Path(__file__).resolve().parents[1] / "tools/verify_profile_copies.py"
        command = [sys.executable, str(script), "--contracts", str(self.roots[0]),
                   "--client", str(self.roots[1]), "--host", str(self.roots[2]),
                   "--expected-sha256", self.pin]
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.verify())
        self.paths[-1].write_bytes(b'{}')
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr.strip(), "host_contracts: profile digest mismatch")


if __name__ == "__main__":
    unittest.main()
