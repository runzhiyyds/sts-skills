"""Owner-local evidence and cumulative authorization; never runs candidates or APIs."""

import argparse
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat

MICRO = 1_000_000


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def money(value):
    value = Decimal(value)
    if not value.is_finite() or value < 0 or value > 1_000_000 or value * MICRO != int(value * MICRO):
        raise ValueError('Use a nonnegative CNY amount with at most six decimals.')
    return int(value * MICRO)


@contextmanager
def connect(state):
    state = Path(state)
    if state.is_symlink():
        raise ValueError('State must be a private directory, not a symlink.')
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state, 0o700)
    path = state / 'evidence.sqlite3'
    descriptor = os.open(path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError('State must be an owner-controlled regular file.')
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)
    db = sqlite3.connect(path, timeout=10, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA synchronous=FULL')
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS task(id INTEGER PRIMARY KEY CHECK(id=1),goal_hash TEXT,dataset_hash TEXT,limit_micro INTEGER,final_candidate TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS samples(sample_index INTEGER PRIMARY KEY,input_hash TEXT,split TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY,purpose TEXT,reserved_micro INTEGER,cost_micro INTEGER,state TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY,family TEXT,path TEXT,artifact_hash TEXT)')
        db.execute('CREATE TABLE IF NOT EXISTS observations(candidate_id TEXT REFERENCES candidates(id),sample_index INTEGER REFERENCES samples(sample_index),split TEXT,evidence TEXT,PRIMARY KEY(candidate_id,sample_index))')
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def committed(db):
    return db.execute('SELECT COALESCE(SUM(COALESCE(cost_micro,reserved_micro)),0) FROM calls').fetchone()[0]


def initialize(db, inputs, goal, amount):
    if type(inputs) is not list or not 1 <= len(inputs) <= 10_000 or not goal.strip():
        raise ValueError('Provide a nonempty input list and goal.')
    dataset, goal_hash = digest(inputs), digest(goal)
    existing = db.execute('SELECT * FROM task').fetchone()
    if existing:
        if (existing['dataset_hash'], existing['goal_hash']) != (dataset, goal_hash):
            raise ValueError('Existing state belongs to another task; do not overwrite it.')
        if amount != existing['limit_micro']:
            raise ValueError('Initialization cannot reset authorization. Use budget explicitly.')
        return {'created': False, 'dataset_hash': dataset}
    hashes = [digest(value) for value in inputs]
    ordered = sorted(set(hashes), key=lambda value: digest([dataset, value, 'split-v1']))
    count = len(ordered); train = max(1, count // 2); final = max(1, count // 5) if count >= 10 else 0
    roles = {h: 'train' if i < train else 'final' if final and i >= count - final else 'validation' for i, h in enumerate(ordered)}
    db.execute('INSERT INTO task VALUES(1,?,?,?,NULL)', (goal_hash, dataset, amount))
    db.executemany('INSERT INTO samples VALUES(?,?,?)', [(i, h, roles[h]) for i, h in enumerate(hashes)])
    return {'created': True, 'dataset_hash': dataset, 'splits': {role: [i for i, h in enumerate(hashes) if roles[h] == role] for role in ('train', 'validation', 'final')}}


def operate(db, args):
    command = args.command
    if command == 'init':
        return initialize(db, json.loads(args.inputs.read_text()), args.goal.read_text(), money(args.cny))
    task = db.execute('SELECT * FROM task').fetchone()
    if not task:
        raise ValueError('Initialize this task first.')
    if command == 'status':
        return {'currency': 'CNY', 'authorized_ceiling': task['limit_micro'] / MICRO,
                'committed_ceiling': committed(db) / MICRO, 'provider_bill_verified': False,
                'final_candidate': task['final_candidate'], 'calls': [dict(row) for row in db.execute('SELECT * FROM calls')],
                'splits': {role: [r[0] for r in db.execute('SELECT sample_index FROM samples WHERE split=?', (role,))] for role in ('train', 'validation', 'final')}}
    if command == 'budget':
        amount = money(args.cny)
        if amount < committed(db):
            raise ValueError('Budget cannot be below committed usage/reservations.')
        db.execute('UPDATE task SET limit_micro=? WHERE id=1', (amount,)); return {'authorized_ceiling': amount / MICRO}
    if command == 'reserve':
        amount = money(args.ceiling_cny)
        if not args.id or not args.purpose or amount <= 0:
            raise ValueError('A unique operation ID, purpose and positive ceiling are required.')
        existing = db.execute('SELECT * FROM calls WHERE id=?', (args.id,)).fetchone()
        if existing:
            if existing['purpose'] != args.purpose or existing['reserved_micro'] != amount:
                raise ValueError('Operation ID conflict.')
            return {'created': False, 'submit_permitted': False, 'state': existing['state']}
        if committed(db) + amount > task['limit_micro']:
            raise ValueError('Cumulative budget exhausted.')
        db.execute("INSERT INTO calls VALUES(?,?,?,NULL,'reserved')", (args.id, args.purpose, amount))
        return {'created': True, 'submit_permitted': True}
    if command in ('settle', 'uncertain'):
        row = db.execute('SELECT * FROM calls WHERE id=?', (args.id,)).fetchone()
        if row is None:
            raise ValueError('Reserve the operation before submission.')
        if command == 'uncertain':
            if row['cost_micro'] is not None:
                raise ValueError('A settled cost cannot be made unknown.')
            db.execute("UPDATE calls SET state='uncertain' WHERE id=?", (args.id,)); return {'reservation_retained': True}
        amount = money(args.cost_cny)
        if amount > row['reserved_micro'] or (row['cost_micro'] is not None and row['cost_micro'] != amount):
            raise ValueError('Cost exceeds reservation or conflicts with settled receipt.')
        db.execute("UPDATE calls SET cost_micro=?,state='settled' WHERE id=?", (amount, args.id))
        return {'settled': True, 'provider_bill_verified': False}
    if command in ('candidate', 'record') and task['final_candidate']:
        raise ValueError('Final inputs are exposed; search/tuning is closed.')
    if command == 'candidate':
        if not args.id or not args.family or args.artifact.is_symlink() or not args.artifact.is_file():
            raise ValueError('Candidate needs an ID, extensible family and regular artifact.')
        artifact_hash = hashlib.sha256(args.artifact.read_bytes()).hexdigest()
        old = db.execute('SELECT * FROM candidates WHERE id=?', (args.id,)).fetchone()
        if old:
            if old['family'] != args.family or old['artifact_hash'] != artifact_hash:
                raise ValueError('Candidate artifacts are immutable; register a new ID.')
            return {'created': False, 'artifact_hash': artifact_hash}
        db.execute('INSERT INTO candidates VALUES(?,?,?,?)', (args.id, args.family, str(args.artifact.resolve()), artifact_hash))
        return {'created': True, 'artifact_hash': artifact_hash}
    if command == 'freeze':
        if task['final_candidate']:
            return {'created': False, 'final_candidate': task['final_candidate'], 'execute_final_permitted': False}
        candidate = db.execute('SELECT * FROM candidates WHERE id=?', (args.candidate,)).fetchone()
        if candidate is None or hashlib.sha256(Path(candidate['path']).read_bytes()).hexdigest() != candidate['artifact_hash']:
            raise ValueError('Candidate is missing or changed.')
        validation = [json.loads(row[0]) for row in db.execute("SELECT evidence FROM observations WHERE candidate_id=? AND split='validation'", (args.candidate,))]
        if not any(row['source'] == 'actual_execution' and row['error'] is None for row in validation):
            raise ValueError('Actual validation evidence is required before freeze.')
        if not db.execute("SELECT 1 FROM samples WHERE split='final'").fetchone():
            raise ValueError('No independent final partition; review required.')
        db.execute('UPDATE task SET final_candidate=? WHERE id=1', (args.candidate,))
        return {'created': True, 'final_candidate': args.candidate, 'execute_final_permitted': True, 'quality_certified': False}
    if command in ('record', 'final-record'):
        sample = db.execute('SELECT split FROM samples WHERE sample_index=?', (args.index,)).fetchone()
        role = sample['split'] if sample else None
        candidate = db.execute('SELECT * FROM candidates WHERE id=?', (args.candidate,)).fetchone()
        if candidate is None or hashlib.sha256(Path(candidate['path']).read_bytes()).hexdigest() != candidate['artifact_hash']:
            raise ValueError('Candidate is missing or changed; do not misattribute evidence.')
        if role is None or (command == 'record' and role == 'final') or (command == 'final-record' and (role != 'final' or task['final_candidate'] != args.candidate)):
            raise ValueError('Evidence violates the frozen train/validation/final protocol.')
        if type(args.latency_ms) is not float or args.latency_ms < 0:
            raise ValueError('Report nonnegative measured latency.')
        evidence = canonical({'output': json.loads(args.output.read_text()), 'error': args.error,
                              'latency_ms': args.latency_ms, 'source': args.source, 'quality_is_verified_accuracy': False})
        old = db.execute('SELECT evidence FROM observations WHERE candidate_id=? AND sample_index=?', (args.candidate, args.index)).fetchone()
        if old:
            if old[0] != evidence:
                raise ValueError('Evidence is immutable; do not overwrite or replay final inputs.')
            return {'created': False}
        db.execute('INSERT INTO observations VALUES(?,?,?,?)', (args.candidate, args.index, role, evidence))
        return {'created': True, 'split': role}
    raise ValueError('Unknown command.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init'); p.add_argument('--inputs', type=Path, required=True); p.add_argument('--goal', type=Path, required=True); p.add_argument('--cny', required=True)
    sub.add_parser('status')
    p = sub.add_parser('budget'); p.add_argument('--cny', required=True)
    p = sub.add_parser('reserve'); p.add_argument('--id', required=True); p.add_argument('--purpose', required=True); p.add_argument('--ceiling-cny', required=True)
    p = sub.add_parser('settle'); p.add_argument('--id', required=True); p.add_argument('--cost-cny', required=True)
    p = sub.add_parser('uncertain'); p.add_argument('--id', required=True)
    p = sub.add_parser('candidate'); p.add_argument('--id', required=True); p.add_argument('--family', required=True); p.add_argument('--artifact', type=Path, required=True)
    p = sub.add_parser('freeze'); p.add_argument('--candidate', required=True)
    for name in ('record', 'final-record'):
        p = sub.add_parser(name); p.add_argument('--candidate', required=True); p.add_argument('--index', required=True, type=int)
        p.add_argument('--output', required=True, type=Path); p.add_argument('--latency-ms', required=True, type=float)
        p.add_argument('--source', choices=('actual_execution', 'protocol_fixture'), required=True); p.add_argument('--error')
    args = parser.parse_args()
    with connect(args.state_dir) as db:
        print(canonical(operate(db, args)))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, InvalidOperation, OSError, sqlite3.Error):
        raise SystemExit('Evidence operation refused; inspect task, budget and immutable state. No operation was replayed.') from None
