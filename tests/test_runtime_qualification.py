"""Offline evidence conformance only: no model, host or application calls."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from tests.runtime_qualification import DuplicateMember, EvidenceError, inspect_record

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / 'schemas/runtime/v1/qualification.schema.json'
FIXTURES = ROOT / 'fixtures/runtime/v1/qualification'
MAX = 9007199254740991
EXPECTED_INSTANCE = json.loads((FIXTURES / 'cuda-complete.json').read_bytes())['instance_id']


def raw(value):
    return (json.dumps(value, ensure_ascii=False) + '\n').encode()


def pairs():
    for backend, platform in [('cuda', 'linux-x64'), ('vulkan', 'windows-x64')]:
        yield (json.loads((FIXTURES / (backend + '-complete.json')).read_bytes()),
               (FIXTURES / (platform + '-profile-binding.json')).read_bytes())


def inspect(record, profile, instance=EXPECTED_INSTANCE):
    return inspect_record(raw(record), profile_bytes=profile,
                          expected_instance_id=instance)


def bind_profile(record, profile):
    profile_bytes = raw(profile)
    record['profile_id'] = sha256(profile_bytes).hexdigest()
    record['intended']['profile']['sha256'] = record['profile_id']
    return profile_bytes


def observations(record):
    return [(group, name) for group in ('device', 'effective_settings', 'concurrency')
            for name in record[group]]


def objects(value, path=()):
    if isinstance(value, dict):
        yield path
        for key, child in value.items():
            yield from objects(child, path + (key,))
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from objects(child, path + (i,))


def at(value, path):
    for key in path:
        value = value[key]
    return value


class QualificationContractTests(unittest.TestCase):
    def test_schema_is_closed_and_valid(self):
        self.assertTrue(SCHEMA.is_file(), 'canonical qualification schema is absent')
        schema = json.loads(SCHEMA.read_text())
        Draft202012Validator.check_schema(schema)
        self.assertIs(schema['additionalProperties'], False)

    def test_schema_only_observation_discriminators(self):
        # The reader's state/source access must not mask a lost schema guard.
        validator = Draft202012Validator(json.loads(SCHEMA.read_text()))
        for base, _ in pairs():
            observed = base['device']['name']
            unavailable = {'state': 'unavailable', 'reason': 'not_reported'}
            for valid in (observed, unavailable):
                record = copy.deepcopy(base)
                record['device']['name'] = valid
                self.assertTrue(validator.is_valid(record))
            corruptions = [
                ('missing unavailable state', {'reason': 'not_reported'}),
                ('missing unavailable reason', {'state': 'unavailable'}),
                ('unknown unavailable state', dict(unavailable, state='garbage')),
                ('wrong unavailable state', dict(unavailable, state='observed')),
                ('unknown observed state', dict(observed, state='garbage')),
                ('wrong observed state', dict(observed, state='unavailable')),
            ]
            for key in ('state', 'value', 'source'):
                missing = copy.deepcopy(observed)
                del missing[key]
                corruptions.append(('missing observed ' + key, missing))
            for name, observation in corruptions:
                with self.subTest(backend=base['backend'], case=name):
                    record = copy.deepcopy(base)
                    record['device']['name'] = observation
                    self.assertFalse(validator.is_valid(record))

    def test_schema_only_backend_tier_and_platform_discrimination(self):
        schema = json.loads(SCHEMA.read_text())
        validator = Draft202012Validator(schema)
        for base, _ in pairs():
            self.assertTrue(validator.is_valid(base))
            other = 'vulkan' if base['backend'] == 'cuda' else 'cuda'
            for key, value in [('backend', other), ('tier', 'gpu-' + other),
                               ('backend', 'unknown'), ('tier', 'unknown'),
                               ('platform', 'unknown')]:
                with self.subTest(backend=base['backend'], field=key, value=value):
                    record = copy.deepcopy(base)
                    record[key] = value
                    self.assertFalse(validator.is_valid(record))
        # The enums are redundant under root oneOf; exercise their canonical
        # definitions directly instead of inventing a root-level counterexample.
        for key, accepted in [('backend', ('cuda', 'vulkan')),
                              ('tier', ('gpu-cuda', 'gpu-vulkan'))]:
            field_validator = Draft202012Validator(schema['properties'][key])
            for value in accepted:
                self.assertTrue(field_validator.is_valid(value))
            for value in ('unknown', '', False, 0, None):
                with self.subTest(field=key, value=value):
                    self.assertFalse(field_validator.is_valid(value))

    def test_nonfinite_constants_fail_at_reader_ingestion(self):
        base, profile = next(pairs())
        for token in ('NaN', 'Infinity', '-Infinity'):
            record = copy.deepcopy(base)
            record['effective_settings']['context_checkpoints']['value'] = float(token)
            # Replacing this constant with zero would produce a valid record.
            profile_with_constant = json.loads(profile)
            profile_with_constant['outside_comparison_surface'] = float(token)
            bound_record = copy.deepcopy(base)
            bound_profile = bind_profile(bound_record, profile_with_constant)
            inputs = [(token.encode(), profile), (raw(base), token.encode()),
                      (raw(record), profile), (raw(bound_record), bound_profile)]
            for number, (record_bytes, profile_bytes) in enumerate(inputs):
                with self.subTest(token=token, input=number):
                    with self.assertRaisesRegex(EvidenceError, '^non-JSON numeric constant$'):
                        inspect_record(record_bytes, profile_bytes=profile_bytes,
                                       expected_instance_id=EXPECTED_INSTANCE)

    def test_frozen_fixture_inventory(self):
        index = json.loads((FIXTURES / 'index.json').read_bytes())
        # The exhaustive file inventory remains test_runtime_contracts' owner.
        for case in index:
            with self.subTest(case=case['record']):
                args = dict(profile_bytes=(FIXTURES / case['profile']).read_bytes(),
                            expected_instance_id=case['expected_instance_id'])
                if case['valid']:
                    result = inspect_record((FIXTURES / case['record']).read_bytes(), **args)
                    self.assertEqual(result.complete, case['complete'])
                else:
                    with self.assertRaises(EvidenceError) as error:
                        inspect_record((FIXTURES / case['record']).read_bytes(), **args)
                    self.assertEqual(str(error.exception), case['error'])

    def test_every_observation_can_be_explicitly_unavailable(self):
        for base, profile in pairs():
            for group, name in observations(base):
                for reason in ('not_collected', 'not_reported', 'source_error'):
                    with self.subTest(backend=base['backend'], group=group, name=name, reason=reason):
                        record = copy.deepcopy(base)
                        record[group][name] = {'state': 'unavailable', 'reason': reason}
                        result = inspect(record, profile)
                        self.assertFalse(result.complete)
                        self.assertEqual(result.missing_observations, (group + '.' + name,))
                        self.assertEqual(result.record['task_evidence'], base['task_evidence'])
                        for key, value in [('value', 0), ('source', base[group][name]['source']),
                                           ('reason', ''), ('reason', 'guessed')]:
                            bad = copy.deepcopy(record)
                            bad[group][name][key] = value
                            with self.assertRaises(EvidenceError):
                                inspect(bad, profile)

    def test_all_unavailable_retains_all_paths_and_task_receipts(self):
        for record, profile in pairs():
            for group, name in observations(record):
                record[group][name] = {'state': 'unavailable', 'reason': 'not_collected'}
            result = inspect(record, profile)
            self.assertEqual(set(result.missing_observations),
                             {g + '.' + n for g, n in observations(record)})
            self.assertEqual(result.record, record)
            self.assertFalse(result.complete)

    def test_every_record_object_is_closed_and_every_member_required(self):
        for base, profile in pairs():
            for path in objects(base):
                with self.subTest(backend=base['backend'], path=path):
                    record = copy.deepcopy(base)
                    at(record, path)['unexpected'] = 'no'
                    with self.assertRaises(EvidenceError):
                        inspect(record, profile)
                    for key in at(base, path):
                        record = copy.deepcopy(base)
                        del at(record, path)[key]
                        with self.assertRaises(EvidenceError):
                            inspect(record, profile)

    def test_wrong_variants_and_false_approval_fields(self):
        for base, profile in pairs():
            for key, value in [('record_version', 0), ('record_version', 2),
                               ('record_version', False), ('backend', 'cpu'),
                               ('backend', 'vulkan' if base['backend'] == 'cuda' else 'cuda'),
                               ('platform', 'macos'), ('tier', 'cpu'), ('qualified', True),
                               ('status', 'PASS'), ('approval', {})]:
                with self.subTest(key=key, value=value):
                    record = copy.deepcopy(base)
                    record[key] = value
                    with self.assertRaises(EvidenceError):
                        inspect(record, profile)

    def test_observed_value_type_and_count_boundaries(self):
        for base, profile in pairs():
            for group, name in observations(base):
                original = base[group][name]['value']
                if type(original) is bool:
                    good, bad = [False, True], [0, 1, '', None, [], 'false']
                elif type(original) is int:
                    minimum = 0 if name in ('context_checkpoints', 'offloaded_layers') else 1
                    good, bad = [minimum, MAX], [minimum - 1, MAX + 1, False, '', None, 1.5, []]
                elif type(original) is str:
                    good, bad = ['x', 'x' * 256], ['', ' ' * 3, 'x' * 257, 0, False, None, []]
                else:
                    good, bad = [{'major': 0, 'minor': 0}, {'major': MAX, 'minor': MAX}], [0, False, '', None, {}, {'major': -1, 'minor': 1}, {'major': True, 'minor': 1}, {'major': MAX+1, 'minor': 0}]
                for valid, values in [(True, good), (False, bad)]:
                    for value in values:
                        with self.subTest(backend=base['backend'], group=group, name=name, value=value):
                            record = copy.deepcopy(base)
                            record[group][name]['value'] = value
                            if name == 'slots':
                                record['effective_settings']['slots']['value'] = value
                                record['concurrency']['slots']['value'] = value
                            if valid:
                                self.assertTrue(inspect(record, profile).complete)
                            else:
                                with self.assertRaises(EvidenceError):
                                    inspect(record, profile)

    def test_every_observed_source_binds_expected_instance_and_kind(self):
        for base, profile in pairs():
            for group, name in observations(base):
                with self.subTest(group=group, name=name):
                    record = copy.deepcopy(base)
                    record[group][name]['source']['instance_id'] = 'f' * 64
                    with self.assertRaisesRegex(EvidenceError, '^observation instance mismatch$'):
                        inspect(record, profile)
                    for kind in ('device', 'server', 'request', 'workload', 'unknown'):
                        record = copy.deepcopy(base)
                        record[group][name]['source']['kind'] = kind
                        if kind == base[group][name]['source']['kind']:
                            self.assertTrue(inspect(record, profile).complete)
                        else:
                            with self.assertRaises(EvidenceError):
                                inspect(record, profile)
            with self.assertRaisesRegex(EvidenceError, '^record instance mismatch$'):
                inspect(base, profile, 'f' * 64)
            record = copy.deepcopy(base)
            record['instance_id'] = 'f' * 64
            with self.assertRaisesRegex(EvidenceError, '^record instance mismatch$'):
                inspect(record, profile)
            for invalid in ('', False, None, 'f' * 63, 'f' * 65, 'g' * 64):
                with self.assertRaises(EvidenceError):
                    inspect_record(raw(base), profile_bytes=profile, expected_instance_id=invalid)

    def test_each_cross_artifact_comparison_and_slots(self):
        base, original_profile = next(pairs())
        cases = [('profile_id', '1' * 64, 'profile digest mismatch'),
                 ('platform', 'windows-x64', 'profile platform mismatch'),
                 ('runtime_archive_sha256', '1' * 64, 'profile archive mismatch'),
                 ('model_sha256', '1' * 64, 'profile model mismatch')]
        for key, value, message in cases:
            record = copy.deepcopy(base)
            record[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(EvidenceError, '^' + message + '$'):
                inspect(record, original_profile)
        record = copy.deepcopy(base)
        record['intended']['profile']['sha256'] = '1' * 64
        with self.assertRaisesRegex(EvidenceError, '^profile intent mismatch$'):
            inspect(record, original_profile)
        record = copy.deepcopy(base)
        record['concurrency']['slots']['value'] = 2
        with self.assertRaisesRegex(EvidenceError, '^slot observations disagree$'):
            inspect(record, original_profile)
        for case in ('duplicate', 'missing', 'backend'):
            record = copy.deepcopy(base)
            profile = json.loads(original_profile)
            if case == 'duplicate':
                profile['tiers'].append(copy.deepcopy(profile['tiers'][0]))
            elif case == 'missing':
                profile['tiers'] = profile['tiers'][1:]
            else:
                profile['tiers'][0]['device_class'] = 'vulkan-discrete'
            message = {'duplicate': 'duplicate profile tier', 'missing': 'selected profile tier missing',
                       'backend': 'profile backend mismatch'}[case]
            profile_bytes = bind_profile(record, profile)
            with self.subTest(case=case), self.assertRaisesRegex(EvidenceError, '^' + message + '$'):
                inspect(record, profile_bytes)

    def test_profile_comparison_surface_types_and_required_fields(self):
        base, original = next(pairs())
        for path in objects(json.loads(original)):
            for key in at(json.loads(original), path):
                profile = json.loads(original)
                del at(profile, path)[key]
                record = copy.deepcopy(base)
                encoded = bind_profile(record, profile)
                with self.subTest(path=path, key=key), self.assertRaises(EvidenceError):
                    inspect(record, encoded)
        for profile in (None, [], False, {'platform': 'linux-x64', 'tiers': []}):
            record = copy.deepcopy(base)
            with self.assertRaises(EvidenceError):
                inspect(record, bind_profile(record, profile))
        record = copy.deepcopy(base)
        profile = json.loads(original)
        profile['not_part_of_binding_validation'] = 'retained but not admitted'
        self.assertTrue(inspect(record, bind_profile(record, profile)).complete)

    def test_backend_variants_are_independent_of_platform(self):
        for base, original in pairs():
            for platform in ('linux-x64', 'windows-x64'):
                with self.subTest(backend=base['backend'], platform=platform):
                    record = copy.deepcopy(base)
                    profile = json.loads(original)
                    record['platform'] = profile['platform'] = platform
                    self.assertTrue(inspect(record, bind_profile(record, profile)).complete)

    def test_duplicate_ingestion_and_non_json_constants_are_not_hidden(self):
        record, profile = next(pairs())
        duplicate_record = raw(record).replace(b'"record_version": 1', b'"record_version": 1, "record_version": 1', 1)
        nested = raw(record).replace(b'"state": "observed"', b'"state": "unavailable", "state": "observed"', 1)
        duplicate_profile = profile.replace(b'"platform": "linux-x64"', b'"platform": "windows-x64", "platform": "linux-x64"', 1)
        nested_profile = profile.replace(b'"id": "gpu-cuda"', b'"id": "gpu-vulkan", "id": "gpu-cuda"', 1)
        for r, p in [(duplicate_record, profile), (nested, profile),
                     (raw(record), duplicate_profile), (raw(record), nested_profile)]:
            with self.assertRaises(DuplicateMember):
                inspect_record(r, profile_bytes=p, expected_instance_id=record['instance_id'])
        for invalid in (b'NaN', b'Infinity', b'-Infinity', b'{} trailing', b'\xff', b'{', {}, 'text'):
            for r, p in [(invalid, profile), (raw(record), invalid)]:
                with self.subTest(invalid=invalid), self.assertRaises(EvidenceError):
                    inspect_record(r, profile_bytes=p, expected_instance_id=record['instance_id'])

    def test_raw_bytes_are_preserved_and_profile_hash_is_not_reserialized(self):
        record, profile = next(pairs())
        encoded = b' \n' + raw(record) + b'\n'
        before = (encoded, profile)
        result = inspect_record(encoded, profile_bytes=profile, expected_instance_id=record['instance_id'])
        self.assertEqual((encoded, profile), before)
        self.assertEqual(result.record, record)
        self.assertEqual(list(result.record), list(record))
        # Parsed-profile equality must not make a changed byte stream share its digest.
        same_profile = raw(json.loads(profile))
        self.assertNotEqual(same_profile, profile)
        with self.assertRaisesRegex(EvidenceError, '^profile digest mismatch$'):
            inspect(record, same_profile)
        self.assertTrue(inspect(record, bind_profile(record, json.loads(profile))).complete)

    def test_complete_evidence_is_not_task_pass_and_no_outcome_is_lost(self):
        record, profile = next(pairs())
        result = inspect(record, profile)
        self.assertTrue(result.complete)
        self.assertEqual(result.record['task_evidence'], record['task_evidence'])
        self.assertEqual(result.record['task_evidence'][0]['alias'], 'synthetic-failed-task-and-pending-review')
        record['task_evidence'] = []
        self.assertTrue(inspect(record, profile).complete)

    def test_artifact_hash_and_alias_boundaries(self):
        base, profile = next(pairs())
        fields = {
            'sha256': (['0' * 64, 'f' * 64],
                       ['', 'f' * 63, 'f' * 65, 'F' * 64, 'g' * 64, 'f' * 64 + '\n', False, 0]),
            'alias': (['a', 'a' * 128, 'a-0_1.json'],
                      ['', 'a' * 129, '../a', '/a', 'a\\b', 'a\n', ' a', 'a ', False, 0]),
        }
        for key, (good, bad) in fields.items():
            for valid, values in [(True, good), (False, bad)]:
                for value in values:
                    with self.subTest(key=key, value=value):
                        record = copy.deepcopy(base)
                        record['task_evidence'][0][key] = value
                        if valid:
                            self.assertTrue(inspect(record, profile).complete)
                        else:
                            with self.assertRaises(EvidenceError):
                                inspect(record, profile)


if __name__ == '__main__':
    unittest.main()
