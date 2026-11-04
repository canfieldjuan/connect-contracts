"""Raw evidence admission only; schemas, task scores and model calls stay separate."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from jsonschema import Draft202012Validator

from tests.runtime_qualification import DuplicateMember, EvidenceError, _parse, inspect_record
from tests import runtime_qualification as numeric_owner
from tests import test_runtime_companion as companion
from tests import test_runtime_contracts as inventory
from tests import test_runtime_qualification as qualification

FIXTURES = qualification.FIXTURES.parent / 'numeric-ingestion'


def cases():
    # The index is trusted test metadata, not raw evidence input.
    return json.loads((FIXTURES / 'index.json').read_bytes())


def schema_validator(kind):
    if kind == 'companion':
        return companion.validator('companion.schema.json')
    schema = json.loads(qualification.SCHEMA.read_bytes())
    definition = {'sequence': 'positive_count', 'profile': 'profile_binding'}[kind]
    return Draft202012Validator({'$ref': '#/$defs/' + definition, '$defs': schema['$defs']})


class NumericIngestionTests(unittest.TestCase):
    def test_exact_integer_domain_and_adjacent_refusals(self):
        for token, value in [(b'-9223372036854775808', -(2**63)),
                             (b'18446744073709551615', 2**64 - 1)]:
            with self.subTest(control=token):
                self.assertIs(type(_parse(token)), int)
                self.assertEqual(_parse(token), value)
        for token in (b'-9223372036854775809', b'18446744073709551616'):
            with self.subTest(overflow=token):
                with self.assertRaisesRegex(EvidenceError, '^invalid evidence integer$'):
                    _parse(token)

    def test_rounding_reproductions_are_refused_before_schema(self):
        for name in ('rounded-sequence', 'rounded-one',
                     'manifest-rounded-sequence', 'manifest-rounded-one'):
            with self.subTest(case=name):
                raw = (FIXTURES / (name + '.json')).read_bytes()
                # The historical parser really makes these schema-valid.
                kind = 'companion' if name.startswith('manifest-') else 'sequence'
                self.assertTrue(schema_validator(kind).is_valid(json.loads(raw)))
                with self.assertRaisesRegex(EvidenceError, '^integer JSON notation required$'):
                    _parse(raw)

    def test_oversized_tokens_never_reach_integer_conversion(self):
        # Patch only the owner's conversion lookup, not process-wide builtins.
        with patch.object(numeric_owner, 'int', create=True,
                          side_effect=AssertionError('oversized token reached int')) as conversion:
            for length in (21, 4301):
                for sign in ('', '-'):
                    with self.subTest(length=length, sign=sign):
                        with self.assertRaisesRegex(EvidenceError, '^invalid evidence integer$'):
                            _parse((sign + '1' * length).encode())
            conversion.assert_not_called()

    def test_oversized_tokens_are_evidence_errors_in_fresh_interpreter(self):
        # Set the limit only at process startup; never mutate the test process.
        script = '''
import json, sys
from pathlib import Path
from tests.runtime_qualification import _parse
results = []
for name in ('positive-4301-digits.json', 'negative-4301-digits.json'):
    try:
        _parse((Path(sys.argv[1]) / name).read_bytes())
    except Exception as error:
        results.append(type(error).__name__)
    else:
        results.append('accepted')
print(json.dumps({'limit': sys.get_int_max_str_digits(), 'results': results}))
'''
        process = subprocess.run(
            [sys.executable, '-B', '-X', 'int_max_str_digits=4300', '-c',
             script, str(FIXTURES)], cwd=qualification.ROOT, text=True,
            capture_output=True, timeout=20, check=True)
        self.assertEqual(json.loads(process.stdout),
                         {'limit': 4300, 'results': ['EvidenceError', 'EvidenceError']})

    def test_frozen_raw_cases_and_separate_schema_outcomes(self):
        for case in cases():
            with self.subTest(case=case['fixture']):
                raw = (FIXTURES / case['fixture']).read_bytes()
                self.assertEqual(len(raw), case['bytes'])
                self.assertEqual(sha256(raw).hexdigest(), case['sha256'])
                expected = case['ingestion']
                if not expected['accepted']:
                    with self.assertRaises(EvidenceError) as caught:
                        _parse(raw)
                    self.assertEqual(str(caught.exception), expected['error'])
                    self.assertIsNone(case['schema']['valid'])
                    continue
                value = _parse(raw)
                wanted = json.loads(expected['expected_json'])
                self.assertEqual(value, wanted)
                for path, item in companion.nodes(wanted):
                    self.assertIs(type(companion.at(value, path)), type(item))
                kind = case['schema']['kind']
                if kind != 'none':
                    self.assertEqual(schema_validator(kind).is_valid(value), case['schema']['valid'])

    def test_schema_semantics_are_not_replaced_by_raw_policy(self):
        v = schema_validator('sequence')
        # Schema-only probes intentionally bypass raw numeric admission.
        for value in (1, 1.0, 100.0, 9007199254740991):
            self.assertTrue(v.is_valid(value))
        for value in (0, False, None, '', 1.5, 9007199254740992):
            self.assertFalse(v.is_valid(value))

    def test_profile_extras_use_ingestion_before_binding(self):
        base, _ = next(qualification.pairs())
        for suffix, valid in [('min', True), ('max', True), ('under', False), ('over', False)]:
            with self.subTest(extra=suffix):
                record = copy.deepcopy(base)
                profile = (FIXTURES / ('profile-extra-' + suffix + '.json')).read_bytes()
                record['profile_id'] = sha256(profile).hexdigest()
                record['intended']['profile']['sha256'] = record['profile_id']
                if valid:
                    result = inspect_record(qualification.raw(record), profile_bytes=profile,
                                            expected_instance_id=record['instance_id'])
                    self.assertTrue(result.complete)
                else:
                    with self.assertRaisesRegex(EvidenceError, '^invalid evidence integer$'):
                        inspect_record(qualification.raw(record), profile_bytes=profile,
                                       expected_instance_id=record['instance_id'])

    def test_record_ingestion_does_not_round_version(self):
        record, profile = next(qualification.pairs())
        raw = qualification.raw(record)
        self.assertEqual(raw.count(b'"record_version": 1'), 1)
        raw = raw.replace(b'"record_version": 1', b'"record_version": 1.0000000000000000001')
        with self.assertRaisesRegex(EvidenceError, '^integer JSON notation required$'):
            inspect_record(raw, profile_bytes=profile, expected_instance_id=record['instance_id'])

    def test_evidence_fixture_loaders_share_raw_admission(self):
        read_bytes = Path.read_bytes
        targets = [
            (companion.FIXTURES / 'manifest-empty.json',
             lambda: companion.fixture('manifest-empty.json'), b'"sequence": 1', b'"sequence": -0'),
            (qualification.FIXTURES / 'cuda-complete.json',
             lambda: next(qualification.pairs()), b'"record_version": 1', b'"record_version": -0'),
        ]
        for path, call, before, after in targets:
            raw = read_bytes(path)
            self.assertEqual(raw.count(before), 1)
            poisoned = raw.replace(before, after)
            def read(p):
                return poisoned if p == path else read_bytes(p)
            with self.subTest(path=path.name), patch.object(Path, 'read_bytes', read):
                with self.assertRaisesRegex(EvidenceError, '^invalid evidence integer$'):
                    call()

    def test_other_raw_failures_keep_their_owners(self):
        for raw in (b'\xef\xbb\xbf{}', b'\xff', b'{} trailing'):
            with self.subTest(raw_length=len(raw)):
                with self.assertRaisesRegex(EvidenceError, '^invalid UTF-8 JSON$'):
                    _parse(raw)
        with self.assertRaisesRegex(EvidenceError, '^raw UTF-8 JSON bytes required$'):
            _parse('1')
        with self.assertRaises(DuplicateMember):
            _parse(b'{"x":[{"a":1,"a":2}]}')
        # Byte/depth limits of the future bundle API are not invented here.

    def test_numeric_inventory_rejects_unlisted_and_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'runtime'
            shutil.copytree(inventory.FIXTURES, target)
            check = inventory.RuntimeContractTests('test_fixture_inventory_is_complete')
            with patch.object(inventory, 'FIXTURES', target):
                check.test_fixture_inventory_is_complete()
                extra = target / 'numeric-ingestion/unlisted.json'
                extra.write_text('0\n')
                with self.assertRaisesRegex(AssertionError, 'numeric-ingestion/unlisted.json'):
                    check.test_fixture_inventory_is_complete()
                extra.unlink()
                index = target / 'numeric-ingestion/index.json'
                rows = json.loads(index.read_bytes())
                index.write_text(json.dumps(rows + [rows[0]]))
                with self.assertRaises(AssertionError):
                    check.test_fixture_inventory_is_complete()
