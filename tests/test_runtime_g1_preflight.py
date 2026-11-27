"""Public conformance vectors for the unsigned G1 numeric annex."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator

from tests.runtime_qualification import DuplicateMember, EvidenceError, check_g1_preflight_annex

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads((ROOT / 'schemas/runtime/v1/g1-preflight-annex.schema.json').read_bytes())
RAW = (ROOT / 'fixtures/runtime/v1/g1-preflight/synthetic.json').read_bytes()
SAMPLE = json.loads(RAW)
MAX_U64 = 2**64 - 1


def with_counters(value, number):
    if isinstance(value, dict):
        return {key: with_counters(item, number) for key, item in value.items()}
    return number if type(value) is int else value


class G1Annex(unittest.TestCase):
    def test_generation_absent_from_operations(self):
        for unwanted in ('completion', 'canary', 'generate', 'url'):
            with self.subTest(unwanted=unwanted):
                plan = deepcopy(SAMPLE)
                plan['operations'][unwanted] = {'calls': 0}
                with self.assertRaisesRegex(EvidenceError, 'shape invalid'):
                    check_g1_preflight_annex(json.dumps(plan).encode())

    def test_frozen_bytes(self):
        folder = ROOT / 'fixtures/runtime/v1/g1-preflight'
        index = json.loads((folder / 'index.json').read_bytes())
        expected_outcomes = {
            'synthetic.json': 'valid',
            'completion.invalid.json': 'shape-invalid',
            'duplicate.invalid.json': 'duplicate-member',
        }
        self.assertEqual(set(index), set(expected_outcomes))
        for name, expected in expected_outcomes.items():
            with self.subTest(name=name):
                self.assertEqual(index[name]['outcome'], expected)
                digest = sha256((folder / name).read_bytes()).hexdigest()
                self.assertEqual(digest, index[name]['sha256'])
        self.assertIsNone(check_g1_preflight_annex(RAW))
        with self.assertRaisesRegex(EvidenceError, 'shape invalid'):
            check_g1_preflight_annex((folder / 'completion.invalid.json').read_bytes())
        with self.assertRaises(DuplicateMember):
            check_g1_preflight_annex((folder / 'duplicate.invalid.json').read_bytes())

    def test_allowed_subsets_and_counter_boundaries(self):
        Draft202012Validator.check_schema(SCHEMA)
        for number in (0, 1, MAX_U64 - 1, MAX_U64):
            plan = with_counters(SAMPLE, number)
            check_g1_preflight_annex(json.dumps(plan).encode())
        check_g1_preflight_annex(json.dumps(dict(SAMPLE, operations={})).encode())
        for name, budget in SAMPLE['operations'].items():
            plan = dict(SAMPLE, operations={name: budget})
            check_g1_preflight_annex(json.dumps(plan).encode())

    def test_schema_boundaries(self):
        # Exercise the portable schema on structured values independently of
        # lexical rejection in the Python byte reader.
        validator = Draft202012Validator(SCHEMA)

        def reject(path, candidate, *, omit=False):
            plan = deepcopy(SAMPLE)
            if path:
                parent = plan
                for key in path[:-1]:
                    parent = parent[key]
                if omit:
                    del parent[path[-1]]
                else:
                    parent[path[-1]] = candidate
            else:
                plan = candidate
            with self.subTest(path=path, candidate=candidate, omit=omit):
                self.assertFalse(validator.is_valid(plan))

        reject(('phase',), 'G2')
        for key in SAMPLE:
            reject((key,), None, omit=True)
        counters_by_path = {('total',): SAMPLE['total']}
        for name, budget in SAMPLE['operations'].items():
            counters_by_path['operations', name] = budget
        for probe in ('verify_models', 'verify_props', 'reverify_models', 'reverify_props'):
            reject(('operations', probe, 'request_bytes_per_call'), 1)
        for path in [(), ('operations',), *counters_by_path]:
            reject(path, [])
            reject((*path, 'generation_allowance'), 0)
        for prefix, counters in counters_by_path.items():
            for key in counters:
                path = (*prefix, key)
                reject(path, None, omit=True)
                for value in (-1, MAX_U64 + 1, False, '', 0.5):
                    reject(path, value)

    def test_strict_bytes_and_lexical_forms(self):
        # Start from raw bytes so decoding cannot erase lexical differences.
        for token in (b'false', b'""', b'-0', b'1.0', b'1e0', b'18446744073709551616'):
            raw = RAW.replace(b'"calls": 7', b'"calls": ' + token, 1)
            with self.subTest(token=token), self.assertRaises(EvidenceError):
                check_g1_preflight_annex(raw)
        for raw in (b'', b'\xff', RAW + b'{}', b'[' * 1000 + b']' * 1000):
            with self.assertRaises(EvidenceError):
                check_g1_preflight_annex(raw)
        for target in (b'"phase": "G1"', b'"calls": 7', b'"calls": 1'):
            with self.subTest(target=target), self.assertRaises(DuplicateMember):
                check_g1_preflight_annex(RAW.replace(target, target + b',' + target, 1))

    def test_measured_size_and_predecode_limit(self):
        widest = with_counters(SAMPLE, MAX_U64)
        self.assertEqual(len(json.dumps(widest, separators=(',', ':')).encode()), 1213)
        self.assertEqual(len((json.dumps(widest, indent=2) + '\n').encode()), 1516)
        for size in (2047, 2048):
            check_g1_preflight_annex(RAW.ljust(size))
        with self.assertRaisesRegex(EvidenceError, 'byte limit'):
            check_g1_preflight_annex(RAW.ljust(2049))
        with self.assertRaisesRegex(EvidenceError, 'byte limit'):
            check_g1_preflight_annex(b'!' * 2049)
        with self.assertRaisesRegex(EvidenceError, 'raw UTF-8 JSON bytes required'):
            check_g1_preflight_annex(None)

    def test_alternative_encoding_keeps_its_own_digest(self):
        reordered = json.dumps(SAMPLE, separators=(',', ':'), sort_keys=True).encode()
        self.assertEqual(json.loads(reordered), SAMPLE)
        self.assertNotEqual(sha256(reordered).digest(), sha256(RAW).digest())
        check_g1_preflight_annex(reordered)
