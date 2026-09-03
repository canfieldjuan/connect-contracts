import base64
import getpass
import json
import os
import stat
import tempfile
import unittest
import warnings
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, FormatChecker

from tools.entitlement_issuer import (
    FEATURE_ID,
    ROOT,
    IssuerError,
    _create_secret_service_passphrase,
    _ensure_secret_collection_unlocked,
    _interactive_passphrase,
    _read_secret_service_passphrase,
    _write_new,
    initialize_authority,
    issue_entitlement,
    main,
)


UTC = timezone.utc
PASSPHRASE = b"correct horse battery staple"


def decode_base64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class EntitlementIssuerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.private_parent = self.root / "private"
        self.private_parent.mkdir(mode=0o700)
        self.private_key = self.private_parent / "issuer.private.pem"
        self.keyring = self.root / "keyring.json"
        self.output = self.private_parent / "entitlement-v1.json"
        self.key_id = "local-connect-prod-2026-01"

    def tearDown(self):
        self.temporary.cleanup()

    def initialize(self):
        return initialize_authority(
            key_id=self.key_id,
            private_key_path=self.private_key,
            keyring_path=self.keyring,
            passphrase=PASSPHRASE,
        )

    def issue(self, **overrides):
        values = {
            "private_key_path": self.private_key,
            "keyring_path": self.keyring,
            "key_id": self.key_id,
            "subject": "juan-canfield-local-connect",
            "features": [FEATURE_ID],
            "issued_at": datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
            "not_before": datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
            "expires_at": datetime(2027, 9, 2, 12, 0, tzinfo=UTC),
            "output_path": self.output,
            "passphrase": PASSPHRASE,
        }
        values.update(overrides)
        return issue_entitlement(**values)

    def test_initialization_writes_only_encrypted_private_key_and_public_keyring(self):
        result = self.initialize()

        self.assertEqual(result["key_id"], self.key_id)
        self.assertEqual(stat.S_IMODE(self.private_key.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.keyring.stat().st_mode), 0o644)
        private_content = self.private_key.read_bytes()
        self.assertIn(b"BEGIN ENCRYPTED PRIVATE KEY", private_content)
        self.assertNotIn(PASSPHRASE, private_content)
        keyring = json.loads(self.keyring.read_text(encoding="utf-8"))
        self.assertEqual(
            set(keyring["keys"][0]),
            {"key_id", "algorithm", "public_key_base64url"},
        )
        self.assertEqual(keyring["keys"][0]["algorithm"], "Ed25519")
        self.assertEqual(
            len(decode_base64url(keyring["keys"][0]["public_key_base64url"])), 32
        )

    def test_issued_entitlement_matches_schema_and_signature_contract(self):
        self.initialize()
        result = self.issue()

        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        envelope = json.loads(self.output.read_text(encoding="utf-8"))
        payload = decode_base64url(envelope["payload_base64url"])
        claims = json.loads(payload)
        signature = decode_base64url(envelope["signature_base64url"])
        keyring = json.loads(self.keyring.read_text(encoding="utf-8"))
        public_key = decode_base64url(keyring["keys"][0]["public_key_base64url"])
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, payload)

        entitlement_root = ROOT / "entitlements" / "v1"
        for filename, value in (
            ("keyring.schema.json", keyring),
            ("envelope.schema.json", envelope),
            ("claims.schema.json", claims),
        ):
            schema = json.loads(
                (entitlement_root / filename).read_text(encoding="utf-8")
            )
            Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
        self.assertEqual(result["entitlement_id"], claims["entitlement_id"])
        self.assertEqual(claims["features"], [FEATURE_ID])
        self.assertEqual(claims["issued_at"], "2026-09-02T12:00:00Z")
        self.assertEqual(claims["expires_at"], "2027-09-02T12:00:00Z")

    def test_private_key_destination_must_be_outside_repo_and_owner_private(self):
        with self.assertRaisesRegex(IssuerError, "cannot be stored in the repository"):
            initialize_authority(
                key_id=self.key_id,
                private_key_path=ROOT / "issuer.private.pem",
                keyring_path=self.keyring,
                passphrase=PASSPHRASE,
            )

        unsafe_parent = self.root / "unsafe"
        unsafe_parent.mkdir(mode=0o755)
        unsafe_parent.chmod(0o755)
        with self.assertRaisesRegex(IssuerError, "parent directory must be owner-only"):
            initialize_authority(
                key_id=self.key_id,
                private_key_path=unsafe_parent / "issuer.private.pem",
                keyring_path=self.keyring,
                passphrase=PASSPHRASE,
            )

    def test_initialization_rejects_test_id_short_passphrase_and_existing_output(self):
        with self.assertRaisesRegex(IssuerError, "production-shaped"):
            initialize_authority(
                key_id="local-connect-test-2026-01",
                private_key_path=self.private_key,
                keyring_path=self.keyring,
                passphrase=PASSPHRASE,
            )
        with self.assertRaisesRegex(IssuerError, "production-shaped"):
            initialize_authority(
                key_id="local-connect-2026-01",
                private_key_path=self.private_key,
                keyring_path=self.keyring,
                passphrase=PASSPHRASE,
            )
        with self.assertRaisesRegex(IssuerError, "at least sixteen"):
            initialize_authority(
                key_id=self.key_id,
                private_key_path=self.private_key,
                keyring_path=self.keyring,
                passphrase=b"short",
            )
        with self.assertRaisesRegex(IssuerError, "at most 1023"):
            initialize_authority(
                key_id=self.key_id,
                private_key_path=self.private_key,
                keyring_path=self.keyring,
                passphrase=b"x" * 1_024,
            )

        self.initialize()
        original_private = self.private_key.read_bytes()
        original_keyring = self.keyring.read_bytes()
        with self.assertRaisesRegex(IssuerError, "already exists"):
            self.initialize()
        self.assertEqual(self.private_key.read_bytes(), original_private)
        self.assertEqual(self.keyring.read_bytes(), original_keyring)

    def test_initialization_interrupts_remove_partial_outputs(self):
        partial = self.private_parent / "partial"
        with unittest.mock.patch(
            "tools.entitlement_issuer.os.write", side_effect=KeyboardInterrupt()
        ):
            with self.assertRaises(KeyboardInterrupt):
                _write_new(partial, b"private", 0o600)
        self.assertFalse(partial.exists())

        real_write_new = _write_new
        calls = 0

        def interrupt_keyring(path, content, mode):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise KeyboardInterrupt()
            return real_write_new(path, content, mode)

        with unittest.mock.patch(
            "tools.entitlement_issuer._write_new", side_effect=interrupt_keyring
        ):
            with self.assertRaises(KeyboardInterrupt):
                self.initialize()
        self.assertFalse(self.private_key.exists())
        self.assertFalse(self.keyring.exists())

    def test_issue_rejects_wrong_passphrase_keyring_and_unsafe_private_mode(self):
        self.initialize()
        with self.assertRaisesRegex(IssuerError, "key or passphrase is invalid"):
            self.issue(passphrase=b"wrong passphrase with length")
        with self.assertRaisesRegex(IssuerError, "at most 1023"):
            self.issue(passphrase=b"x" * 1_024)

        with unittest.mock.patch(
            "tools.entitlement_issuer.serialization.load_pem_private_key",
            side_effect=UnsupportedAlgorithm("unsupported key algorithm"),
        ):
            with self.assertRaisesRegex(IssuerError, "key or passphrase is invalid"):
                self.issue()

        other_private = self.private_parent / "other.private.pem"
        other_keyring = self.root / "other-keyring.json"
        initialize_authority(
            key_id="local-connect-prod-2026-02",
            private_key_path=other_private,
            keyring_path=other_keyring,
            passphrase=PASSPHRASE,
        )
        with self.assertRaisesRegex(IssuerError, "does not match"):
            self.issue(keyring_path=other_keyring, key_id="local-connect-prod-2026-02")

        self.private_key.chmod(0o640)
        with self.assertRaisesRegex(IssuerError, "owner-only"):
            self.issue()

    def test_issue_rejects_invalid_claim_boundaries_and_does_not_replace_output(self):
        self.initialize()
        with self.assertRaisesRegex(IssuerError, "unique and bounded"):
            self.issue(features=[FEATURE_ID, FEATURE_ID])
        with self.assertRaisesRegex(IssuerError, "invalid feature"):
            self.issue(features=["Connect.Bad"])
        with self.assertRaisesRegex(IssuerError, "one to two hundred"):
            self.issue(subject="")
        instant = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
        with self.assertRaisesRegex(
            IssuerError, "issued_at <= not_before < expires_at"
        ):
            self.issue(not_before=instant, expires_at=instant)
        with self.assertRaisesRegex(IssuerError, "timestamps must be UTC-aware"):
            self.issue(issued_at=instant.replace(tzinfo=None))
        with self.assertRaisesRegex(IssuerError, "fractional seconds"):
            self.issue(
                not_before=instant.replace(microsecond=100_000),
                expires_at=instant.replace(microsecond=900_000),
            )

        self.issue()
        original = self.output.read_bytes()
        with self.assertRaisesRegex(IssuerError, "already exists"):
            self.issue()
        self.assertEqual(self.output.read_bytes(), original)

    def test_issue_rejects_partial_duplicate_and_unknown_keyrings(self):
        self.initialize()
        partial = self.root / "partial.json"
        partial.write_text('{"keys":[{"key_id":"prod"}]}', encoding="utf-8")
        with self.assertRaisesRegex(IssuerError, "fields do not match"):
            self.issue(keyring_path=partial)

        duplicate = self.root / "duplicate.json"
        duplicate.write_text('{"keys":[],"keys":[]}', encoding="utf-8")
        with self.assertRaisesRegex(IssuerError, "duplicate JSON member"):
            self.issue(keyring_path=duplicate)

        invalid_public_key = self.root / "invalid-public-key.json"
        invalid_public_key.write_text(
            json.dumps(
                {
                    "keys": [
                        {
                            "key_id": self.key_id,
                            "algorithm": "Ed25519",
                            "public_key_base64url": None,
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(IssuerError, "base64url"):
            self.issue(keyring_path=invalid_public_key)

        with self.assertRaisesRegex(IssuerError, "not present"):
            self.issue(key_id="local-connect-prod-2099-01")

    def test_issue_normalizes_json_numeric_and_recursion_limits(self):
        numeric = self.root / "numeric.json"
        numeric.write_text('{"keys":' + "9" * 5_000 + "}", encoding="utf-8")
        with self.assertRaisesRegex(IssuerError, "invalid JSON document"):
            self.issue(keyring_path=numeric)

        with unittest.mock.patch(
            "tools.entitlement_issuer.json.loads",
            side_effect=RecursionError("maximum recursion depth exceeded"),
        ):
            with self.assertRaisesRegex(IssuerError, "invalid JSON document"):
                self.issue(keyring_path=numeric)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO support is unavailable")
    def test_issue_input_reader_rejects_fifo_without_waiting_for_a_writer(self):
        fifo = self.root / "keyring.fifo"
        os.mkfifo(fifo)

        with self.assertRaisesRegex(IssuerError, "bounded regular file"):
            self.issue(keyring_path=fifo)

    def test_secret_collection_unlock_accepts_successful_prompt(self):
        collection = Mock()
        collection.is_locked.side_effect = [True, False]
        collection.unlock.return_value = False

        _ensure_secret_collection_unlocked(collection)

        collection.unlock.assert_called_once_with()

    def test_secret_collection_unlock_rejects_dismissal_or_still_locked(self):
        dismissed = Mock()
        dismissed.is_locked.return_value = True
        dismissed.unlock.return_value = True
        with self.assertRaisesRegex(IssuerError, "collection is locked"):
            _ensure_secret_collection_unlocked(dismissed)

        still_locked = Mock()
        still_locked.is_locked.return_value = True
        still_locked.unlock.return_value = False
        with self.assertRaisesRegex(IssuerError, "collection is locked"):
            _ensure_secret_collection_unlocked(still_locked)

    def test_secret_service_search_failures_use_stable_issuer_error(self):
        collection = Mock()
        collection.search_items.side_effect = RuntimeError("daemon disconnected")

        with unittest.mock.patch(
            "tools.entitlement_issuer._secret_collection", return_value=collection
        ):
            with self.assertRaisesRegex(IssuerError, "could not search"):
                _create_secret_service_passphrase(self.key_id)
            with self.assertRaisesRegex(IssuerError, "could not search"):
                _read_secret_service_passphrase(self.key_id)

    def test_interactive_prompt_accepts_no_echo_and_normalizes_failures(self):
        with unittest.mock.patch(
            "tools.entitlement_issuer.getpass.getpass", return_value="private phrase"
        ):
            self.assertEqual(
                _interactive_passphrase("Issuer passphrase: "), b"private phrase"
            )

        for failure in (EOFError(), KeyboardInterrupt(), OSError("no terminal")):
            with self.subTest(failure=type(failure).__name__):
                with unittest.mock.patch(
                    "tools.entitlement_issuer.getpass.getpass", side_effect=failure
                ):
                    with self.assertRaisesRegex(
                        IssuerError, "cancelled or unavailable"
                    ):
                        _interactive_passphrase("Issuer passphrase: ")

        with unittest.mock.patch(
            "tools.entitlement_issuer.getpass.getpass", return_value="\ud800"
        ):
            with self.assertRaisesRegex(IssuerError, "cancelled or unavailable"):
                _interactive_passphrase("Issuer passphrase: ")

        def echoed_fallback(_prompt):
            warnings.warn(
                "Can not control echo on the terminal.", getpass.GetPassWarning
            )
            return "exposed passphrase"

        with unittest.mock.patch(
            "tools.entitlement_issuer.getpass.getpass", side_effect=echoed_fallback
        ):
            with self.assertRaisesRegex(IssuerError, "cancelled or unavailable"):
                _interactive_passphrase("Issuer passphrase: ")

    def test_secret_service_initialization_interrupt_rolls_back_item(self):
        uncertain_item = Mock()
        uncertain_item.get_secret.return_value = b"generated-secret"
        collection = Mock()
        collection.search_items.side_effect = [[], [uncertain_item]]
        collection.create_item.side_effect = KeyboardInterrupt()
        with (
            unittest.mock.patch(
                "tools.entitlement_issuer._secret_collection", return_value=collection
            ),
            unittest.mock.patch(
                "tools.entitlement_issuer.secrets.token_urlsafe",
                return_value="generated-secret",
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                _create_secret_service_passphrase(self.key_id)
        uncertain_item.delete.assert_called_once_with()

        foreign_item = Mock()
        foreign_item.get_secret.return_value = b"another credential"
        collection.reset_mock()
        collection.search_items.side_effect = [[], [foreign_item]]
        collection.create_item.side_effect = KeyboardInterrupt()
        with (
            unittest.mock.patch(
                "tools.entitlement_issuer._secret_collection", return_value=collection
            ),
            unittest.mock.patch(
                "tools.entitlement_issuer.secrets.token_urlsafe",
                return_value="generated-secret",
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                _create_secret_service_passphrase(self.key_id)
        foreign_item.delete.assert_not_called()

        secret_item = Mock()
        arguments = [
            "init",
            "--key-id",
            self.key_id,
            "--private-key",
            str(self.private_key),
            "--keyring",
            str(self.keyring),
            "--secret-service",
        ]
        with (
            unittest.mock.patch(
                "tools.entitlement_issuer._create_secret_service_passphrase",
                return_value=(PASSPHRASE, secret_item),
            ),
            unittest.mock.patch(
                "tools.entitlement_issuer.initialize_authority",
                side_effect=KeyboardInterrupt(),
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                main(arguments)
        secret_item.delete.assert_called_once_with()

        secret_item.reset_mock()
        secret_item.delete.side_effect = OSError("delete failed")
        error = unittest.mock.MagicMock()
        with (
            unittest.mock.patch(
                "tools.entitlement_issuer._create_secret_service_passphrase",
                return_value=(PASSPHRASE, secret_item),
            ),
            unittest.mock.patch(
                "tools.entitlement_issuer.initialize_authority",
                side_effect=KeyboardInterrupt(),
            ),
            unittest.mock.patch("tools.entitlement_issuer.print", error),
        ):
            self.assertEqual(main(arguments), 2)
        self.assertIn("rollback failed", error.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
