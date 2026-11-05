"""Compare committed profile blobs at explicit offline migration revisions.

The expected digest comes from the independently reviewed profile, not any input
repository. This is a commit-bound consistency receipt, not source authentication
or runtime admission. Working-tree files are never read.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def _git(root: Path, role: str, operation: str, *args: str) -> bytes:
    # Explicit -C must not be redirected by inherited repository/object settings.
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("GIT_")}
    env.update(GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", "-C", str(root), *args],
            capture_output=True, check=True, timeout=10, env=env)
    except (OSError, subprocess.SubprocessError):
        raise ValueError(f"{role}: cannot {operation}") from None
    return result.stdout


def verify_profile_copies(contracts: Path, client: Path, host: Path,
                          expected_sha256: str, *, contracts_revision: str,
                          client_revision: str, host_revision: str) -> dict:
    if (len(expected_sha256) != 64
            or any(char not in "0123456789abcdef" for char in expected_sha256)):
        raise ValueError("expected digest must be a lowercase SHA-256")
    repositories = {
        "contracts": (contracts, contracts_revision),
        "client": (client, client_revision),
        "host": (host, host_revision),
    }
    revisions = {}
    for role, (root, revision) in repositories.items():
        if not revision:
            raise ValueError(f"{role}: revision is required")
        raw = _git(root, role, "resolve commit", "rev-parse", "--verify",
                   "--end-of-options", f"{revision}^{{commit}}")
        commit = raw.strip().decode("ascii")
        if (len(commit) not in (40, 64)
                or any(char not in "0123456789abcdef" for char in commit)):
            raise ValueError(f"{role}: invalid resolved commit")
        revisions[role] = commit
    paths = {
        "contracts": ("contracts", "runtime/v1/profile.json"),
        "client": ("client", "crates/model-primitives/assets/profile.json"),
        "host_client": ("host", "vendor/local-connect-model-client/crates/model-primitives/assets/profile.json"),
        "host_contracts": ("host", "vendor/connect-contracts/profile.json"),
    }
    copies = {}
    canonical = None
    for role, (repository, path) in paths.items():
        root = repositories[repository][0]
        raw = _git(root, role, "read profile blob", "cat-file", "blob",
                   f"{revisions[repository]}:{path}")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected_sha256:
            raise ValueError(f"{role}: profile digest mismatch")
        if canonical is None:
            canonical = raw
        elif raw != canonical:
            raise ValueError(f"{role}: profile bytes differ")
        copies[role] = {"sha256": digest, "size_bytes": len(raw)}
    return {"expected_sha256": expected_sha256, "revisions": revisions,
            "copies": copies}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for role in ("contracts", "client", "host"):
        parser.add_argument(f"--{role}", type=Path, required=True)
        parser.add_argument(f"--{role}-revision", required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        receipt = verify_profile_copies(
            args.contracts, args.client, args.host, args.expected_sha256,
            contracts_revision=args.contracts_revision,
            client_revision=args.client_revision, host_revision=args.host_revision)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
