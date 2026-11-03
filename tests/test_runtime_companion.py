"""Offline schema conformance only, never companion admission or authentication."""
import copy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource, Unresolvable

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'schemas/runtime/v1'
NAMES = ('companion', 'instance', 'host-snapshot')
FIXTURES = ROOT / 'fixtures/runtime/v1/companion'
BASE = 'https://local-connect.invalid/schemas/runtime/v1/'
MAX = 9007199254740991
SCHEMA_NAMES = tuple(n + '.schema.json' for n in (*NAMES, 'qualification'))
# Fixed file selection, never fixture-controlled paths or URLs.
CASES = {
    **{'instance-' + p + '-' + b + '.json': 'instance.schema.json'
       for p in ('linux', 'windows') for b in ('cuda', 'vulkan')},
    **{'snapshot-' + p + '-' + b + '.json': 'host-snapshot.schema.json'
       for p in ('linux', 'windows') for b in ('cuda', 'vulkan')},
    **{'snapshot-unavailable-' + b + '.json': 'host-snapshot.schema.json'
       for b in ('cuda', 'vulkan')},
    **{n + '.json': 'companion.schema.json' for n in (
        'manifest-empty', 'manifest-sources', 'manifest-invalid-bytes',
        'manifest-semantic-mismatch')},
    **{n + '.json': 'instance.schema.json' for n in (
        'instance-invalid-pair', 'instance-invalid-process', 'instance-semantic-overflow')},
    **{n + '.json': 'host-snapshot.schema.json' for n in (
        'snapshot-invalid-placeholder', 'snapshot-invalid-device', 'snapshot-semantic-reversed')},
}


def fixture(name):
    if name not in CASES:
        raise ValueError('fixture is not in the fixed allowlist')
    return json.loads((FIXTURES / name).read_bytes())


def documents():
    return {BASE + name: json.loads((SCHEMAS / name).read_bytes()) for name in SCHEMA_NAMES}


def no_retrieval(uri):
    raise NoSuchResource(ref=uri)


def registry(docs):
    return Registry(retrieve=no_retrieval).with_resources(
        (uri, Resource.from_contents(value)) for uri, value in docs.items())


def validator(name, docs=None):
    if name not in SCHEMA_NAMES:
        raise ValueError('schema is not in the fixed allowlist')
    docs = documents() if docs is None else docs
    return Draft202012Validator(docs[BASE + name], registry=registry(docs))


def nodes(value, path=()):
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from nodes(child, (*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from nodes(child, (*path, index))


def at(value, path):
    for key in path:
        value = value[key]
    return value


def replace(value, path, item):
    value = copy.deepcopy(value)
    at(value, path[:-1])[path[-1]] = item
    return value


def error_details(errors):
    for error in errors:
        yield tuple(error.absolute_path), error.validator
        yield from error_details(error.context)


def positive_cases():
    for name, schema in CASES.items():
        if '-invalid-' not in name and '-semantic-' not in name:
            yield schema, fixture(name)


class CompanionSchemaTests(unittest.TestCase):
    def assert_valid(self, schema, value, docs=None):
        self.assertEqual(list(validator(schema, docs).iter_errors(value)), [])

    def assert_rejected(self, schema, value, path, keyword, docs=None):
        errors = list(validator(schema, docs).iter_errors(value))
        self.assertTrue(errors, 'missing direct schema rejection')
        self.assertIn((tuple(path), keyword), set(error_details(errors)))

    def test_canonical_schema_files_exist(self):
        for name in NAMES:
            with self.subTest(schema=name):
                self.assertTrue((SCHEMAS / (name + '.schema.json')).is_file(),
                                'canonical companion schema is absent: ' + name)

    def test_meta_schema_and_every_reference_resolves_offline(self):
        docs = documents()
        reg = registry(docs)
        for uri, value in docs.items():
            self.assertEqual(value['$id'], uri)
            Draft202012Validator.check_schema(value)
            for _, node in nodes(value):
                if isinstance(node, dict) and '$ref' in node:
                    resolved = reg.resolver(uri).lookup(node['$ref'])
                    self.assertIsInstance(resolved.contents, dict)
                    self.assertIn(urljoin(uri, node['$ref']).split('#')[0], docs)

    def test_missing_reference_fails_without_retrieval(self):
        docs = documents()
        for uri in ('https://local-connect.invalid/unknown.schema.json',
                    'file:///unregistered', BASE + 'qualification.schema.json'):
            with self.subTest(uri=uri):
                partial = {k: v for k, v in docs.items() if k != uri}
                # Exercise the same registry factory as every conformance probe.
                with patch(__name__ + '.no_retrieval', wraps=no_retrieval) as denied:
                    v = Draft202012Validator({'$ref': uri}, registry=registry(partial))
                    with self.assertRaises(Unresolvable):
                        list(v.iter_errors({}))
                    denied.assert_called_once_with(uri)

    def test_frozen_fixture_inventory_and_exact_rejection(self):
        cases = json.loads((FIXTURES / 'index.json').read_bytes())
        self.assertEqual(len(cases), len(CASES))
        self.assertEqual({c['fixture'] for c in cases}, set(CASES))
        self.assertEqual({p.name for p in FIXTURES.glob('*.json')}, {*CASES, 'index.json'})
        for case in cases:
            name = case['fixture']
            with self.subTest(fixture=name):
                schema = CASES[name]
                self.assertEqual(schema, case['schema'])
                raw = (FIXTURES / name).read_bytes()
                self.assertEqual(sha256(raw).hexdigest(), case['sha256'])
                self.assertIs(type(case['valid']), bool)
                self.assertTrue(case['constraint'])
                value = json.loads(raw)
                if case['valid']:
                    self.assert_valid(schema, value)
                else:
                    self.assert_rejected(schema, value, case['error']['path'], case['error']['keyword'])

    def test_every_object_closed_every_member_required_and_types(self):
        for schema, base in positive_cases():
            self.assert_valid(schema, base)
            for path, obj in nodes(base):
                if not isinstance(obj, dict):
                    continue
                with self.subTest(schema=schema, path=path):
                    extra = copy.deepcopy(base)
                    at(extra, path)['unexpected'] = 'forbidden'
                    self.assert_rejected(schema, extra, path, 'additionalProperties')
                    for key in obj:
                        absent = copy.deepcopy(base)
                        del at(absent, path)[key]
                        self.assert_rejected(schema, absent, path, 'required')
                    for wrong in (None, False, '', 0, []):
                        changed = replace(base, path, wrong) if path else wrong
                        self.assert_rejected(schema, changed, path, 'type')

    def test_versions_pairings_and_platform_process_fields(self):
        for schema, base in positive_cases():
            version = {'companion.schema.json': 'companion_version',
                       'instance.schema.json': 'instance_version',
                       'host-snapshot.schema.json': 'snapshot_version'}[schema]
            for bad in (0, 2, '', False, None, '1'):
                self.assert_rejected(schema, dict(base, **{version: bad}), [version],
                                     'const' if type(bad) is int else 'type')
        for platform in ('linux', 'windows'):
            for backend in ('cuda', 'vulkan'):
                v = fixture('instance-' + platform + '-' + backend + '.json')
                for field, bad in [('backend', 'vulkan' if backend == 'cuda' else 'cuda'),
                                   ('tier', 'gpu-vulkan' if backend == 'cuda' else 'gpu-cuda')]:
                    self.assert_rejected('instance.schema.json', dict(v, **{field: bad}), [field], 'const')
                for field in ('platform', 'backend', 'tier'):
                    for bad in ('unknown', '', False, None):
                        self.assert_rejected('instance.schema.json', dict(v, **{field: bad}), [field], 'enum')
                for process in ('host', 'server'):
                    wrong = copy.deepcopy(v)
                    foreign = 'creation_filetime' if platform == 'linux' else 'boot_id'
                    wrong[process][foreign] = '1'
                    self.assert_rejected('instance.schema.json', wrong, [process], 'additionalProperties')

    def test_every_scalar_rejects_wrong_types_at_its_field(self):
        for schema, base in positive_cases():
            for path, value in nodes(base):
                if isinstance(value, (dict, list)):
                    continue
                bad_values = (None, False, 0, [], {}) if isinstance(value, str) else (None, '', [], {})
                if type(value) is int:
                    bad_values = (*bad_values, False, 1.5)
                if type(value) is bool:
                    bad_values = (*bad_values, 0, 1, 'false')
                for wrong in bad_values:
                    with self.subTest(schema=schema, path=path, wrong=wrong):
                        errors = list(validator(schema).iter_errors(replace(base, path, wrong)))
                        self.assertTrue(errors)
                        self.assertTrue(any(p == path for p, _ in error_details(errors)),
                                        'wrong type was not rejected at the changed field')

    def test_process_and_counter_lexical_constraints_at_usage(self):
        for platform in ('linux', 'windows'):
            base = fixture('instance-' + platform + '-cuda.json')
            for process in ('host', 'server'):
                for field in ('pid', 'start_ticks' if platform == 'linux' else 'creation_filetime'):
                    path = [process, field]
                    for value in ('1', '9'*20):
                        self.assert_valid('instance.schema.json', replace(base, path, value))
                    for value in ('', '01', '9'*21, '1\n', ' 1', '١'):
                        self.assertTrue(list(validator('instance.schema.json').iter_errors(replace(base, path, value))))
                    zero = replace(base, path, '0')
                    if field == 'start_ticks':
                        self.assert_valid('instance.schema.json', zero)
                    else:
                        self.assert_rejected('instance.schema.json', zero, path, 'not')
        base = fixture('snapshot-linux-cuda.json')
        for field in ('start', 'end'):
            for value in ('0', '1', '9'*20):
                self.assert_valid('host-snapshot.schema.json', replace(base, ['capture_window', field], value))
            for value in ('', '-1', '01', '9'*21, '1\n'):
                self.assertTrue(list(validator('host-snapshot.schema.json').iter_errors(replace(base, ['capture_window', field], value))))

    def test_observation_reuse_keeps_original_meaning(self):
        for backend in ('cuda', 'vulkan'):
            prior = json.loads((FIXTURES.parent / 'qualification' / (backend + '-complete.json')).read_bytes())
            for platform in ('linux', 'windows'):
                new = fixture('snapshot-' + platform + '-' + backend + '.json')
                for group in ('device', 'effective_settings', 'concurrency'):
                    for field, value in prior[group].items():
                        if field not in ('prompt_cache_reuse', 'requests_overlap'):
                            self.assertEqual(new[group][field], value)
            incomplete = json.loads((FIXTURES.parent / 'qualification' / (backend + '-incomplete.json')).read_bytes())
            snapshot = fixture('snapshot-linux-' + backend + '.json')
            reused = 0
            for group in ('device', 'effective_settings', 'concurrency'):
                for field, value in incomplete[group].items():
                    if value['state'] == 'unavailable' and field not in ('prompt_cache_reuse', 'requests_overlap'):
                        reused += 1
                        self.assert_valid('host-snapshot.schema.json', replace(snapshot, [group, field], value))
            self.assertGreater(reused, 0)

    def test_declared_size_sequence_and_source_count_boundaries(self):
        v = fixture('manifest-empty.json')
        for name, cap in [('instance', 16384), ('snapshot', 65536), ('bindings', 262144)]:
            for n in (1, cap - 1, cap):
                self.assert_valid('companion.schema.json', replace(v, [name, 'bytes'], n))
            for n, keyword in [(-1, 'minimum'), (0, 'minimum'), (cap + 1, 'maximum'),
                               ('', 'type'), (False, 'type'), (None, 'type'), (1.5, 'type')]:
                self.assert_rejected('companion.schema.json', replace(v, [name, 'bytes'], n),
                                     [name, 'bytes'], keyword)
        for schema, base in [('companion.schema.json', v),
                             ('host-snapshot.schema.json', fixture('snapshot-linux-cuda.json'))]:
            for n in (1, MAX - 1, MAX):
                self.assert_valid(schema, dict(base, sequence=n))
            for n, keyword in [(0, 'minimum'), (-1, 'minimum'), (MAX + 1, 'maximum'),
                               ('', 'type'), (False, 'type'), (None, 'type')]:
                self.assert_rejected(schema, dict(base, sequence=n), ['sequence'], keyword)
        item = fixture('manifest-sources.json')['sources'][0]
        for count in (0, 1, 31, 32):
            self.assert_valid('companion.schema.json', dict(v, sources=[dict(item, alias='s'+str(i)) for i in range(count)]))
        self.assert_rejected('companion.schema.json', dict(v, sources=[item]*33), ['sources'], 'maxItems')
        for bad in (False, None, '', {}):
            self.assert_rejected('companion.schema.json', dict(v, sources=bad), ['sources'], 'type')
        mixed = fixture('manifest-sources.json')
        for n in (1, 262143, 262144):
            self.assert_valid('companion.schema.json', replace(mixed, ['sources', 1, 'object', 'bytes'], n))
        for n, keyword in [(0, 'minimum'), (262145, 'maximum'), (False, 'type'), ('', 'type'), (None, 'type')]:
            self.assert_rejected('companion.schema.json', replace(mixed, ['sources', 1, 'object', 'bytes'], n),
                                 ['sources', 1, 'object', 'bytes'], keyword)
        self.assert_rejected('companion.schema.json', replace(mixed, ['sources', 1, 'kind'], 'request'),
                             ['sources', 1, 'kind'], 'enum')

    def test_lexical_definitions_and_u64_proof_boundary(self):
        docs = documents()
        reg = registry(docs)
        vectors = {
            'qualification.schema.json#/$defs/sha256':
                (['a'*64], ['', 'a'*63, 'a'*65, 'A'*64, 'g'*64, 'a'*64+'\n', False, None]),
            'qualification.schema.json#/$defs/alias':
                (['a', 'a'*128, 'a.b_c-0'], ['', 'a'*129, 'A', '../x', 'a/b', 'a\n', 'a ', False, None]),
            'instance.schema.json#/$defs/u64_text':
                (['0', '1', '9'*19, '18446744073709551615', '18446744073709551616'],
                 ['', '00', '01', '-1', '+1', '1.0', '1e1', ' 1', '1 ', '1\n', '١', '9'*21, False, None, 1]),
            'instance.schema.json#/$defs/positive_u64_text':
                (['1', '18446744073709551615'], ['0', '', '01', False, None, 1]),
            'instance.schema.json#/$defs/uuid':
                (['12345678-1234-1234-abcd-123456789abc'],
                 ['', '12345678-1234-1234-ABCD-123456789ABC', '1'*36, '12345678-1234-1234-abcd-123456789abc\n', False]),
            'instance.schema.json#/$defs/uuid_v4':
                (['12345678-1234-4234-abcd-123456789abc'],
                 ['12345678-1234-1234-abcd-123456789abc', '12345678-1234-4234-7bcd-123456789abc', '', None]),
        }
        for reference, (good, bad) in vectors.items():
            v = Draft202012Validator({'$ref': BASE + reference}, registry=reg)
            for value in good:
                with self.subTest(reference=reference, value=value):
                    self.assertEqual(list(v.iter_errors(value)), [])
            for value in bad:
                with self.subTest(reference=reference, value=value):
                    self.assertTrue(list(v.iter_errors(value)))
        instance = fixture('instance-linux-cuda.json')
        for value in ('b'*39, 'b'*41, 'B'*40, 'b'*40+'\n', '', False):
            self.assertTrue(list(validator('instance.schema.json').iter_errors(dict(instance, build_commit=value))))

    def test_host_placeholders_and_all_other_unavailable_alternatives(self):
        for backend in ('cuda', 'vulkan'):
            base = fixture('snapshot-linux-'+backend+'.json')
            frozen = copy.deepcopy(base)
            for group in ('device', 'effective_settings', 'concurrency'):
                for field, observation in base[group].items():
                    path = [group, field]
                    host_placeholder = field in ('prompt_cache_reuse', 'requests_overlap')
                    for reason in ('not_collected', 'not_reported', 'source_error'):
                        value = {'state': 'unavailable', 'reason': reason}
                        new = replace(base, path, value)
                        if host_placeholder and reason != 'not_collected':
                            self.assert_rejected('host-snapshot.schema.json', new, path, 'const')
                        else:
                            self.assert_valid('host-snapshot.schema.json', new)
                    for invalid in ({'reason': 'not_collected'}, {'state': 'unavailable'},
                                    {'state': 'unavailable', 'reason': ''},
                                    {'state': 'unavailable', 'reason': 'not_collected', 'value': 0},
                                    {'state': 'unavailable', 'reason': 'not_collected', 'source': {}}):
                        self.assertTrue(list(validator('host-snapshot.schema.json').iter_errors(replace(base, path, invalid))))
                    if host_placeholder:
                        for boolean in (False, True):
                            source = dict(base['effective_settings']['slots']['source'],
                                          kind='request' if field == 'prompt_cache_reuse' else 'workload')
                            new = replace(base, path, {'state': 'observed', 'value': boolean, 'source': source})
                            self.assert_rejected('host-snapshot.schema.json', new, path, 'const')
                    elif observation['state'] == 'observed':
                        for kind in ('device', 'server', 'request', 'workload'):
                            new = replace(base, [*path, 'source', 'kind'], kind)
                            if kind == observation['source']['kind']:
                                self.assert_valid('host-snapshot.schema.json', new)
                            else:
                                self.assert_rejected('host-snapshot.schema.json', new, [*path, 'source', 'kind'], 'const')
            self.assertEqual(base, frozen)
            for field in ('context_checkpoints', 'offloaded_layers'):
                self.assert_valid('host-snapshot.schema.json', replace(base, ['effective_settings', field, 'value'], 0))
            self.assert_valid('host-snapshot.schema.json', replace(base, ['effective_settings', 'flash_attention', 'value'], False))

    def test_shape_valid_counterexamples_are_not_bundle_admission(self):
        for name in ('instance-semantic-overflow.json', 'manifest-semantic-mismatch.json', 'snapshot-semantic-reversed.json'):
            self.assert_valid(CASES[name], fixture(name))
        v = fixture('manifest-sources.json')
        v['sources'][1]['alias'] = v['sources'][0]['alias']
        self.assert_valid('companion.schema.json', v)  # uniqueness by alias is semantic
        v = fixture('snapshot-linux-cuda.json')
        v['capture_window']['clock'] = 'windows-uptime-ms'
        self.assert_valid('host-snapshot.schema.json', v)  # no independent instance here
        v['capture_window']['clock'] = 'wall-clock'
        self.assert_rejected('host-snapshot.schema.json', v, ['capture_window', 'clock'], 'enum')

    def test_inventory_owner_rejects_unlisted_and_duplicate_fixture(self):
        from tests import test_runtime_contracts as owner
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / 'runtime'
            shutil.copytree(owner.FIXTURES, target)
            case = owner.RuntimeContractTests('test_fixture_inventory_is_complete')
            with patch.object(owner, 'FIXTURES', target):
                case.test_fixture_inventory_is_complete()
                extra = target / 'companion/unlisted.json'
                extra.write_text('{}\n')
                with self.assertRaisesRegex(AssertionError, 'companion/unlisted.json'):
                    case.test_fixture_inventory_is_complete()
                extra.unlink()
                p = target / 'companion/index.json'
                rows = json.loads(p.read_bytes())
                p.write_text(json.dumps(rows + [rows[0]]))
                with self.assertRaises(AssertionError):
                    case.test_fixture_inventory_is_complete()

    def test_direct_schema_probes_kill_guard_mutations(self):
        manifest = fixture('manifest-empty.json')
        pair = fixture('instance-linux-cuda.json')
        placeholder = fixture('snapshot-linux-cuda.json')
        source = dict(placeholder['effective_settings']['slots']['source'], kind='request')
        placeholder['effective_settings']['prompt_cache_reuse'] = {'state': 'observed', 'value': False, 'source': source}
        bad_missing = dict(manifest)
        del bad_missing['sequence']
        probes = [
            ('companion.schema.json', bad_missing, [], 'required',
             lambda d: d['required'].remove('sequence')),
            ('companion.schema.json', dict(manifest, unexpected=True), [], 'additionalProperties',
             lambda d: d.pop('additionalProperties')),
            ('companion.schema.json', dict(manifest, sources=[fixture('manifest-sources.json')['sources'][0]]*33), ['sources'], 'maxItems',
             lambda d: d['properties']['sources'].pop('maxItems')),
            ('companion.schema.json', replace(manifest, ['instance', 'bytes'], 16385), ['instance', 'bytes'], 'maximum',
             lambda d: d['properties']['instance']['allOf'][1]['properties']['bytes'].pop('maximum')),
            ('instance.schema.json', dict(pair, backend='vulkan'), ['backend'], 'const',
             lambda d: d['allOf'].pop(0)),
            ('host-snapshot.schema.json', placeholder, ['effective_settings', 'prompt_cache_reuse'], 'const',
             lambda d: d['properties']['effective_settings']['allOf'].pop(1)),
        ]
        for schema, bad, path, keyword, mutate in probes:
            with self.subTest(schema=schema, keyword=keyword):
                self.assert_rejected(schema, bad, path, keyword)
                docs = documents()
                mutate(docs[BASE + schema])
                # Prove this direct assertion fails when its owning guard is removed.
                with self.assertRaisesRegex(AssertionError, 'missing direct schema rejection'):
                    self.assert_rejected(schema, bad, path, keyword, docs)


if __name__ == '__main__':
    unittest.main()
