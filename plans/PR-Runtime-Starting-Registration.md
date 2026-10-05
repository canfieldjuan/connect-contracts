# Runtime registration before profile and device admission

## Root cause

ADR-0011 requires a `starting` registration before any file check or tier probe.
The server schema requires a selected tier, model hash, context, build and
template hash in every state. Its only starting fixture already chose CUDA.
The initial host therefore cannot publish truthful progress under that schema.
The direct probe against `e1ada18a262144f564fe6811088bd2c48dbfd8ba` rejects the
unknown values. This is an existing canonical contract gap, not a host failure.

## Required change surface

- Clarify ADR-0011's pre-admission starting record. Keep the existing keys;
  represent the complete unselected runtime group with null, including device
  and server. Host identity, profile id, start id, socket and deadline are known.
- Make the canonical server schema admit that complete group only in starting.
  Preserve fully selected starting, ready and stopping records. Reject partial
  selections, unknown ready/stopping details, or a server before selection.
- Adjust the offline semantic check to consume the schema's state distinction.
  Add the pre-admission public fixture and boundary regressions.

## Explicit non-scope

No profile bytes, runtime pins, argv, GPU policy, Connect protocols, application
code, executable host, download logic or entitlement changes. This does not
prove startup or qualify the model.

## Assumptions and compatibility

There is no deployed shared host implementation yet. Consumers must adopt this
schema revision before using the newly representable starting record. A starting
record never authorizes inference; ready identity and peer checks stay required.
The known profile id is the expected digest supplied by the client, not evidence
that the host has admitted the profile bytes yet.

## Verification plan

Fail first on a complete pre-admission starting record. Then prove it passes,
while fully selected existing fixtures still pass. Probe every partial runtime
group, absent keys, invalid states, falsy values, and pre-selection server/device.
Exercise schema validation directly as well as the offline conformance helper.
Run the affected runtime contract suite and repository contract checks when CI
is unavailable. Inspect the final diff and confirm profile bytes did not change.

## Implementation summary

Pending.

## Cold diff audit

Pending.

## Gap audit

NOT DONE. Contract committed before implementation; regression and fix pending.
