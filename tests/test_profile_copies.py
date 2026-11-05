"""Real tiny Git repositories; no native runtime or model execution."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.verify_profile_copies import verify_profile_copies


class ProfileCopyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.roles = ("contracts", "client", "host")
        self.roots = [root / name for name in self.roles]
        self.paths = [
            self.roots[0] / "runtime/v1/profile.json",
            self.roots[1] / "crates/model-primitives/assets/profile.json",
            self.roots[2] / "vendor/local-connect-model-client/crates/model-primitives/assets/profile.json",
            self.roots[2] / "vendor/connect-contracts/profile.json",
        ]
        self.raw = b'{"a":1,"b":2}\n'
        self.pin = hashlib.sha256(self.raw).hexdigest()
        self.env = {key: value for key, value in os.environ.items()
                    if not key.startswith("GIT_")}
        self.env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="Fixture", GIT_AUTHOR_EMAIL="fixture@example.invalid",
                        GIT_COMMITTER_NAME="Fixture", GIT_COMMITTER_EMAIL="fixture@example.invalid")
        for path in self.paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.raw)
        for root in self.roots:
            self.git(root, "init", "-q")
        self.revisions = self.commit_all()

    def git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              env=self.env, capture_output=True, timeout=10).stdout

    def commit_all(self):
        revisions = {}
        for role, root in zip(self.roles, self.roots):
            self.git(root, "add", "-A")
            self.git(root, "commit", "--allow-empty", "-qm", "fixture")
            revisions[role] = self.git(root, "rev-parse", "HEAD").decode().strip()
        return revisions

    def verify(self, pin=None, revisions=None):
        revisions = self.revisions if revisions is None else revisions
        return verify_profile_copies(
            *self.roots, self.pin if pin is None else pin,
            **{f"{role}_revision": revisions[role] for role in self.roles})

    def test_identical_blobs_pass_with_all_roles_and_full_commits(self):
        receipt = self.verify(revisions=dict.fromkeys(self.roles, "HEAD"))
        self.assertEqual(receipt["expected_sha256"], self.pin)
        self.assertEqual(receipt["revisions"], self.revisions)
        self.assertEqual(set(receipt["copies"]), {
            "contracts", "client", "host_client", "host_contracts"})
        for item in receipt["copies"].values():
            self.assertEqual(item, {"sha256": self.pin, "size_bytes": len(self.raw)})

    def test_uncommitted_matching_bytes_cannot_certify_a_different_commit(self):
        for path in self.paths:
            with self.subTest(copy=path):
                path.write_bytes(b'{}')
                bad = self.commit_all()
                path.write_bytes(self.raw)
                with self.assertRaisesRegex(ValueError, "profile digest mismatch"):
                    self.verify(revisions=bad)
                self.commit_all()

    def test_dirty_or_missing_working_tree_cannot_change_a_matching_commit(self):
        for path in self.paths:
            path.write_bytes(b'{}')
        self.assertEqual(self.verify()["revisions"], self.revisions)
        for path in self.paths:
            path.unlink()
        self.assertEqual(self.verify()["revisions"], self.revisions)

    def test_explicit_older_revision_does_not_follow_head(self):
        for path in self.paths:
            path.write_bytes(b'{}')
        self.commit_all()
        self.assertEqual(self.verify()["revisions"], self.revisions)
        with self.assertRaisesRegex(ValueError, "profile digest mismatch"):
            self.verify(revisions=dict.fromkeys(self.roles, "HEAD"))

    def test_every_committed_copy_must_match_even_if_json_is_equivalent(self):
        changed = b'{ "a": 1, "b": 2 }\n'
        self.assertEqual(json.loads(changed), json.loads(self.raw))
        for path in self.paths:
            with self.subTest(copy=path):
                path.write_bytes(changed)
                revisions = self.commit_all()
                with self.assertRaisesRegex(ValueError, "profile digest mismatch"):
                    self.verify(revisions=revisions)
                path.write_bytes(self.raw)
                self.commit_all()

    def test_all_committed_copies_drifting_do_not_redefine_expected_identity(self):
        for path in self.paths:
            path.write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError, "contracts: profile digest mismatch"):
            self.verify(revisions=self.commit_all())

    def test_each_missing_blob_fails_without_falling_back_to_working_tree(self):
        for path in self.paths:
            with self.subTest(copy=path):
                path.unlink()
                revisions = self.commit_all()
                path.write_bytes(self.raw)
                with self.assertRaisesRegex(ValueError, "cannot read profile blob") as caught:
                    self.verify(revisions=revisions)
                self.assertNotIn(str(path), str(caught.exception))
                self.commit_all()

    def test_each_revision_is_required_resolvable_and_a_commit(self):
        for role in self.roles:
            for revision in ("", "missing-ref", "--help", "HEAD^{tree}"):
                with self.subTest(role=role, revision=revision):
                    revisions = dict(self.revisions, **{role: revision})
                    message = "revision is required" if revision == "" else "cannot resolve commit"
                    with self.assertRaisesRegex(ValueError, f"{role}: {message}"):
                        self.verify(revisions=revisions)

    def test_replace_objects_cannot_change_the_committed_bytes(self):
        self.paths[0].write_bytes(b'{}')
        bad = self.commit_all()
        self.git(self.roots[0], "replace", bad["contracts"], self.revisions["contracts"])
        with self.assertRaisesRegex(ValueError, "contracts: profile digest mismatch"):
            self.verify(revisions=bad)

    def test_inherited_git_directory_cannot_redirect_the_check(self):
        with patch.dict(os.environ, {"GIT_DIR": str(self.roots[0] / ".git")}):
            self.assertEqual(self.verify()["revisions"], self.revisions)

    def test_pin_is_required_and_exact_lowercase_sha256(self):
        for pin in ("", "0", "0" * 63, "0" * 65, "g" * 64, self.pin.upper()):
            with self.subTest(pin=pin):
                with self.assertRaisesRegex(ValueError, "expected digest must be"):
                    self.verify(pin)
        with self.assertRaisesRegex(ValueError, "profile digest mismatch"):
            self.verify("0" * 64)

    def test_cli_success_and_failure_have_distinct_exit_codes(self):
        script = Path(__file__).resolve().parents[1] / "tools/verify_profile_copies.py"
        command = [sys.executable, str(script), "--expected-sha256", self.pin]
        for role, root in zip(self.roles, self.roots):
            command.extend([f"--{role}", str(root), f"--{role}-revision", "HEAD"])
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.verify())
        self.paths[-1].write_bytes(b'{}')
        self.commit_all()
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr.strip(), "host_contracts: profile digest mismatch")


if __name__ == "__main__":
    unittest.main()
