#!/usr/bin/env python3
"""Offline release authority for Local Connect entitlement v1."""

from __future__ import annotations

import argparse
import base64
import binascii
import getpass
import json
import os
import re
import secrets
import stat
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


ROOT = Path(__file__).resolve().parents[1]
FEATURE_ID = "connect.capability_exchange"
MAX_KEYRING_BYTES = 64 * 1024
MAX_PRIVATE_KEY_BYTES = 64 * 1024
MAX_KEYS = 16
MAX_FEATURES = 32
MAX_PASSPHRASE_BYTES = 1023
KEY_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
FEATURE_PATTERN = re.compile(r"^[a-z0-9]+(?:[._-][a-z0-9]+)*$")
UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SECRET_ATTRIBUTES = {"application": "local-connect-entitlement-issuer"}
NON_PRODUCTION_KEY_TOKENS = frozenset(("dev", "example", "fixture", "test"))


class IssuerError(RuntimeError):
    """A safe, operator-facing issuer failure."""


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: object) -> bytes:
    if not isinstance(value, str) or "=" in value:
        raise IssuerError("base64url values must be unpadded")
    try:
        decoded = base64.b64decode(
            value + "=" * (-len(value) % 4), altchars=b"-_", validate=True
        )
    except (binascii.Error, ValueError) as exc:
        raise IssuerError("invalid base64url value") from exc
    if _base64url_encode(decoded) != value:
        raise IssuerError("non-canonical base64url value")
    return decoded


def _strict_json_object(content: bytes) -> dict[str, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise IssuerError(f"duplicate JSON member: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(content, object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise IssuerError("invalid JSON document") from exc
    if not isinstance(value, dict):
        raise IssuerError("JSON document must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise IssuerError(f"{label} fields do not match entitlement v1")


def _valid_identifier(value: object, pattern: re.Pattern[str], limit: int) -> bool:
    return (
        isinstance(value, str)
        and 1 <= len(value) <= limit
        and bool(pattern.fullmatch(value))
    )


def _read_regular_file(path: Path, *, limit: int, private: bool) -> bytes:
    if not path.is_absolute():
        raise IssuerError("issuer input paths must be absolute")
    flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode) or not 0 < metadata.st_size <= limit:
                raise IssuerError(f"issuer input is not a bounded regular file: {path}")
            if private and (
                metadata.st_uid != os.geteuid()
                or stat.S_IMODE(metadata.st_mode) & 0o077
            ):
                raise IssuerError("private issuer key must be owner-only")
            chunks: list[bytes] = []
            remaining = limit + 1
            while remaining:
                chunk = os.read(descriptor, min(remaining, 8192))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            content = b"".join(chunks)
            if not content or len(content) > limit:
                raise IssuerError(f"issuer input is not a bounded regular file: {path}")
            return content
        finally:
            os.close(descriptor)
    except IssuerError:
        raise
    except OSError as exc:
        raise IssuerError(f"issuer input could not be read safely: {path}") from exc


def _require_private_destination(path: Path) -> None:
    if not path.is_absolute():
        raise IssuerError("private issuer key destination must be absolute")
    try:
        resolved = path.resolve(strict=False)
        if resolved.is_relative_to(ROOT.resolve()):
            raise IssuerError("private issuer keys cannot be stored in the repository")
        parent = path.parent.lstat()
    except OSError as exc:
        raise IssuerError("private issuer key parent directory is unavailable") from exc
    if (
        not stat.S_ISDIR(parent.st_mode)
        or parent.st_uid != os.geteuid()
        or stat.S_IMODE(parent.st_mode) & 0o077
    ):
        raise IssuerError("private issuer key parent directory must be owner-only")


def _write_new(path: Path, content: bytes, mode: int) -> None:
    if not path.is_absolute():
        raise IssuerError("issuer output paths must be absolute")
    parent_flags = os.O_RDONLY | os.O_CLOEXEC
    if hasattr(os, "O_DIRECTORY"):
        parent_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        parent_flags |= os.O_NOFOLLOW
    file_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        file_flags |= os.O_NOFOLLOW
    try:
        parent = os.open(path.parent, parent_flags)
    except OSError as exc:
        raise IssuerError(
            f"issuer output parent is unavailable: {path.parent}"
        ) from exc
    created = False

    def rollback_created_output() -> None:
        if not created:
            return
        try:
            os.unlink(path.name, dir_fd=parent)
            os.fsync(parent)
        except OSError as exc:
            raise IssuerError(f"issuer output rollback failed: {path}") from exc

    try:
        try:
            try:
                descriptor = os.open(path.name, file_flags, mode, dir_fd=parent)
            except FileExistsError as exc:
                raise IssuerError(f"issuer output already exists: {path}") from exc
            created = True
            try:
                os.fchmod(descriptor, mode)
                view = memoryview(content)
                while view:
                    written = os.write(descriptor, view)
                    if written == 0:
                        raise OSError("issuer output write made no progress")
                    view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.fsync(parent)
        except IssuerError:
            raise
        except OSError as exc:
            rollback_created_output()
            raise IssuerError(
                f"issuer output could not be created safely: {path}"
            ) from exc
        except BaseException:
            rollback_created_output()
            raise
    finally:
        os.close(parent)


def _load_keyring(path: Path) -> dict[str, bytes]:
    content = _read_regular_file(path, limit=MAX_KEYRING_BYTES, private=False)
    document = _strict_json_object(content)
    _exact_keys(document, {"keys"}, "keyring")
    items = document["keys"]
    if not isinstance(items, list) or not 1 <= len(items) <= MAX_KEYS:
        raise IssuerError("keyring must contain between one and sixteen keys")
    keys: dict[str, bytes] = {}
    for item in items:
        if not isinstance(item, dict):
            raise IssuerError("keyring entries must be objects")
        _exact_keys(
            item, {"key_id", "algorithm", "public_key_base64url"}, "keyring entry"
        )
        key_id = item["key_id"]
        if not _valid_identifier(key_id, KEY_ID_PATTERN, 100):
            raise IssuerError("keyring contains an invalid key ID")
        if item["algorithm"] != "Ed25519" or key_id in keys:
            raise IssuerError("keyring contains an invalid or duplicate entry")
        public_key = _base64url_decode(item["public_key_base64url"])
        if len(public_key) != 32:
            raise IssuerError("keyring contains an invalid Ed25519 public key")
        keys[key_id] = public_key
    return keys


def initialize_authority(
    *,
    key_id: str,
    private_key_path: Path,
    keyring_path: Path,
    passphrase: bytes,
) -> dict[str, str]:
    if not _valid_identifier(key_id, KEY_ID_PATTERN, 100):
        raise IssuerError("invalid production key ID")
    key_tokens = frozenset(re.split(r"[.-]", key_id))
    if "prod" not in key_tokens or key_tokens & NON_PRODUCTION_KEY_TOKENS:
        raise IssuerError("production key ID must be explicitly production-shaped")
    if len(passphrase) < 16:
        raise IssuerError("issuer passphrase must contain at least sixteen bytes")
    if len(passphrase) > MAX_PASSPHRASE_BYTES:
        raise IssuerError("issuer passphrase must contain at most 1023 bytes")
    _require_private_destination(private_key_path)
    if not keyring_path.is_absolute():
        raise IssuerError("public keyring destination must be absolute")

    try:
        private_key = Ed25519PrivateKey.generate()
        private_bytes = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.BestAvailableEncryption(passphrase),
        )
        public_bytes = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
    except (TypeError, ValueError, UnsupportedAlgorithm) as exc:
        raise IssuerError("issuer key could not be generated safely") from exc
    keyring = {
        "keys": [
            {
                "key_id": key_id,
                "algorithm": "Ed25519",
                "public_key_base64url": _base64url_encode(public_bytes),
            }
        ]
    }
    keyring_bytes = (
        json.dumps(keyring, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")

    _write_new(private_key_path, private_bytes, 0o600)
    try:
        _write_new(keyring_path, keyring_bytes, 0o644)
    except BaseException:
        try:
            private_key_path.unlink(missing_ok=True)
        except OSError as exc:
            raise IssuerError("private issuer key rollback failed") from exc
        raise
    return {
        "key_id": key_id,
        "private_key": str(private_key_path),
        "keyring": str(keyring_path),
    }


def _parse_utc(value: str) -> datetime:
    if not UTC_PATTERN.fullmatch(value):
        raise IssuerError("timestamps must use YYYY-MM-DDTHH:MM:SSZ")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IssuerError("timestamp is not a real UTC instant") from exc


def _format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timezone.utc.utcoffset(value):
        raise IssuerError("issuer timestamps must be UTC-aware")
    if value.microsecond:
        raise IssuerError("issuer timestamps must not contain fractional seconds")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def issue_entitlement(
    *,
    private_key_path: Path,
    keyring_path: Path,
    key_id: str,
    subject: str,
    features: Iterable[str],
    issued_at: datetime,
    not_before: datetime,
    expires_at: datetime,
    output_path: Path,
    passphrase: bytes,
) -> dict[str, str]:
    if not isinstance(subject, str) or not 1 <= len(subject) <= 200:
        raise IssuerError(
            "entitlement subject must contain one to two hundred characters"
        )
    feature_list = list(features)
    if not 1 <= len(feature_list) <= MAX_FEATURES or len(set(feature_list)) != len(
        feature_list
    ):
        raise IssuerError("entitlement features must be unique and bounded")
    if any(
        not _valid_identifier(value, FEATURE_PATTERN, 100) for value in feature_list
    ):
        raise IssuerError("entitlement contains an invalid feature ID")
    issued_at_text = _format_utc(issued_at)
    not_before_text = _format_utc(not_before)
    expires_at_text = _format_utc(expires_at)
    if not issued_at <= not_before < expires_at:
        raise IssuerError(
            "entitlement validity must satisfy issued_at <= not_before < expires_at"
        )
    if len(passphrase) < 16:
        raise IssuerError("issuer passphrase must contain at least sixteen bytes")
    if len(passphrase) > MAX_PASSPHRASE_BYTES:
        raise IssuerError("issuer passphrase must contain at most 1023 bytes")

    keys = _load_keyring(keyring_path)
    expected_public = keys.get(key_id)
    if expected_public is None:
        raise IssuerError("selected key ID is not present in the public keyring")
    private_bytes = _read_regular_file(
        private_key_path, limit=MAX_PRIVATE_KEY_BYTES, private=True
    )
    try:
        loaded = serialization.load_pem_private_key(private_bytes, password=passphrase)
    except (TypeError, ValueError, UnsupportedAlgorithm) as exc:
        raise IssuerError("private issuer key or passphrase is invalid") from exc
    if not isinstance(loaded, Ed25519PrivateKey):
        raise IssuerError("private issuer key is not Ed25519")
    actual_public = loaded.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    if actual_public != expected_public:
        raise IssuerError("private issuer key does not match the selected public key")

    entitlement_id = str(uuid.uuid4())
    claims = {
        "format_version": 1,
        "entitlement_id": entitlement_id,
        "subject": subject,
        "features": feature_list,
        "issued_at": issued_at_text,
        "not_before": not_before_text,
        "expires_at": expires_at_text,
    }
    payload = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = loaded.sign(payload)
    try:
        Ed25519PublicKey.from_public_bytes(expected_public).verify(signature, payload)
    except InvalidSignature as exc:  # pragma: no cover - cryptography invariant
        raise IssuerError("issuer self-verification failed") from exc
    envelope = {
        "format_version": 1,
        "key_id": key_id,
        "payload_base64url": _base64url_encode(payload),
        "signature_base64url": _base64url_encode(signature),
    }
    content = (
        json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    _write_new(output_path, content, 0o600)
    return {
        "entitlement_id": entitlement_id,
        "key_id": key_id,
        "output": str(output_path),
    }


def _ensure_secret_collection_unlocked(collection: Any) -> None:
    if not collection.is_locked():
        return
    prompt_dismissed = collection.unlock()
    if prompt_dismissed or collection.is_locked():
        raise IssuerError("default Secret Service collection is locked")


def _secret_collection():
    try:
        import secretstorage

        collection = secretstorage.get_default_collection(secretstorage.dbus_init())
        _ensure_secret_collection_unlocked(collection)
        return collection
    except ImportError as exc:
        raise IssuerError(
            "Secret Service support requires the secretstorage package"
        ) from exc
    except IssuerError:
        raise
    except Exception as exc:
        raise IssuerError("Secret Service is unavailable") from exc


def _secret_attributes(key_id: str) -> dict[str, str]:
    return {**SECRET_ATTRIBUTES, "key_id": key_id}


def _search_secret_service_items(collection: Any, key_id: str) -> list[Any]:
    try:
        return list(collection.search_items(_secret_attributes(key_id)))
    except Exception as exc:
        raise IssuerError("Secret Service could not search issuer passphrases") from exc


def _create_secret_service_passphrase(key_id: str) -> tuple[bytes, Any]:
    collection = _secret_collection()
    attributes = _secret_attributes(key_id)
    if _search_secret_service_items(collection, key_id):
        raise IssuerError("Secret Service already contains this issuer key ID")
    passphrase = secrets.token_urlsafe(48).encode("ascii")
    try:
        item = collection.create_item(
            f"Local Connect production issuer {key_id}",
            attributes,
            passphrase,
            replace=False,
        )
    except Exception as exc:
        raise IssuerError(
            "Secret Service could not store the issuer passphrase"
        ) from exc
    return passphrase, item


def _read_secret_service_passphrase(key_id: str) -> bytes:
    collection = _secret_collection()
    items = _search_secret_service_items(collection, key_id)
    if len(items) != 1:
        raise IssuerError(
            "Secret Service must contain exactly one matching issuer passphrase"
        )
    try:
        return items[0].get_secret()
    except Exception as exc:
        raise IssuerError(
            "Secret Service could not read the issuer passphrase"
        ) from exc


def _interactive_passphrase(prompt: str) -> bytes:
    try:
        return getpass.getpass(prompt).encode("utf-8")
    except (EOFError, KeyboardInterrupt, OSError, UnicodeError) as exc:
        raise IssuerError(
            "issuer passphrase prompt was cancelled or unavailable"
        ) from exc


def _interactive_new_passphrase() -> bytes:
    first = _interactive_passphrase("New issuer passphrase: ")
    second = _interactive_passphrase("Confirm issuer passphrase: ")
    if first != second:
        raise IssuerError("issuer passphrases do not match")
    return first


def _rollback_secret_service_item(item: Any) -> None:
    try:
        item.delete()
    except BaseException as exc:
        raise IssuerError("Secret Service issuer rollback failed") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    initialize = commands.add_parser("init", help="Create a new production issuer key")
    initialize.add_argument("--key-id", required=True)
    initialize.add_argument("--private-key", type=Path, required=True)
    initialize.add_argument("--keyring", type=Path, required=True)
    initialize.add_argument("--secret-service", action="store_true")

    issue = commands.add_parser("issue", help="Issue a signed entitlement-v1 file")
    issue.add_argument("--private-key", type=Path, required=True)
    issue.add_argument("--keyring", type=Path, required=True)
    issue.add_argument("--key-id", required=True)
    issue.add_argument("--subject", required=True)
    issue.add_argument("--feature", action="append")
    issue.add_argument("--issued-at")
    issue.add_argument("--not-before")
    issue.add_argument("--expires-at", required=True)
    issue.add_argument("--output", type=Path, required=True)
    issue.add_argument("--secret-service", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    secret_item = None
    try:
        if args.command == "init":
            if args.secret_service:
                passphrase, secret_item = _create_secret_service_passphrase(args.key_id)
            else:
                passphrase = _interactive_new_passphrase()
            try:
                result = initialize_authority(
                    key_id=args.key_id,
                    private_key_path=args.private_key,
                    keyring_path=args.keyring,
                    passphrase=passphrase,
                )
            except BaseException:
                if secret_item is not None:
                    _rollback_secret_service_item(secret_item)
                raise
        else:
            now = datetime.now(timezone.utc).replace(microsecond=0)
            issued_at = _parse_utc(args.issued_at) if args.issued_at else now
            not_before = _parse_utc(args.not_before) if args.not_before else issued_at
            expires_at = _parse_utc(args.expires_at)
            passphrase = (
                _read_secret_service_passphrase(args.key_id)
                if args.secret_service
                else _interactive_passphrase("Issuer passphrase: ")
            )
            result = issue_entitlement(
                private_key_path=args.private_key,
                keyring_path=args.keyring,
                key_id=args.key_id,
                subject=args.subject,
                features=args.feature or [FEATURE_ID],
                issued_at=issued_at,
                not_before=not_before,
                expires_at=expires_at,
                output_path=args.output,
                passphrase=passphrase,
            )
    except IssuerError as exc:
        print(f"Local Connect issuer failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
