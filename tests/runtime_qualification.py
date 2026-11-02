"""Offline evidence reader. No profile admission, task scoring or approval API.

The profile definition validates only the comparison surface. A future host must
supply independently admitted profile bytes and an authenticated instance binding.
Artifact references are opaque: this module never reads their paths or URLs.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_PATH = Path(__file__).resolve().parents[1] / 'schemas/runtime/v1/qualification.schema.json'


class EvidenceError(ValueError):
    """The evidence is malformed or its declared bindings disagree."""


class DuplicateMember(EvidenceError):
    """An input JSON object repeats a member, at any nesting depth."""


def _object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateMember('duplicate JSON member')
        value[key] = item
    return value


def _constant(_value):
    raise EvidenceError('non-JSON numeric constant')


def _parse(raw):
    if not isinstance(raw, bytes):
        raise EvidenceError('raw UTF-8 JSON bytes required')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise EvidenceError('invalid UTF-8 JSON') from error


def _validate(schema, value, label):
    if not Draft202012Validator(schema).is_valid(value):
        # Do not echo private input values in diagnostics.
        raise EvidenceError(label + ' shape invalid')


def _observations(record):
    for group in ('device', 'effective_settings', 'concurrency'):
        for name, observation in record[group].items():
            yield group + '.' + name, observation


@dataclass(frozen=True)
class Inspection:
    # Completeness is only a diagnostic snapshot of this validation; not authority.
    record: dict
    missing_observations: tuple[str, ...]

    @property
    def complete(self):
        return not self.missing_observations


def inspect_record(record_bytes, *, profile_bytes, expected_instance_id):
    """Validate one offline record without rewriting input or deciding task PASS.

    expected_instance_id is supplied independently by the conformance/capture
    caller, not inferred from the submitted record. This function does not
    authenticate it, the source-binding table or the raw evidence artifacts.
    """
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    record = _parse(record_bytes)
    profile = _parse(profile_bytes)
    _validate(schema, record, 'record')
    _validate({'$ref': '#/$defs/profile_binding', '$defs': schema['$defs']}, profile, 'profile binding')
    _validate({'$ref': '#/$defs/sha256', '$defs': schema['$defs']}, expected_instance_id, 'expected instance')

    # This is the single owner of cross-artifact rules that schemas cannot express.
    if sha256(profile_bytes).hexdigest() != record['profile_id']:
        raise EvidenceError('profile digest mismatch')
    if profile['platform'] != record['platform']:
        raise EvidenceError('profile platform mismatch')
    if record['intended']['profile']['sha256'] != record['profile_id']:
        raise EvidenceError('profile intent mismatch')
    ids = [tier['id'] for tier in profile['tiers']]
    if len(set(ids)) != len(ids):
        raise EvidenceError('duplicate profile tier')
    selected = [tier for tier in profile['tiers'] if tier['id'] == record['tier']]
    if len(selected) != 1:
        raise EvidenceError('selected profile tier missing')
    tier = selected[0]
    expected_class = {'cuda': 'nvidia-cuda', 'vulkan': 'vulkan-discrete'}[record['backend']]
    if tier['device_class'] != expected_class:
        raise EvidenceError('profile backend mismatch')
    if tier['runtime']['archive']['sha256'] != record['runtime_archive_sha256']:
        raise EvidenceError('profile archive mismatch')
    if tier['model']['sha256'] != record['model_sha256']:
        raise EvidenceError('profile model mismatch')
    if record['instance_id'] != expected_instance_id:
        raise EvidenceError('record instance mismatch')

    missing = []
    for path, observation in _observations(record):
        if observation['state'] == 'unavailable':
            missing.append(path)
        elif observation['source']['instance_id'] != expected_instance_id:
            raise EvidenceError('observation instance mismatch')
    setting_slots = record['effective_settings']['slots']
    workload_slots = record['concurrency']['slots']
    if setting_slots['state'] == workload_slots['state'] == 'observed':
        if setting_slots['value'] != workload_slots['value']:
            raise EvidenceError('slot observations disagree')
    return Inspection(record, tuple(missing))
