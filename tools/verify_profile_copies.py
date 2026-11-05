"""Compare original profile bytes in trusted offline migration checkouts.

The expected digest comes from the independently reviewed profile, not any input
checkout. This is a consistency receipt, not source authentication or admission.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def verify_profile_copies(contracts: Path, client: Path, host: Path,
                          expected_sha256: str) -> dict:
    if (len(expected_sha256) != 64
            or any(char not in "0123456789abcdef" for char in expected_sha256)):
        raise ValueError("expected digest must be a lowercase SHA-256")
    paths = {
        "contracts": contracts / "runtime/v1/profile.json",
        "client": client / "crates/model-primitives/assets/profile.json",
        "host_client": host / "vendor/local-connect-model-client/crates/model-primitives/assets/profile.json",
        "host_contracts": host / "vendor/connect-contracts/profile.json",
    }
    copies = {}
    canonical = None
    for role, path in paths.items():
        try:
            raw = path.read_bytes()
        except OSError:
            raise ValueError(f"{role}: cannot read profile") from None
        digest = hashlib.sha256(raw).hexdigest()
        if digest != expected_sha256:
            raise ValueError(f"{role}: profile digest mismatch")
        if canonical is None:
            canonical = raw
        elif raw != canonical:
            raise ValueError(f"{role}: profile bytes differ")
        copies[role] = {"sha256": digest, "size_bytes": len(raw)}
    return {"expected_sha256": expected_sha256, "copies": copies}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, required=True)
    parser.add_argument("--client", type=Path, required=True)
    parser.add_argument("--host", type=Path, required=True)
    parser.add_argument("--expected-sha256", required=True)
    args = parser.parse_args()
    try:
        receipt = verify_profile_copies(
            args.contracts, args.client, args.host, args.expected_sha256)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
