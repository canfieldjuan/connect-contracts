# G1 preflight numeric annex

This is the numeric annex referenced by a qualification invocation under the
[permit contract](../../../../plans/PR-Shared-Runtime-U1b-Qualification-Permit.md).
The signer binds the SHA-256 of the exact retained annex bytes. The separate
invocation binds the challenge, candidate, profile, tier and program. This
fixture supplies synthetic ceilings for format tests only.

## Reading the budgets

The phase is `G1`. All ceilings are inclusive unsigned 64-bit integers in
integer JSON notation. Only operations named in the map have a budget. Omission
or zero calls permits no calls of that class. An empty operation map and zero
totals are representable. Every admitted operation must fit its own ceilings
and all applicable totals. A high total cannot authorize an omitted operation.

| Operation | What one call counts | Measured bytes and tokens |
| --- | --- | --- |
| `start_host` | One host-start attempt | No HTTP body |
| `verify_models`, `verify_props` | One identity GET to the respective endpoint | Response body octets. Both GETs have empty bodies. |
| `reverify_models`, `reverify_props` | One GET during re-verification | Same units as the corresponding initial probe |
| `observe_settings` | One independent settings read | Bytes read from the settings source. Interpreting an already charged probe response incurs no second physical read. |
| `tokenize` | One tokenizer POST | Request and response body octets, plus the input token count returned for the submitted input |

`calls` counts physical attempts. The per-call byte and token fields apply to
one offer. The corresponding `total` fields apply across the invocation,
including observation bytes in `response_bytes`. Time ceilings are elapsed durations
measured in milliseconds on a monotonic clock. `total.elapsed_ms` runs from dispatch,
and `elapsed_ms_per_call` also limits the attempt. Generation and canary have
no representation at any level. The client still owns admission, reservation
before side effects, and enforcement against actual sends and responses.

## Exact-byte fixtures

`index.json` records each fixture's SHA-256 and expected outcome. Hash the file
including its final newline. The duplicate-member fixture must reach the strict
reader as bytes. An ordinary JSON load before validation would lose the repeated
key. The completion fixture carries a positive budget for a forbidden operation.

The synthetic fixture is 1041 bytes. With every class present and every counter
at its widest accepted value, the compact encoding is 1213 bytes and the
two-space-indented encoding with final newline is 1516 bytes. The offline byte
reader caps this small metadata object at 2048 bytes before decoding. That
admits both layouts with whitespace headroom while bounding parser work on
untrusted input. The cap excludes padded representations above that size. A
shape check alone cannot bound the raw input. The parser accepts different
member orders and whitespace within this limit. Different bytes have different
digests even when they represent the same limits.

Run `python3 -m unittest tests.test_runtime_g1_preflight` with the repository's
development dependencies. These checks validate bytes and schema shape. A
successful check cannot start a host, claim a permit or enroll a release.
