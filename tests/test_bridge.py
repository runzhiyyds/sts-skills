"""Local HTTP protocol fixtures only; no provider, engine worker or paid calls."""

from concurrent.futures import ThreadPoolExecutor
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('sts_bridge', ROOT / 'skills/solve2ship/scripts/sts_bridge.py')
bridge = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(bridge)
TASK, SEARCH, CANDIDATE = 'a' * 32, 'b' * 32, 'c' * 32


class EngineFixture:
    def __init__(self):
        self.requests = []; self.model_available = True; self.model_configured = True; self.limit = 10; self.used = .2
        self.mode = None; self.archive_changed = False; self.drop_start = False
        self.definition = {'title': 'Protocol fixture only', 'samples': [{'text': 'private fixture input'}],
                           'output_specification': 'Return a category.', 'budget': {'mode': 'inherit_work'}}
        self.task = {'task_id': TASK, 'revision': 1, 'content_sha256': 'e' * 64,
                     'contract': {'definition': self.definition, 'dataset': {'sample_count': 1}}}
        self.search = {'id': SEARCH, 'task_id': TASK, 'revision': 1, 'state': 'succeeded', 'error': None,
                       'candidates': [{'id': CANDIDATE, 'family': 'rules.v1', 'name': 'Protocol fixture only'}],
                       'executions': [{'candidate_id': CANDIDATE, 'sample_index': 0, 'output': 'private fixture output',
                                       'error': None, 'label_agreement': 1,
                                       'criteria': {'status': 'checked', 'passed': True}}],
                       'selection': {'candidate_id': CANDIDATE, 'evidence': {'basis': 'provided_label_agreement_unverified', 'final_test_evaluated': False}},
                       'criteria_bundle': {'status': 'proposed', 'schema_sha256': 'd' * 64}, 'delivery_id': 'f' * 32}
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('service/manifest.json', '{"protocol_fixture":true}')
        self.archive = archive.getvalue()
        self.delivery = {'id': 'f' * 32, 'state': 'private_draft_ready', 'report': {'gate_passed': True},
                         'export': {'archive_integrity_verified': True, 'archive_sha256': hashlib.sha256(self.archive).hexdigest()}}
        self.packet = {'subject_kind': 'validation', 'closed': False, 'review_evidence_sha256': 'e' * 64,
                       'summary': {'source': 'self_attested_operator', 'quality_is_verified_accuracy': False},
                       'targets': [{'sample_index': 0, 'input': 'private fixture input', 'output': 'private fixture output'}]}
        fixture = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def reply(self, value, status=200, kind='application/json'):
                body = value if type(value) is bytes else bridge.encode(value)
                self.send_response(status); self.send_header('Content-Type', kind); self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)
            def do_GET(self):
                fixture.requests.append(('GET', self.path, None, dict(self.headers)))
                if self.path == '/api/health':
                    if fixture.mode == 'redirect':
                        self.send_response(302); self.send_header('Location', '/trap'); self.end_headers(); return
                    if fixture.mode == 'html': self.reply(b'<html>not an engine</html>', kind='text/html'); return
                    if fixture.mode == 'oversize': self.reply(b' ' * 200, kind='application/json'); return
                    self.reply({'status': 'ok', 'version': 'fixture', 'candidate_execution_enabled': True, 'arbitrary_code_execution_enabled': False})
                elif self.path == '/api/budget': self.reply({'limit_cny': fixture.limit, 'committed_ceiling_cny': fixture.used})
                elif self.path == '/api/model-status':
                    if not fixture.model_available: self.reply({'error': 'not_found'}, 404)
                    else: self.reply({'configured': fixture.model_configured, 'api_key_configured': fixture.model_configured, 'api_key': 'unit-test-placeholder'})
                elif self.path == '/api/tasks': self.reply({'tasks': [fixture.task]})
                elif self.path in ('/api/tasks/' + TASK, '/api/tasks/' + TASK + '/revisions/1'): self.reply(fixture.task)
                elif self.path == '/api/searches': self.reply({'searches': [fixture.search]})
                elif self.path == '/api/searches/' + SEARCH: self.reply(fixture.search)
                elif self.path.endswith('/delivery/export'):
                    self.reply(fixture.archive + (b'changed' if fixture.archive_changed else b''), kind='application/zip')
                elif self.path.endswith('/delivery'): self.reply({'delivery': fixture.delivery})
                elif self.path.endswith(('/quality-reviews', '/delivery/reviews')): self.reply(fixture.packet)
                else: self.reply({'error': 'not_found'}, 404)
            def do_POST(self):
                body = bridge.decode(self.rfile.read(int(self.headers['Content-Length'])))
                fixture.requests.append(('POST', self.path, body, dict(self.headers)))
                if self.headers.get('X-STS-Request') != '1': self.reply({'error': 'header_required'}, 403); return
                if self.path == '/api/tasks/preview':
                    definition = body['definition']
                    self.reply({'content_sha256': hashlib.sha256(bridge.encode(definition)).hexdigest(), 'contract': {
                        'definition': definition, 'dataset': {'sample_count': len(definition['samples'])}, 'evaluation': {'label_count': 0}}})
                elif self.path == '/api/tasks': self.reply(fixture.task, 201)
                elif self.path == '/api/searches':
                    if fixture.drop_start:
                        self.connection.shutdown(2); self.connection.close(); return
                    self.reply({**fixture.search, 'state': 'queued', 'request_id': body['request_id']}, 201)
                elif self.path.endswith(('/cancel', '/rollback', '/evolve', '/reactivate')): self.reply(fixture.search, 201)
                elif self.path.endswith(('/quality-reviews', '/delivery/reviews')):
                    if fixture.mode == 'stale_review': self.reply({'error': 'review_snapshot_changed'}, 409)
                    else: self.reply(fixture.packet, 201)
                elif self.path.endswith(('/delivery', '/quality-decision')): self.reply(fixture.delivery, 201)
                else: self.reply({'error': 'not_found'}, 404)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True); self.thread.start()
        self.url = 'http://127.0.0.1:' + str(self.server.server_port)

    def close(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.fixture = EngineFixture(); self.addCleanup(self.fixture.close)
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup); self.root = Path(directory.name)
        self.client = bridge.Client(self.fixture.url, timeout=2)
        self.state = self.root / 'private'

    def args(self, *arguments):
        return bridge.parser().parse_args(['--url', self.fixture.url, '--state-dir', str(self.state), *arguments])

    def run_command(self, *arguments):
        return bridge.run(self.args(*arguments), self.client)

    def posts(self, path=None):
        return [r for r in self.fixture.requests if r[0] == 'POST' and (path is None or r[1] == path)]

    def task_file(self):
        path = self.root / 'definition.json'; path.write_bytes(bridge.encode(self.fixture.definition)); return path

    def start(self, operation='explore-one', allow=True):
        return self.run_command('start', '--task-id', TASK, '--revision', '1', '--operation-id', operation, *(['--allow-paid'] if allow else []))

    def test_default_status_and_lists_are_read_only_and_do_not_create_private_state(self):
        facts = self.run_command()
        self.assertEqual(facts['model_configured'], True); self.assertEqual(facts['budget']['committed_ceiling'], .2)
        self.assertNotIn('api_key', facts); self.assertNotIn('unit-test-placeholder', bridge.encode(facts).decode())
        self.assertEqual(self.run_command('tasks')['tasks'][0]['task_id'], TASK)
        self.assertEqual(self.run_command('searches', '--task-id', TASK)['searches'][0]['id'], SEARCH)
        self.assertEqual(self.posts(), []); self.assertFalse(self.state.exists())

    def test_unsafe_destinations_paths_and_redirects_are_refused(self):
        for value in ('https://127.0.0.1:8000', 'http://example.test:80', 'http://127.0.0.1:80/key',
                      'http://user:key@localhost:80', 'http://localhost:80/?key=private', 'http://0.0.0.0:8000'):
            with self.subTest(value=value), self.assertRaises(bridge.BridgeError): bridge.Client(value)
        with self.assertRaises(bridge.BridgeError): self.client.get('/api/tasks/' + TASK + '/../../trap')
        self.fixture.mode = 'redirect'
        with self.assertRaises(bridge.BridgeError): self.run_command()
        self.assertFalse(any(r[1] == '/trap' for r in self.fixture.requests))

    def test_proxy_environment_is_ignored_and_localhost_uses_numeric_loopback(self):
        client = bridge.Client(self.fixture.url.replace('127.0.0.1', 'localhost'), timeout=2)
        with patch.dict(os.environ, {'HTTP_PROXY': 'http://127.0.0.1:1', 'http_proxy': 'http://127.0.0.1:1', 'NO_PROXY': ''}):
            self.assertEqual(bridge.status(client)['status'], 'ok')
        self.assertTrue(client.base_url.startswith('http://127.0.0.1:'))

    def test_malformed_or_oversized_engine_response_is_not_a_success(self):
        self.fixture.mode = 'html'
        with self.assertRaisesRegex(bridge.BridgeError, 'invalid_engine_response'): self.run_command()
        self.fixture.mode = 'oversize'
        with patch.object(bridge, 'MAX_JSON', 100), self.assertRaisesRegex(bridge.BridgeError, 'too_large'): self.run_command()
        with self.assertRaises(bridge.BridgeError): bridge.decode(b'{"key":1,"key":2}')
        with self.assertRaises(bridge.BridgeError): bridge.decode(b'{"key":NaN}')

    def test_start_requires_explicit_paid_command_and_existing_resources(self):
        with self.assertRaisesRegex(bridge.BridgeError, 'explicit_paid'): self.start(allow=False)
        self.fixture.model_configured = False
        with self.assertRaisesRegex(bridge.BridgeError, 'model_configuration'): self.start()
        self.fixture.model_available = False
        self.assertIsNone(self.run_command()['model_configured'])
        with self.assertRaisesRegex(bridge.BridgeError, 'model_status_unavailable'): self.start()
        self.fixture.model_available = self.fixture.model_configured = True; self.fixture.limit = 0; self.fixture.used = 0
        with self.assertRaisesRegex(bridge.BridgeError, 'existing_budget'): self.start()
        self.assertEqual(self.posts(), []); self.assertFalse(self.state.exists())

    def test_reviewed_definition_is_saved_without_starting_a_search_or_budget(self):
        path = self.task_file(); preview = self.run_command('preview', '--definition', str(path))
        self.assertFalse(preview['search_started']); self.assertNotIn('private fixture input', bridge.encode(preview).decode())
        arguments = ('save', '--definition', str(path), '--reviewed-sha256', preview['content_sha256'], '--operation-id', 'save-one')
        result = self.run_command(*arguments); self.assertEqual(result['result']['task_id'], TASK)
        requests = len(self.fixture.requests)
        self.assertEqual(self.run_command(*arguments)['status'], 'cached_submission_receipt')
        self.assertEqual(len(self.fixture.requests), requests)
        self.assertEqual(len(self.posts('/api/tasks')), 1); self.assertEqual(self.posts('/api/searches'), [])
        self.assertEqual(set(self.posts('/api/tasks')[0][2]), {'definition', 'reviewed_sha256'})
        path.write_text('{"title":"changed","samples":[],"output_specification":"other"}')
        with self.assertRaisesRegex(bridge.BridgeError, 'operation_id_conflict'): self.run_command(*arguments)
        self.assertEqual(len(self.fixture.requests), requests)
        with self.assertRaisesRegex(bridge.BridgeError, 'reviewed_task_changed'):
            self.run_command('save', '--definition', str(path), '--reviewed-sha256', preview['content_sha256'], '--operation-id', 'save-changed')

    def test_task_keys_or_credentials_never_reach_the_engine(self):
        path = self.task_file(); path.write_text('{"samples":[{"api_key":"private"}],"output_specification":"example"}')
        with self.assertRaisesRegex(bridge.BridgeError, 'credentials_in_task'): self.run_command('preview', '--definition', str(path))
        self.assertEqual(self.posts(), [])
        path.write_bytes(b' ' * (bridge.MAX_TASK + 1))
        with self.assertRaisesRegex(bridge.BridgeError, 'task_too_large'): self.run_command('preview', '--definition', str(path))

    def test_duplicate_and_concurrent_starts_submit_only_once_and_bind_engine_payload(self):
        def attempt(_):
            try: return self.start()
            except bridge.BridgeError as error: return error.code
        with ThreadPoolExecutor(max_workers=6) as pool: results = list(pool.map(attempt, range(6)))
        self.assertEqual(sum(type(r) is dict and r.get('submitted') is True for r in results), 1)
        self.assertEqual(len(self.posts('/api/searches')), 1)
        cached = self.start(); self.assertFalse(cached['submitted'])
        self.assertEqual(bridge.Journal(self.state).read('explore-one')['state'], 'succeeded')
        with self.assertRaisesRegex(bridge.BridgeError, 'operation_id_conflict'):
            bridge.Journal(self.state).claim('explore-one', 'http://127.0.0.1:1', 'start', {'task_id': TASK, 'revision': 1})
        self.assertEqual((self.state / 'operations.sqlite3').stat().st_mode & 0o777, 0o600)
        self.assertNotIn('private fixture input', (self.state / 'operations.sqlite3').read_bytes().decode(errors='replace'))

    def test_uncertain_submission_is_persisted_across_restart_and_never_automatically_replayed(self):
        self.fixture.drop_start = True
        with self.assertRaises(bridge.BridgeError): self.start()
        receipt = bridge.Journal(self.state).read('explore-one'); self.assertEqual(receipt['state'], 'uncertain')
        self.fixture.drop_start = False; self.fixture.limit = self.fixture.used
        with self.assertRaisesRegex(bridge.BridgeError, 'operation_requires_review'): self.start()
        self.assertEqual(len(self.posts('/api/searches')), 1)

    def test_saved_success_is_available_after_resources_are_exhausted_without_any_http_retry(self):
        operations = [
            ('start', '--task-id', TASK, '--revision', '1', '--operation-id', 'cached-start', '--allow-paid'),
            ('evolve', '--search-id', SEARCH, '--candidate-id', CANDIDATE, '--operation-id', 'cached-edit', '--allow-paid'),
            ('reactivate', '--search-id', SEARCH, '--candidate-id', CANDIDATE, '--operation-id', 'cached-retest', '--allow-paid'),
            ('restore', '--search-id', SEARCH, '--operation-id', 'cached-restore', '--allow-paid'),
            ('prepare-final', '--search-id', SEARCH, '--operation-id', 'cached-final', '--operator-review'),
        ]
        receipts = [self.run_command(*operation)['result'] for operation in operations]
        self.fixture.limit = self.fixture.used; self.fixture.model_configured = False
        self.fixture.search['state'] = 'queued'; self.fixture.search['selection'] = None
        before = len(self.fixture.requests)
        for operation, receipt in zip(operations, receipts):
            result = self.run_command(*operation)
            self.assertEqual(result['status'], 'cached_submission_receipt')
            self.assertEqual(result['result'], receipt)
        self.assertEqual(len(self.fixture.requests), before)
        with self.assertRaisesRegex(bridge.BridgeError, 'operation_id_conflict'):
            self.run_command('start', '--task-id', 'd' * 32, '--revision', '1', '--operation-id', 'cached-start', '--allow-paid')
        self.assertEqual(len(self.fixture.requests), before)

    def test_cancel_works_with_zero_budget_and_does_not_create_new_authorization(self):
        self.fixture.limit = self.fixture.used = 0; self.fixture.model_configured = False
        result = self.run_command('cancel', '--search-id', SEARCH, '--operation-id', 'stop-one')
        self.assertTrue(result['submitted']); self.assertEqual(self.posts()[0][1], '/api/searches/' + SEARCH + '/cancel')
        self.assertEqual(self.posts()[0][2], {})
        self.assertFalse(any('/budget' in r[1] for r in self.posts()))

    def test_evidence_is_explicit_owner_only_and_does_not_overwrite_user_files(self):
        summary = self.run_command('show', '--search-id', SEARCH)
        self.assertNotIn('private fixture output', bridge.encode(summary).decode())
        self.assertFalse(summary['selection']['quality_is_verified_accuracy'])
        path = self.root / 'evidence.json'; self.run_command('show', '--search-id', SEARCH, '--evidence-file', str(path))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        self.assertEqual(bridge.decode(path.read_bytes())['executions'][0]['output'], 'private fixture output')
        with self.assertRaisesRegex(bridge.BridgeError, 'output_already_exists'):
            self.run_command('show', '--search-id', SEARCH, '--evidence-file', str(path))
        self.assertTrue(path.is_file())

    def test_download_requires_accepted_receipt_matches_hash_and_never_executes_or_overwrites(self):
        path = self.root / 'service.zip'
        result = self.run_command('download', '--search-id', SEARCH, '--output', str(path))
        self.assertFalse(result['executed']); self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), result['sha256'])
        with self.assertRaisesRegex(bridge.BridgeError, 'output_already_exists'):
            self.run_command('download', '--search-id', SEARCH, '--output', str(path))
        self.fixture.archive_changed = True; other = self.root / 'other.zip'
        with self.assertRaisesRegex(bridge.BridgeError, 'archive_hash_mismatch'):
            self.run_command('download', '--search-id', SEARCH, '--output', str(other))
        self.assertFalse(other.exists()); self.assertEqual(self.posts(), [])

    def test_download_refuses_false_missing_or_non_boolean_quality_gate_before_archive_fetch(self):
        for report in ({'gate_passed': False}, {}, {'gate_passed': 1}, {'gate_passed': 'true'}):
            self.fixture.delivery['report'] = report
            path = self.root / 'unaccepted.zip'
            with self.subTest(report=report), self.assertRaisesRegex(bridge.BridgeError, 'accepted_export_required'):
                self.run_command('download', '--search-id', SEARCH, '--output', str(path))
            self.assertFalse(path.exists())
        self.assertFalse(any(r[1].endswith('/delivery/export') for r in self.fixture.requests))
        self.assertEqual(self.posts(), [])

    def test_operator_packets_are_read_only_and_explicit_answers_are_not_invented(self):
        summary = self.run_command('reviews', '--search-id', SEARCH)
        self.assertFalse(summary['operator_attestation_submitted']); self.assertNotIn('private fixture input', bridge.encode(summary).decode())
        path = self.root / 'packet.json'; self.run_command('review-packet', '--search-id', SEARCH, '--output', str(path))
        self.assertEqual(path.stat().st_mode & 0o777, 0o600); self.assertEqual(self.posts(), [])
        answers = self.root / 'answers.json'; value = {'execution_id': 1, 'snapshot_sha256': 'd' * 64, 'previous_review_id': None,
            'verdict': 'accept', 'reviewer': 'Explicit protocol fixture', 'comment': 'Not human acceptance evidence', 'attested': False}
        answers.write_bytes(bridge.encode(value))
        arguments = ('review-submit', '--search-id', SEARCH, '--answers', str(answers), '--operation-id', 'review-one')
        with self.assertRaisesRegex(bridge.BridgeError, 'explicit_operator_answers'): self.run_command(*arguments)
        self.assertEqual(self.posts(), [])
        value['attested'] = True; answers.write_bytes(bridge.encode(value))
        result = self.run_command(*arguments)
        self.assertTrue(result['result']['operator_attestation_submitted']); self.assertEqual(result['result']['submitted_user_verdict'], 'accept')
        request = self.posts()[0][2]; self.assertTrue(request['attested']); self.assertRegex(request['request_id'], '^[0-9a-f]{32}$')
        self.assertEqual(self.run_command(*arguments)['status'], 'cached_submission_receipt'); self.assertEqual(len(self.posts()), 1)

    def test_stale_review_is_preserved_as_refused_and_cannot_be_silently_resubmitted(self):
        answers = self.root / 'stale-answers.json'; answers.write_bytes(bridge.encode({'execution_id': 1,
            'snapshot_sha256': 'd' * 64, 'previous_review_id': None, 'verdict': 'reject',
            'reviewer': 'Explicit fixture', 'comment': 'Protocol only', 'attested': True}))
        self.fixture.mode = 'stale_review'
        arguments = ('review-submit', '--search-id', SEARCH, '--answers', str(answers), '--operation-id', 'stale-review')
        with self.assertRaisesRegex(bridge.BridgeError, 'review_snapshot_changed'): self.run_command(*arguments)
        self.assertEqual(bridge.Journal(self.state).read('stale-review')['state'], 'refused')
        self.fixture.mode = None
        with self.assertRaisesRegex(bridge.BridgeError, 'operation_requires_review'): self.run_command(*arguments)
        self.assertEqual(len(self.posts()), 1)

    def test_symlink_private_journal_and_download_output_are_refused(self):
        external = self.root / 'external'; external.mkdir(); self.state.symlink_to(external)
        with self.assertRaises(bridge.BridgeError): self.start()
        self.assertEqual(self.posts(), []); self.assertEqual(list(external.iterdir()), [])
        target = self.root / 'unchanged.txt'; target.write_text('User content')
        link = self.root / 'service.zip'; link.symlink_to(target)
        with self.assertRaisesRegex(bridge.BridgeError, 'output_already_exists'):
            self.run_command('download', '--search-id', SEARCH, '--output', str(link))
        self.assertEqual(target.read_text(), 'User content')

    def test_final_run_and_completion_are_explicit_bound_operations_not_quality_claims(self):
        args = ('prepare-final', '--search-id', SEARCH, '--operation-id', 'final-one')
        with self.assertRaisesRegex(bridge.BridgeError, 'explicit_operator_final'): self.run_command(*args)
        result = self.run_command(*args, '--allow-paid', '--operator-review')
        self.assertTrue(result['submitted']); self.assertEqual(self.posts()[0][2]['quality_mode'], 'operator_review')
        self.assertFalse(result['result']['quality_is_verified_accuracy'])
        answers = self.root / 'decision.json'; answers.write_bytes(bridge.encode({'review_evidence_sha256': 'e' * 64,
            'reviewer': 'Explicit fixture', 'comment': 'Protocol only', 'attested': True}))
        self.run_command('complete-review', '--search-id', SEARCH, '--answers', str(answers), '--operation-id', 'decision-one')
        self.assertEqual(self.posts()[-1][1], '/api/searches/' + SEARCH + '/delivery/quality-decision')

    def test_deterministic_final_needs_explicit_review_intent_but_no_model_or_paid_budget(self):
        self.fixture.limit = self.fixture.used = 0; self.fixture.model_configured = False
        result = self.run_command('prepare-final', '--search-id', SEARCH, '--operation-id', 'free-final', '--operator-review')
        self.assertTrue(result['submitted'])
        self.assertEqual(self.posts()[0][2]['quality_mode'], 'operator_review')
        self.assertFalse(any(r[1] in {'/api/budget', '/api/model-status'} for r in self.fixture.requests))

    def test_model_or_unknown_family_final_keeps_explicit_paid_authorization_and_resource_gate(self):
        for family in ('prompt.v1', 'future.unreviewed.v1'):
            self.fixture.search['candidates'][0]['family'] = family
            arguments = ('prepare-final', '--search-id', SEARCH, '--operation-id', 'paid-final', '--operator-review')
            with self.subTest(family=family), self.assertRaisesRegex(bridge.BridgeError, 'explicit_paid_command_required'):
                self.run_command(*arguments)
        self.assertEqual(self.posts(), [])
        self.fixture.limit = self.fixture.used
        with self.assertRaisesRegex(bridge.BridgeError, 'existing_budget_required'):
            self.run_command(*arguments, '--allow-paid')
        self.assertFalse(self.state.exists()); self.assertEqual(self.posts(), [])


if __name__ == '__main__': unittest.main()
