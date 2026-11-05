"""Offline formats and bounded test ingestion, NOT final record binding/authority.

The pair runner is test-only. Existing numeric ingestion is reused unchanged;
no runtime rules, temporal comparisons, provenance or client API are implemented.
"""
import copy
from hashlib import sha256
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource, Unresolvable

from tests.runtime_qualification import _parse, EvidenceError, DuplicateMember
from tests.test_runtime_companion import nodes, replace, error_details

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'schemas/runtime/v1'
FIXTURES = ROOT / 'fixtures/runtime/v1/record-binding'
BASE = 'https://local-connect.invalid/schemas/runtime/v1/'
NAMES = ('app-bindings', 'observation-scope')
SCHEMA_NAMES = tuple(n + '.schema.json' for n in (*NAMES, 'qualification', 'instance'))
METADATA_BYTES = 256 * 1024
MAX_DEPTH = 32
CASES = {
    **{name + '.json': 'app-bindings.schema.json' for name in (
        'app-empty', 'app-paired', 'app-invalid-kind', 'app-invalid-indices',
        'app-semantic-alias', 'app-semantic-indices', 'app-semantic-source-field')},
    **{name + '.json': 'observation-scope.schema.json' for name in (
        'scope-empty', 'scope-linux-cuda', 'scope-windows-vulkan',
        'scope-invalid-field', 'scope-invalid-time', 'scope-semantic-reversed',
        'scope-semantic-overflow', 'scope-semantic-field', 'scope-semantic-backend')},
}


def documents():
    return {BASE + n: json.loads((SCHEMAS / n).read_bytes()) for n in SCHEMA_NAMES}


def no_retrieval(uri):
    raise NoSuchResource(ref=uri)


def registry(docs):
    return Registry(retrieve=no_retrieval).with_resources(
        (uri, Resource.from_contents(value)) for uri, value in docs.items())


def validator(name, docs=None):
    if name not in SCHEMA_NAMES:
        raise ValueError('schema outside fixed registry')
    docs = documents() if docs is None else docs
    return Draft202012Validator(docs[BASE + name], registry=registry(docs))


def raw_fixture(name):
    if name not in CASES:
        raise ValueError('fixture outside fixed inventory')
    return (FIXTURES / name).read_bytes()


def fixture(name):
    return _parse(raw_fixture(name))


def parse_metadata(raw):
    """Test ingestion: byte cap before shared parser; iterative tree depth check.

    This is not the later client's during-descent depth/memory proof. The shared
    Python parser is unchanged; its recursion errors remain EvidenceError.
    """
    if not isinstance(raw, bytes):
        raise EvidenceError('raw bytes required')
    if len(raw) > METADATA_BYTES:
        raise EvidenceError('metadata byte limit')
    value = _parse(raw)
    stack = [(value, 1)]
    while stack:
        node, depth = stack.pop()
        if isinstance(node, (dict, list)):
            if depth > MAX_DEPTH:
                raise EvidenceError('metadata depth limit')
            children = node.values() if isinstance(node, dict) else node
            stack.extend((child, depth + 1) for child in children)
    return value


def inspect_shapes(app_raw, scope_raw):
    """A bounded offline test pair; deliberately no binding or validity checks."""
    if not isinstance(app_raw, bytes) or not isinstance(scope_raw, bytes):
        raise EvidenceError('raw bytes required')
    if len(app_raw) + len(scope_raw) > METADATA_BYTES:
        raise EvidenceError('metadata byte limit')
    values = []
    for name, raw in zip(NAMES, (app_raw, scope_raw)):
        value = parse_metadata(raw)
        if not validator(name + '.schema.json').is_valid(value):
            raise EvidenceError('metadata shape invalid')
        values.append(value)
    return tuple(values)


def positive_cases():
    for name in ('app-empty', 'app-paired', 'scope-empty',
                 'scope-linux-cuda', 'scope-windows-vulkan'):
        yield CASES[name + '.json'], fixture(name + '.json')


class RecordBindingSchemaTests(unittest.TestCase):
    def assert_valid(self, name, value, docs=None):
        self.assertEqual(list(validator(name, docs).iter_errors(value)), [])

    def assert_rejected(self, name, value, path, keyword, docs=None):
        errors = list(validator(name, docs).iter_errors(value))
        self.assertTrue(errors, 'missing schema rejection')
        self.assertIn((tuple(path), keyword), set(error_details(errors)))

    def test_duplicate_field_fixtures_fail_shape(self):
        for name, collection in (
                ('app-semantic-source-field.json', 'sources'),
                ('scope-semantic-field.json', 'requirements')):
            with self.subTest(fixture=name):
                self.assert_rejected(CASES[name], fixture(name), [collection], 'maxContains')

    def field_collection_cases(self):
        app = fixture('app-paired.json')
        yield 'app-bindings.schema.json', app, 'sources', app['sources']
        scope = fixture('scope-linux-cuda.json')
        fields = documents()[BASE + 'observation-scope.schema.json'][
            '$defs']['requirement']['properties']['field']['enum']
        entries = [dict(scope['requirements'][0], field=field,
                        interval={'start': '0', 'end': '0'}, rule=None)
                   for field in fields]
        yield 'observation-scope.schema.json', scope, 'requirements', entries

    def test_field_uniqueness_accepts_empty_partial_and_all_distinct(self):
        for name, base, collection, entries in self.field_collection_cases():
            for size in (0, 1, len(entries)-1, len(entries)):
                with self.subTest(schema=name, size=size):
                    self.assert_valid(name, dict(base, **{collection: entries[:size]}))
            # Every individual field remains optional; no implicit contains minimum.
            for entry in entries:
                with self.subTest(schema=name, field=entry['field']):
                    self.assert_valid(name, dict(base, **{collection: [entry]}))

    def test_each_field_rejects_identical_and_different_duplicates(self):
        for name, base, collection, entries in self.field_collection_cases():
            for entry in entries:
                changed = copy.deepcopy(entry)
                if collection == 'sources':
                    changed['artifact']['alias'] = 'different-source'
                else:
                    changed['interval']['end'] = '1'
                self.assertNotEqual(entry, changed)
                other = next(e for e in entries if e['field'] != entry['field'])
                for duplicate in (entry, changed):
                    # Two entries stay within maxItems, isolating the field guard.
                    wrong = dict(base, **{collection: [entry, duplicate]})
                    with self.subTest(schema=name, field=entry['field'], duplicate=duplicate):
                        errors = list(validator(name).iter_errors(wrong))
                        self.assertEqual(set(error_details(errors)), {((collection,), 'maxContains')})
                        mixed = dict(base, **{collection: [other, entry, duplicate]})
                        self.assert_rejected(name, mixed, [collection], 'maxContains')
                        # App's mixed triple also exceeds maxItems=2; scope does not.
                        self.assert_rejected(name, dict(base, **{collection: [entry]*3}),
                                             [collection], 'maxContains')

    def test_each_field_guard_removal_and_optional_minimum_mutations(self):
        for name, base, collection, entries in self.field_collection_cases():
            original = documents()
            guards = original[BASE + name]['properties'][collection]['allOf']
            self.assertEqual(len(guards), len(entries))
            self.assertEqual({g['contains']['properties']['field']['const'] for g in guards},
                             {e['field'] for e in entries})
            for i, guard in enumerate(guards):
                field = guard['contains']['properties']['field']['const']
                entry = next(e for e in entries if e['field'] == field)
                other = next(e for e in entries if e['field'] != field)
                duplicate = dict(base, **{collection: [entry, entry]})
                with self.subTest(schema=name, field=field):
                    self.assert_rejected(name, duplicate, [collection], 'maxContains')
                    weakened = copy.deepcopy(original)
                    del weakened[BASE + name]['properties'][collection]['allOf'][i]['maxContains']
                    self.assert_valid(name, duplicate, weakened)
                    too_strict = copy.deepcopy(original)
                    del too_strict[BASE + name]['properties'][collection]['allOf'][i]['minContains']
                    for allowed in ([], [other]):
                        value = dict(base, **{collection: allowed})
                        self.assert_valid(name, value)
                        self.assert_rejected(name, value, [collection], 'contains', too_strict)

    def test_duplicate_fields_reach_existing_shape_error_boundary(self):
        app, scope = raw_fixture('app-empty.json'), raw_fixture('scope-empty.json')
        for a, s in ((raw_fixture('app-semantic-source-field.json'), scope),
                     (app, raw_fixture('scope-semantic-field.json'))):
            with self.subTest(app_sha=sha256(a).hexdigest(), scope_sha=sha256(s).hexdigest()):
                with self.assertRaisesRegex(EvidenceError, '^metadata shape invalid$'):
                    inspect_shapes(a, s)
        # The test-only runner has no Rust Malformed type or record-binding API.
        # It must reject through its existing schema-error path, not a new scanner.

    def test_canonical_schema_files_exist(self):
        for name in NAMES:
            with self.subTest(schema=name):
                self.assertTrue((SCHEMAS / (name + '.schema.json')).is_file(),
                                'contracted schema is absent: ' + name)

    def test_meta_schema_reference_closure_and_fixed_registry(self):
        docs = documents()
        reg = registry(docs)
        for uri, value in docs.items():
            self.assertEqual(value['$id'], uri)
            Draft202012Validator.check_schema(value)
            for _, node in nodes(value):
                if isinstance(node, dict) and '$ref' in node:
                    self.assertIn(urljoin(uri, node['$ref']).split('#')[0], docs)
                    self.assertIsInstance(reg.resolver(uri).lookup(node['$ref']).contents, dict)
        for bad in ('../qualification.schema.json', '', 'https://example.invalid/schema'):
            with self.assertRaisesRegex(ValueError, 'fixed registry'):
                validator(bad)
        for uri in ('https://example.invalid/schema', 'file:///unknown',
                    BASE + 'qualification.schema.json', BASE + 'instance.schema.json'):
            with self.subTest(uri=uri):
                partial = {k: v for k, v in docs.items() if k != uri}
                with patch(__name__ + '.no_retrieval', wraps=no_retrieval) as denied:
                    v = Draft202012Validator({'$ref': uri}, registry=registry(partial))
                    with self.assertRaises(Unresolvable):
                        list(v.iter_errors({}))
                    denied.assert_called_once_with(uri)

    def test_fixture_inventory_hashes_and_exact_shape_outcomes(self):
        cases = _parse((FIXTURES / 'index.json').read_bytes())
        self.assertEqual(len(cases), len(CASES))
        self.assertEqual({c['fixture'] for c in cases}, set(CASES))
        self.assertEqual({p.name for p in FIXTURES.glob('*.json')}, {*CASES, 'index.json'})
        for case in cases:
            with self.subTest(fixture=case['fixture']):
                raw = raw_fixture(case['fixture'])
                self.assertEqual(sha256(raw).hexdigest(), case['sha256'])
                self.assertEqual(case['schema'], CASES[case['fixture']])
                self.assertIs(type(case['valid']), bool)
                self.assertTrue(case['constraint'])
                value = parse_metadata(raw)
                if case['valid']:
                    self.assert_valid(case['schema'], value)
                else:
                    self.assert_rejected(case['schema'], value,
                                         case['error']['path'], case['error']['keyword'])
        with self.assertRaisesRegex(ValueError, 'fixed inventory'):
            raw_fixture('../index.json')

    def test_path_enum_equals_canonical_observation_union(self):
        docs = documents()
        defs = docs[BASE + 'qualification.schema.json']['$defs']
        expected = {group + '.' + key
                    for name, group in (('cuda_device', 'device'), ('vulkan_device', 'device'),
                                        ('settings', 'effective_settings'), ('concurrency', 'concurrency'))
                    for key in defs[name]['properties']}
        scope = docs[BASE + 'observation-scope.schema.json']
        actual = scope['$defs']['requirement']['properties']['field']['enum']
        self.assertEqual(set(actual), expected)
        self.assertEqual(len(actual), len(expected))
        self.assertEqual(scope['properties']['requirements']['maxItems'], len(expected))
        base = fixture('scope-linux-cuda.json')
        for field in expected:
            v = copy.deepcopy(base)
            v['requirements'] = [dict(v['requirements'][0], field=field)]
            self.assert_valid('observation-scope.schema.json', v)

    def test_all_objects_closed_and_all_members_required(self):
        for name, base in positive_cases():
            for path, node in nodes(base):
                if not isinstance(node, dict):
                    continue
                with self.subTest(schema=name, path=path):
                    wrong = copy.deepcopy(node)
                    wrong['unexpected'] = True
                    value = replace(base, path, wrong) if path else wrong
                    self.assert_rejected(name, value, path, 'additionalProperties')
                    for key in node:
                        wrong = copy.deepcopy(node)
                        del wrong[key]
                        value = replace(base, path, wrong) if path else wrong
                        self.assert_rejected(name, value, path, 'required')

    def test_scalar_types_versions_and_unknown_discriminators(self):
        for name, base in positive_cases():
            for path, value in nodes(base):
                if isinstance(value, (dict, list)) or value is None:
                    continue
                bads = (None, False, 0, [], {}) if isinstance(value, str) else (None, False, '', [], {})
                for bad in bads:
                    with self.subTest(schema=name, path=path, bad=bad):
                        self.assertFalse(validator(name).is_valid(replace(base, path, bad)))
        for name, version, leaf in [('app-bindings', 'app_bindings_version', 'app-empty'),
                                    ('observation-scope', 'observation_scope_version', 'scope-empty')]:
            for bad in (0, 2, -1):
                self.assert_rejected(name + '.schema.json', dict(fixture(leaf + '.json'), **{version: bad}),
                                     [version], 'const')
        scope = fixture('scope-linux-cuda.json')
        for clock in ('', 'wall-clock', False, None):
            self.assert_rejected('observation-scope.schema.json', dict(scope, clock=clock), ['clock'], 'enum')

    def test_source_pairing_both_directions_and_mixed_list(self):
        base = fixture('app-paired.json')
        self.assert_valid('app-bindings.schema.json', base)
        for i in (0, 1):
            wrong = copy.deepcopy(base)
            wrong['sources'][i]['kind'] = base['sources'][1-i]['kind']
            self.assert_rejected('app-bindings.schema.json', wrong, ['sources', i, 'kind'], 'const')
            wrong = copy.deepcopy(base)
            wrong['sources'][i]['field'] = 'effective_settings.slots'
            self.assert_rejected('app-bindings.schema.json', wrong, ['sources', i, 'field'], 'const')

    def test_array_count_and_index_boundaries(self):
        app = fixture('app-paired.json')
        for count in (0, 1, 2):
            self.assert_valid('app-bindings.schema.json', dict(app, sources=app['sources'][:count]))
        self.assert_rejected('app-bindings.schema.json', dict(app, sources=app['sources'] + [app['sources'][0]]),
                             ['sources'], 'maxItems')
        for indices, keyword in [([], 'minItems'), ([0, 0], 'uniqueItems'), ([-1], 'minimum'),
                                 ([9007199254740992], 'maximum'), ([False], 'type')]:
            self.assert_rejected('app-bindings.schema.json',
                                 replace(app, ('sources', 0, 'request_indices'), indices),
                                 ['sources', 0, 'request_indices'] + ([0] if keyword in ('minimum', 'maximum', 'type') else []), keyword)
        for indices in ([0], [0, 1], [9007199254740991]):
            self.assert_valid('app-bindings.schema.json', replace(app, ('sources', 0, 'request_indices'), indices))
        scope = fixture('scope-linux-cuda.json')
        paths = documents()[BASE + 'observation-scope.schema.json']['$defs']['requirement']['properties']['field']['enum']
        entries = [dict(scope['requirements'][0], field=p) for p in paths]
        for n in (0, 1, len(paths)-1, len(paths)):
            self.assert_valid('observation-scope.schema.json', dict(scope, requirements=entries[:n]))
        self.assert_rejected('observation-scope.schema.json', dict(scope, requirements=entries + [entries[0]]),
                             ['requirements'], 'maxItems')
        self.assert_valid('app-bindings.schema.json', dict(app, requests=[
            dict(app['requests'][0], alias='offer-' + str(i)) for i in range(200)]))

    def test_digest_and_alias_bounds_at_every_populated_reference(self):
        # One lexical boundary set covers direct digests and nested Artifact/rule
        # references in both formats, including every array occurrence.
        boundaries = {
            'digest': (('0' * 64, 'f' * 64), (
                ('', 'minLength'), ('a' * 63, 'minLength'),
                ('a' * 65, 'maxLength'), ('A' * 64, 'pattern'),
                ('g' * 64, 'pattern'))),
            'alias': (('a', 'a' * 128), (
                ('', 'minLength'), ('a' * 129, 'maxLength'),
                ('../x', 'pattern'), ('a\n', 'pattern'))),
        }
        fields = {
            'instance_id': 'digest', 'app_bindings_sha256': 'digest',
            'bundle_manifest_sha256': 'digest', 'ruleset_sha256': 'digest',
            'sha256': 'digest', 'alias': 'alias', 'rule_id': 'alias',
        }
        covered = set()
        for name, base in positive_cases():
            for path, value in nodes(base):
                if not path or path[-1] not in fields:
                    continue
                covered.add(path[-1])
                self.assertIsInstance(value, str)
                good, bad = boundaries[fields[path[-1]]]
                for valid in good:
                    with self.subTest(schema=name, path=path, valid=valid):
                        self.assert_valid(name, replace(base, path, valid))
                for invalid, keyword in bad:
                    with self.subTest(schema=name, path=path, invalid=invalid):
                        self.assert_rejected(name, replace(base, path, invalid), path, keyword)
        self.assertEqual(covered, set(fields))

    def test_u64text_boundaries(self):
        scope = fixture('scope-linux-cuda.json')
        for key in ('start', 'end'):
            path = ('requirements', 0, 'interval', key)
            for v in ('0', '1', '18446744073709551615', '18446744073709551616'):
                self.assert_valid('observation-scope.schema.json', replace(scope, path, v))
            for v in ('', '01', '-1', '+1', '1.0', '1e1', '1\n', '9'*21, 1, False):
                self.assertFalse(validator('observation-scope.schema.json').is_valid(replace(scope, path, v)))

    def test_nullable_references_are_not_authority(self):
        scope = fixture('scope-windows-vulkan.json')
        for path in [('clock_binding',), ('requirements', 1, 'rule')]:
            self.assert_valid('observation-scope.schema.json', replace(scope, path, None))
            for bad in (False, 0, '', [], {}):
                self.assertFalse(validator('observation-scope.schema.json').is_valid(replace(scope, path, bad)))
        for field in ('approved', 'expression', 'coverage', 'lifetime_invariant'):
            rule = dict(scope['requirements'][1]['rule'], **{field: True})
            self.assert_rejected('observation-scope.schema.json', replace(scope, ('requirements', 1, 'rule'), rule),
                                 ['requirements', 1, 'rule'], 'additionalProperties')

    def test_shared_raw_parser_refuses_rounding_duplicates_and_bad_bytes(self):
        scope = raw_fixture('scope-empty.json')
        app = raw_fixture('app-empty.json')
        for token in (b'1.0', b'1e0', b'-0', b'NaN', b'Infinity', b'18446744073709551616'):
            raw = app.replace(b'"app_bindings_version": 1', b'"app_bindings_version": ' + token)
            with self.subTest(token=token), self.assertRaises(EvidenceError):
                inspect_shapes(raw, scope)
        for raw in (b'\xff', b'\xef\xbb\xbf'+app, app+b'false', b''):
            with self.assertRaises(EvidenceError):
                inspect_shapes(raw, scope)
        with self.assertRaises(DuplicateMember):
            inspect_shapes(app.replace(b'"app_bindings_version": 1', b'"app_bindings_version": 1, "app_bindings_version": 1'), scope)
        for bad in (None, False, '', 0):
            with self.assertRaisesRegex(EvidenceError, 'raw bytes required'):
                inspect_shapes(bad, scope)
            with self.assertRaisesRegex(EvidenceError, 'raw bytes required'):
                inspect_shapes(app, bad)

    def test_combined_budget_before_parser_and_each_document(self):
        app, scope = raw_fixture('app-empty.json'), raw_fixture('scope-empty.json')
        for left, right in ((app, scope), (scope, app)):
            padding = METADATA_BYTES - len(left) - len(right)
            a = left + b' ' * (padding // 2)
            b = right + b' ' * (padding - padding // 2)
            pair = (a, b) if left is app else (b, a)
            for delta in (-1, 0):
                self.assertEqual(inspect_shapes(pair[0], pair[1][:len(pair[1])+delta]),
                                 inspect_shapes(app, scope))
            with patch(__name__ + '._parse', wraps=_parse) as parser:
                with self.assertRaisesRegex(EvidenceError, '^metadata byte limit$'):
                    inspect_shapes(pair[0], pair[1]+b' ')
                parser.assert_not_called()
        for raw in (app, scope):
            capped = raw + b' ' * (METADATA_BYTES - len(raw))
            self.assertEqual(parse_metadata(capped), _parse(raw))
            with patch(__name__ + '._parse', wraps=_parse) as parser:
                with self.assertRaisesRegex(EvidenceError, '^metadata byte limit$'):
                    parse_metadata(capped+b' ')
                parser.assert_not_called()

    def test_tree_depth_boundary_separate_from_schema_shape(self):
        for n in (0, 1, 31, 32):
            raw = b'[' * n + b'0' + b']' * n
            self.assertEqual(parse_metadata(raw), _parse(raw))
        with self.assertRaisesRegex(EvidenceError, '^metadata depth limit$'):
            parse_metadata(b'[' * 33 + b'0' + b']' * 33)

    def test_returned_values_are_parsed_originals_without_reserialization(self):
        app, scope = raw_fixture('app-paired.json'), raw_fixture('scope-windows-vulkan.json')
        with patch(__name__ + '._parse', wraps=_parse) as parser:
            result = inspect_shapes(app, scope)
            self.assertEqual(parser.call_args_list[0].args, (app,))
            self.assertEqual(parser.call_args_list[1].args, (scope,))
        self.assertEqual(result, (_parse(app), _parse(scope)))
        reordered = json.dumps(dict(reversed(list(result[0].items())))).encode()
        self.assertNotEqual(sha256(app).digest(), sha256(reordered).digest())
        self.assertEqual(inspect_shapes(reordered, scope), result)
        wrong = dict(result[0], app_bindings_version=2)
        with self.assertRaisesRegex(EvidenceError, '^metadata shape invalid$'):
            inspect_shapes(json.dumps(wrong).encode(), scope)

    def test_semantic_counterexamples_are_not_misreported_as_shape_failures(self):
        for name in CASES:
            if '-semantic-' in name and name not in (
                    'app-semantic-source-field.json', 'scope-semantic-field.json'):
                self.assert_valid(CASES[name], fixture(name))
        # This runner deliberately cannot authenticate hashes, clock origins,
        # runtime rule IDs, actual backend, interval order, or extraction scores.
        a, s = inspect_shapes(raw_fixture('app-semantic-alias.json'),
                              raw_fixture('scope-semantic-reversed.json'))
        self.assertEqual(a['requests'][0]['alias'], a['requests'][1]['alias'])
        self.assertEqual(s['requirements'][0]['interval'], {'start': '2', 'end': '1'})
