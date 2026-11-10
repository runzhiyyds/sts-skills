"""Optional loopback STS client. No model keys, candidate execution or implicit payment."""

import argparse
from contextlib import contextmanager
import hashlib
from http.client import HTTPException
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import stat
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
import uuid

MAX_TASK = 262144
MAX_JSON = 8 * 1024 * 1024
MAX_ARCHIVE = 32 * 1024 * 1024
IDENTIFIER = re.compile(r'[0-9a-f]{32}\Z')
OPERATION = re.compile(r'[A-Za-z0-9_.-]{1,100}\Z')
SECRET = re.compile(r'\b(?:sk-[A-Za-z0-9_-]{24,}|sk-proj-[A-Za-z0-9_-]{20,})\b')
SECRET_FIELDS = {'api_key', 'authorization', 'access_token', 'secret_key', 'private_key', 'password'}
GET_PATH = re.compile(r'/api/(?:health|budget|model-status|tasks(?:/[0-9a-f]{32}(?:/revisions/[1-9][0-9]{0,8})?)?|searches|searches/[0-9a-f]{32}(?:/delivery(?:/export)?|/quality-reviews|/delivery/reviews)?)\Z')
POST_PATH = re.compile(r'/api/(?:tasks(?:/preview)?|searches|searches/[0-9a-f]{32}/(?:cancel|rollback|quality-reviews|delivery(?:/reviews|/quality-decision)?|candidates/[0-9a-f]{32}/(?:evolve|reactivate)))\Z')


class BridgeError(ValueError):
    def __init__(self, code, http_status=None):
        self.code, self.http_status = code, http_status
        super().__init__(code)


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def decode(body):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate_key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('nonfinite_json')
    try:
        return json.loads(body, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError):
        raise BridgeError('invalid_json') from None


def identifier(value):
    if type(value) is not str or not IDENTIFIER.fullmatch(value):
        raise BridgeError('invalid_identifier')
    return value


def no_credentials(value):
    if type(value) is dict:
        if any(key.casefold() in SECRET_FIELDS for key in value):
            raise BridgeError('credentials_in_task')
        for item in value.values():
            no_credentials(item)
    elif type(value) is list:
        for item in value:
            no_credentials(item)
    elif type(value) is str and (SECRET.search(value) or '-----BEGIN PRIVATE KEY-----' in value):
        raise BridgeError('credentials_in_task')


def redacted(value):
    if type(value) is dict:
        return {key: ('[redacted]' if key.casefold() in SECRET_FIELDS else redacted(item)) for key, item in value.items()}
    if type(value) is list:
        return [redacted(item) for item in value]
    if type(value) is str:
        return SECRET.sub('[redacted]', value)
    return value


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, base_url='http://127.0.0.1:8000', timeout=20):
        try:
            address = urlsplit(base_url)
            port = address.port
        except (TypeError, ValueError):
            raise BridgeError('loopback_url_required') from None
        if (address.scheme != 'http' or address.hostname not in {'127.0.0.1', 'localhost'} or not port
                or address.username or address.password or address.path not in ('', '/') or address.query or address.fragment):
            raise BridgeError('loopback_url_required')
        # Never resolve localhost through DNS or inherit an HTTP proxy for task data.
        self.base_url = 'http://127.0.0.1:' + str(port)
        self.timeout = timeout
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def request(self, method, path, body=None, archive=False):
        if not (GET_PATH if method == 'GET' else POST_PATH).fullmatch(path) or method not in {'GET', 'POST'}:
            raise BridgeError('unsupported_engine_endpoint')
        if archive and not (method == 'GET' and path.endswith('/delivery/export')):
            raise BridgeError('unsupported_engine_endpoint')
        headers = {'Accept': 'application/zip' if archive else 'application/json'}
        data = None
        if method == 'POST':
            data = encode(body)
            if len(data) > MAX_TASK:
                raise BridgeError('task_too_large')
            headers.update({'Content-Type': 'application/json', 'X-STS-Request': '1'})
        limit = MAX_ARCHIVE if archive else MAX_JSON
        try:
            with self.opener.open(Request(self.base_url + path, data=data, headers=headers, method=method), timeout=self.timeout) as response:
                content_type = response.headers.get_content_type()
                if content_type != ('application/zip' if archive else 'application/json'):
                    raise BridgeError('invalid_engine_response')
                payload = response.read(limit + 1)
                if len(payload) > limit:
                    raise BridgeError('engine_response_too_large')
                if archive:
                    return payload
                value = decode(payload)
                if type(value) is not dict:
                    raise BridgeError('invalid_engine_response')
                return value
        except HTTPError as error:
            try:
                body = error.read(4097)
            except (OSError, HTTPException):
                raise BridgeError('engine_unavailable') from None
            code = 'engine_request_refused'
            try:
                value = decode(body)
                candidate = value.get('error') if type(value) is dict else None
                if type(candidate) is str and re.fullmatch('[a-z][a-z0-9_]{0,80}', candidate) and not SECRET.search(candidate):
                    code = candidate
            except BridgeError:
                pass
            raise BridgeError(code, error.code) from None
        except (URLError, TimeoutError, OSError, HTTPException):
            raise BridgeError('engine_unavailable') from None

    def get(self, path):
        return self.request('GET', path)


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise BridgeError('invalid_engine_response')
    return value


def status(client):
    health = client.get('/api/health')
    budget = client.get('/api/budget')
    if type(health) is not dict or health.get('status') != 'ok' or type(budget) is not dict:
        raise BridgeError('invalid_engine_response')
    limit = number(budget.get('limit_cny', 0)); used = number(budget.get('committed_ceiling_cny', 0))
    try:
        model = client.get('/api/model-status')
        configured = model.get('configured') is True and model.get('api_key_configured') is True
    except BridgeError as error:
        if error.http_status != 404:
            raise
        configured = None  # Read-only compatibility with STS v0.13; never assume configured.
    return {'status': 'ok', 'engine_version': health.get('version'), 'engine_url': client.base_url,
            'candidate_execution_enabled': health.get('candidate_execution_enabled') is True,
            'isolated_code_runtime_available': health.get('arbitrary_code_execution_enabled') is True,
            'model_configured': configured, 'connection_verified': False,
            'budget': {'currency': 'CNY', 'authorized_ceiling': limit, 'committed_ceiling': used,
                       'remaining_ceiling': max(0, limit - used), 'provider_bill_verified': False},
            'paid_request_submitted': False}


def preflight_paid(client):
    facts = status(client)
    if not facts['candidate_execution_enabled']:
        raise BridgeError('engine_execution_disabled')
    if facts['model_configured'] is not True:
        raise BridgeError('model_configuration_required' if facts['model_configured'] is False else 'model_status_unavailable')
    if facts['budget']['remaining_ceiling'] <= 0:
        raise BridgeError('existing_budget_required')
    return facts


def task_summary(task):
    definition = task.get('contract', {}).get('definition', {})
    dataset = task.get('contract', {}).get('dataset', {})
    return {'task_id': task.get('task_id'), 'revision': task.get('revision'), 'title': definition.get('title', task.get('title')),
            'sample_count': dataset.get('sample_count', task.get('sample_count')), 'content_sha256': task.get('content_sha256')}


def search_summary(search):
    result = {key: search.get(key) for key in ('id', 'task_id', 'revision', 'state', 'error', 'source_search_id', 'delivery_id')}
    rows = search.get('executions', [])
    result['execution_count'] = len(rows)
    result['candidates'] = []
    for candidate in search.get('candidates', []):
        observations = [row for row in rows if row.get('candidate_id') == candidate.get('id')]
        labels = [r['label_agreement'] for r in observations if r.get('label_agreement') in (0, 1)]
        checks = [r['criteria'] for r in observations if (r.get('criteria') or {}).get('status') == 'checked']
        result['candidates'].append({'id': candidate.get('id'), 'family': candidate.get('family'), 'name': candidate.get('name'),
            'executions': len(observations), 'execution_errors': sum(r.get('error') is not None for r in observations),
            'provided_unverified_label_matches': sum(labels), 'provided_label_cases': len(labels),
            'structural_passes': sum(c.get('passed') is True for c in checks), 'structural_cases': len(checks)})
    selection = search.get('selection') or {}
    evidence = selection.get('evidence') or {}
    result['selection'] = {'candidate_id': selection.get('candidate_id'), 'basis': evidence.get('basis'),
                           'quality_is_verified_accuracy': False, 'final_test_evaluated': evidence.get('final_test_evaluated', False)}
    bundle = search.get('criteria_bundle') or {}
    result['criteria'] = {'status': bundle.get('status'), 'schema_sha256': bundle.get('schema_sha256'),
                          'semantic_quality_verified': False}
    return redacted(result)


class Journal:
    """Owner-local submission fence, not another budget or provider ledger."""
    def __init__(self, path):
        self.path = Path(path).expanduser()

    @contextmanager
    def connection(self):
        if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'getuid'):
            raise BridgeError('private_state_platform_unreviewed')
        if self.path.is_symlink():
            raise BridgeError('unsafe_bridge_state')
        self.path.mkdir(mode=0o700, parents=True, exist_ok=True)
        file = self.path / 'operations.sqlite3'
        descriptor = os.open(file, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                raise BridgeError('unsafe_bridge_state')
            os.fchmod(descriptor, 0o600)
        finally:
            os.close(descriptor)
        db = sqlite3.connect(file, timeout=5, isolation_level=None); db.row_factory = sqlite3.Row
        try:
            db.execute('CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,engine TEXT NOT NULL,action TEXT NOT NULL,payload_sha256 TEXT NOT NULL,request_id TEXT NOT NULL,state TEXT NOT NULL,result_json TEXT,error_code TEXT,created_at REAL NOT NULL)')
            yield db
        finally:
            db.close()

    def claim(self, operation_id, engine, action, payload):
        if not OPERATION.fullmatch(operation_id):
            raise BridgeError('invalid_operation_id')
        digest = hashlib.sha256(encode(payload)).hexdigest()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM operations WHERE id=?', (operation_id,)).fetchone()
            if row:
                if (row['engine'], row['action'], row['payload_sha256']) != (engine, action, digest):
                    raise BridgeError('operation_id_conflict')
                if row['state'] != 'succeeded':
                    raise BridgeError('operation_requires_review')
                return False, row['request_id'], decode(row['result_json'])
            request_id = uuid.uuid4().hex
            db.execute("INSERT INTO operations VALUES(?,?,?,?,?,'started',NULL,NULL,?)", (operation_id, engine, action, digest, request_id, time.time()))
            db.commit()
        return True, request_id, None

    def cached(self, operation_id, engine, action, payload):
        """Read an existing fence before checking resources for genuinely new work."""
        if not OPERATION.fullmatch(operation_id):
            raise BridgeError('invalid_operation_id')
        if self.path.is_symlink():
            raise BridgeError('unsafe_bridge_state')
        file = self.path / 'operations.sqlite3'
        if not file.exists() and not file.is_symlink():
            return None
        digest = hashlib.sha256(encode(payload)).hexdigest()
        with self.connection() as db:
            row = db.execute('SELECT * FROM operations WHERE id=?', (operation_id,)).fetchone()
        if row is None:
            return None
        if (row['engine'], row['action'], row['payload_sha256']) != (engine, action, digest):
            raise BridgeError('operation_id_conflict')
        if row['state'] != 'succeeded':
            raise BridgeError('operation_requires_review')
        return decode(row['result_json'])

    def finish(self, operation_id, result=None, error=None):
        with self.connection() as db:
            if result is not None:
                db.execute("UPDATE operations SET state='succeeded',result_json=? WHERE id=? AND state='started'", (encode(result).decode(), operation_id))
            else:
                state = 'refused' if error.http_status and 400 <= error.http_status < 500 else 'uncertain'
                db.execute('UPDATE operations SET state=?,error_code=? WHERE id=? AND state=\'started\'', (state, error.code, operation_id))

    def read(self, operation_id):
        if not (self.path / 'operations.sqlite3').is_file():
            raise BridgeError('operation_not_found')
        if not OPERATION.fullmatch(operation_id):
            raise BridgeError('invalid_operation_id')
        with self.connection() as db:
            row = db.execute('SELECT id,engine,action,request_id,state,error_code,created_at,result_json FROM operations WHERE id=?', (operation_id,)).fetchone()
        if row is None:
            raise BridgeError('operation_not_found')
        result = dict(row); raw = result.pop('result_json')
        result['result'] = decode(raw) if raw else None
        return result


def submit(client, journal, operation_id, action, path, payload, summarize, request_id=True, preflight=None):
    cached = journal.cached(operation_id, client.base_url, action, payload)
    if cached is not None:
        return {'status': 'cached_submission_receipt', 'submitted': False, 'result': cached}
    if preflight is not None:
        preflight()
    # Recheck/claim atomically: another client may have submitted during preflight.
    created, key, cached = journal.claim(operation_id, client.base_url, action, payload)
    if not created:
        return {'status': 'cached_submission_receipt', 'submitted': False, 'result': cached}
    body = {**payload, 'request_id': key} if request_id else payload
    try:
        response = client.request('POST', path, body)
        result = summarize(response)
    except BridgeError as error:
        journal.finish(operation_id, error=error)
        raise
    except (ValueError, KeyError, TypeError, AttributeError):
        error = BridgeError('invalid_engine_response'); journal.finish(operation_id, error=error); raise error from None
    journal.finish(operation_id, result=result)
    return {'status': 'submitted', 'submitted': True, 'request_id': key, 'result': result}


def definition_file(path):
    with Path(path).open('rb') as handle:
        raw = handle.read(MAX_TASK + 1)
    if len(raw) > MAX_TASK:
        raise BridgeError('task_too_large')
    value = decode(raw)
    if type(value) is not dict:
        raise BridgeError('task_definition_required')
    no_credentials(value)
    return value


def preview(client, definition):
    result = client.request('POST', '/api/tasks/preview', {'definition': definition})
    return {'content_sha256': result.get('content_sha256'), 'outcome': result.get('contract', {}).get('definition', {}).get('output_specification'),
            'sample_count': result.get('contract', {}).get('dataset', {}).get('sample_count'),
            'label_count': result.get('contract', {}).get('evaluation', {}).get('label_count'),
            'budget': result.get('contract', {}).get('definition', {}).get('budget'),
            'search_started': False}


def write_exclusive(path, body):
    path = Path(path)
    if path.is_symlink():
        raise BridgeError('output_already_exists')
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    except FileExistsError:
        raise BridgeError('output_already_exists') from None
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(body)


def review_path(search_id, phase):
    return '/api/searches/' + identifier(search_id) + ('/quality-reviews' if phase == 'validation' else '/delivery/reviews')


def review_input(path, phase, decision=False):
    value = definition_file(path)
    expected = {'review_evidence_sha256', 'reviewer', 'comment', 'attested'} if decision else {
        'execution_id' if phase == 'validation' else 'sample_index', 'snapshot_sha256', 'previous_review_id',
        'verdict', 'reviewer', 'comment', 'attested'}
    if value.keys() != expected or value.get('attested') is not True:
        raise BridgeError('explicit_operator_answers_required')
    if (type(value['reviewer']) is not str or not value['reviewer'].strip() or len(value['reviewer']) > 100
            or type(value['comment']) is not str or len(value['comment']) > 2000):
        raise BridgeError('explicit_operator_answers_required')
    digest = value['review_evidence_sha256'] if decision else value['snapshot_sha256']
    if type(digest) is not str or not re.fullmatch('[0-9a-f]{64}', digest):
        raise BridgeError('invalid_review_snapshot')
    if not decision:
        if value['verdict'] not in ('accept', 'reject', 'unsure'):
            raise BridgeError('explicit_operator_answers_required')
        key = 'execution_id' if phase == 'validation' else 'sample_index'
        if type(value[key]) is not int or value[key] < 0:
            raise BridgeError('invalid_review_target')
        if value['previous_review_id'] is not None:
            identifier(value['previous_review_id'])
    return value


def delivery_summary(delivery):
    report = delivery.get('report') or {}
    export = delivery.get('export') or {}
    return {'delivery_id': delivery.get('id'), 'state': delivery.get('state'),
            'final_gate_passed': report.get('gate_passed'), 'quality_is_verified_accuracy': False,
            'archive_integrity_verified': export.get('archive_integrity_verified') is True,
            'archive_sha256': export.get('archive_sha256'), 'publicly_deployed': False}


def review_summary(packet):
    return {'phase': packet.get('subject_kind', packet.get('phase')), 'closed': packet.get('closed'),
            'target_count': len(packet.get('targets', [])), 'review_evidence_sha256': packet.get('review_evidence_sha256'),
            'operator_feedback': redacted(packet.get('summary', {})), 'operator_attestation_submitted': False}


def run(args, client=None):
    client = client or Client(args.url)
    command = args.command or 'status'
    if command == 'status':
        return status(client)
    if command == 'tasks':
        return {'tasks': [task_summary(t) for t in client.get('/api/tasks')['tasks']], 'search_started': False}
    if command == 'searches':
        rows = client.get('/api/searches')['searches']
        return {'searches': [{k: r.get(k) for k in ('id', 'task_id', 'revision', 'state', 'error', 'source_search_id')} for r in rows if not args.task_id or r.get('task_id') == identifier(args.task_id)]}
    if command in ('show', 'reviews', 'review-packet', 'delivery', 'download'):
        sid = identifier(args.search_id)
        if command in ('reviews', 'review-packet'):
            packet = client.get(review_path(sid, args.phase))
            summary = review_summary(packet)
            if command == 'review-packet':
                write_exclusive(args.output, encode(redacted(packet)) + b'\n')
                summary['private_packet_file'] = str(Path(args.output).resolve())
            return summary
        if command == 'show':
            search = client.get('/api/searches/' + sid)
            summary = search_summary(search)
            if args.evidence_file:
                write_exclusive(args.evidence_file, encode(redacted(search)) + b'\n')
                summary['private_evidence_file'] = str(Path(args.evidence_file).resolve())
            return summary
        delivery = client.get('/api/searches/' + sid + '/delivery').get('delivery')
        if delivery is None:
            raise BridgeError('delivery_not_available')
        export = delivery.get('export') or {}
        if command == 'delivery':
            return delivery_summary(delivery)
        if ((delivery.get('report') or {}).get('gate_passed') is not True
                or export.get('archive_integrity_verified') is not True
                or not re.fullmatch('[0-9a-f]{64}', export.get('archive_sha256', ''))):
            raise BridgeError('accepted_export_required')
        body = client.request('GET', '/api/searches/' + sid + '/delivery/export', archive=True)
        if hashlib.sha256(body).hexdigest() != export['archive_sha256']:
            raise BridgeError('archive_hash_mismatch')
        write_exclusive(args.output, body)
        return {'status': 'downloaded', 'path': str(Path(args.output).resolve()), 'sha256': export['archive_sha256'], 'executed': False}
    if command == 'preview':
        return preview(client, definition_file(args.definition))
    if command == 'operation':
        return Journal(args.state_dir).read(args.operation_id)
    journal = Journal(args.state_dir)
    if command == 'save':
        definition = definition_file(args.definition)
        if not re.fullmatch('[0-9a-f]{64}', args.reviewed_sha256):
            raise BridgeError('reviewed_task_changed')
        def preflight_save():
            checked = preview(client, definition)
            if checked['content_sha256'] != args.reviewed_sha256:
                raise BridgeError('reviewed_task_changed')
        return submit(client, journal, args.operation_id, command, '/api/tasks',
                      {'definition': definition, 'reviewed_sha256': args.reviewed_sha256}, task_summary,
                      request_id=False, preflight=preflight_save)
    if command in ('review-submit', 'complete-review'):
        sid = identifier(args.search_id)
        if command == 'complete-review' and args.phase != 'final':
            raise BridgeError('final_phase_required')
        payload = review_input(args.answers, args.phase, decision=command == 'complete-review')
        path = ('/api/searches/' + sid + '/delivery/quality-decision') if command == 'complete-review' else review_path(sid, args.phase)
        # Attestation is accepted only from the explicit answers file; never generated here.
        summarize = (lambda value: {**review_summary(value), 'submitted_user_verdict': payload['verdict'], 'operator_attestation_submitted': True}) if command == 'review-submit' else delivery_summary
        return submit(client, journal, args.operation_id, command + ':' + path, path, payload, summarize)
    if command == 'prepare-final':
        if not args.operator_review:
            raise BridgeError('explicit_operator_final_required')
        sid = identifier(args.search_id)
        def preflight_final():
            source = client.get('/api/searches/' + sid)
            winner = next((c for c in source.get('candidates', []) if c.get('id') == (source.get('selection') or {}).get('candidate_id')), None)
            if not winner:
                raise BridgeError('selected_candidate_required')
            family = winner.get('family')
            # Only known deterministic families waive API authorization. Unknown
            # extensions remain the engine's decision and require explicit paid intent.
            deterministic = family in {'rules.v1', 'python.v1', 'sklearn.classifier.v1'}
            if family == 'workflow.v1':
                steps = winner.get('artifact', {}).get('steps', [])
                deterministic = bool(steps) and all(t.get('family') in {'rules.v1', 'python.v1'} for t in steps)
            if not deterministic:
                if not args.allow_paid:
                    raise BridgeError('explicit_paid_command_required')
                preflight_paid(client)
        return submit(client, journal, args.operation_id, command + ':' + sid, '/api/searches/' + sid + '/delivery',
                      {'quality_mode': 'operator_review'}, delivery_summary, preflight=preflight_final)
    if command == 'cancel':
        sid = identifier(args.search_id)
        return submit(client, journal, args.operation_id, command + ':' + sid, '/api/searches/' + sid + '/cancel', {}, search_summary, request_id=False)
    if not args.allow_paid:
        raise BridgeError('explicit_paid_command_required')
    if command == 'start':
        task_id = identifier(args.task_id)
        if type(args.revision) is not int or not 1 <= args.revision <= 999999999:
            raise BridgeError('invalid_task_revision')
        def preflight_start():
            preflight_paid(client)
            task = client.get('/api/tasks/' + task_id + '/revisions/' + str(args.revision))
            if task.get('revision') != args.revision:
                raise BridgeError('task_revision_changed')
            budget = task.get('contract', {}).get('definition', {}).get('budget', {})
            if budget.get('mode') != 'inherit_work' and (number(budget.get('max_cost_cny', 0)) <= 0 or budget.get('max_candidate_executions', 0) < 2):
                raise BridgeError('positive_task_budget_required')
        return submit(client, journal, args.operation_id, command, '/api/searches', {'task_id': task_id, 'revision': args.revision}, search_summary, preflight=preflight_start)
    sid = identifier(args.search_id)
    if command == 'restore':
        path = '/api/searches/' + sid + '/rollback'
    else:
        cid = identifier(args.candidate_id)
        path = '/api/searches/' + sid + '/candidates/' + cid + '/' + command
    def preflight_existing():
        preflight_paid(client)
        source = client.get('/api/searches/' + sid)
        if source.get('state') not in {'succeeded', 'failed', 'cancelled', 'interrupted'}:
            raise BridgeError('completed_search_required')
        if command != 'restore' and not any(c.get('id') == cid for c in source.get('candidates', [])):
            raise BridgeError('candidate_not_found')
    return submit(client, journal, args.operation_id, command + ':' + sid + ':' + path, path, {}, search_summary, preflight=preflight_existing)


MESSAGES = {
    'en-US': {'ok': 'Local STS information only; no paid request submitted.', 'submitted': 'Request submitted once. Inspect actual results; this receipt is not execution or quality acceptance.',
              'cached_submission_receipt': 'Saved receipt returned. No request was submitted again.', 'downloaded': 'Accepted source archive downloaded and hash checked; no code executed.',
              'error': 'The operation stopped. Inspect the code; do not change operation IDs to retry an uncertain submission.'},
    'zh-CN': {'ok': '仅查看本机 STS 信息，没有提交付费请求。', 'submitted': '请求只提交了一次。请查看真实结果；回执不代表执行或质量验收已完成。',
              'cached_submission_receipt': '返回已保存的回执，没有再次提交请求。', 'downloaded': '已下载并核验源码包，未执行代码。',
              'error': '操作已停止。请查看原因代码，不要更换操作编号来重试费用或结果不明的请求。'}
}


ERROR_MESSAGES = {
    'en-US': {
        'engine_unavailable': 'The local STS service is not reachable. Start it locally; no automatic retry was made.',
        'model_configuration_required': 'A model connection is missing. Ask your agent to configure it in a hidden terminal prompt; never send the key here.',
        'model_status_unavailable': 'This engine cannot report model readiness safely. Use read-only commands or update it before starting exploration.',
        'existing_budget_required': 'No approved model budget remains. This helper will not create or increase a budget.',
        'operation_requires_review': 'An earlier operation is unresolved or refused. Inspect its saved receipt and engine state; do not submit it with a new ID.',
        'reviewed_task_changed': 'The task differs from the version reviewed. Preview the current file and review the change first.',
        'explicit_operator_answers_required': 'Only your explicit review answers and attestation can be submitted. This helper does not create approvals.',
        'explicit_operator_final_required': 'Final checks close these inputs to further search. Use the explicit operator-review final command only when intended.',
        'archive_hash_mismatch': 'The downloaded archive does not match the accepted receipt. Nothing was written or executed.',
        'output_already_exists': 'The chosen output already exists. Its contents were preserved.',
    },
    'zh-CN': {
        'engine_unavailable': '无法连接本机 STS。请先在本地启动；工具没有自动重试。',
        'model_configuration_required': '尚未配置模型连接。请让 Agent 在终端隐藏输入密钥，不要在聊天中发送。',
        'model_status_unavailable': '当前引擎还不能安全报告模型就绪状态。可继续只读查看，更新引擎后再启动探索。',
        'existing_budget_required': '已授权的模型预算不足。工具不会自行创建或提高额度。',
        'operation_requires_review': '之前的操作仍待核对或已被拒绝。请查看保存回执和引擎状态，不要换新编号重复提交。',
        'reviewed_task_changed': '任务已不同于审阅过的版本。请重新预览文件并确认变更。',
        'explicit_operator_answers_required': '只能提交你明确给出的判断和确认。工具不会代你生成认可意见。',
        'explicit_operator_final_required': '最终检查会关闭这些输入的后续搜索。请只在确实准备完成检查时明确启用人工复核模式。',
        'archive_hash_mismatch': '下载包与已验收回执不一致，没有保存或执行。',
        'output_already_exists': '目标文件已存在，原内容保持不变。',
    },
}


def parser():
    p = argparse.ArgumentParser(description='Use a local STS engine without opening its frontend; no keys or installs.')
    p.add_argument('--url', default='http://127.0.0.1:8000'); p.add_argument('--language', choices=('en-US', 'zh-CN'), default='en-US')
    p.add_argument('--state-dir', type=Path, default=Path('.sts-skill-bridge'))
    sub = p.add_subparsers(dest='command')
    sub.add_parser('status'); sub.add_parser('tasks')
    searches = sub.add_parser('searches'); searches.add_argument('--task-id')
    for name in ('show', 'reviews', 'review-packet', 'delivery', 'download'):
        c = sub.add_parser(name); c.add_argument('--search-id', required=True)
        if name == 'show': c.add_argument('--evidence-file', type=Path)
        if name in ('download', 'review-packet'): c.add_argument('--output', type=Path, required=True)
        if name in ('reviews', 'review-packet'): c.add_argument('--phase', choices=('validation', 'final'), default='validation')
    for name in ('preview', 'save'):
        c = sub.add_parser(name); c.add_argument('--definition', type=Path, required=True)
        if name == 'save': c.add_argument('--reviewed-sha256', required=True); c.add_argument('--operation-id', required=True)
    c = sub.add_parser('operation'); c.add_argument('--operation-id', required=True)
    for name in ('review-submit', 'complete-review'):
        c = sub.add_parser(name); c.add_argument('--search-id', required=True); c.add_argument('--answers', type=Path, required=True)
        c.add_argument('--operation-id', required=True); c.add_argument('--phase', choices=('validation', 'final'), default='validation' if name == 'review-submit' else 'final')
    for name in ('start', 'evolve', 'reactivate', 'restore', 'cancel', 'prepare-final'):
        c = sub.add_parser(name); c.add_argument('--operation-id', required=True)
        if name == 'start': c.add_argument('--task-id', required=True); c.add_argument('--revision', type=int, required=True)
        else: c.add_argument('--search-id', required=True)
        if name in ('evolve', 'reactivate'): c.add_argument('--candidate-id', required=True)
        if name != 'cancel': c.add_argument('--allow-paid', action='store_true')
        if name == 'prepare-final': c.add_argument('--operator-review', action='store_true')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    messages = MESSAGES[args.language]
    try:
        result = redacted(run(args))
        result.setdefault('message', messages.get(result.get('status'), messages['ok']))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (BridgeError, OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError) as error:
        code = error.code if isinstance(error, BridgeError) else 'local_input_or_state_invalid'
        print(json.dumps({'status': 'error', 'code': code, 'message': ERROR_MESSAGES[args.language].get(code, messages['error'])}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    sys.exit(main())
