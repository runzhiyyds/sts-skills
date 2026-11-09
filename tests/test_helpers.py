"""Protocol tests only; not evidence of model optimization or task accuracy."""

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from install_skill import install
from package_skill import build, FILES, SKILL
spec = importlib.util.spec_from_file_location('evidence', SKILL / 'scripts/evidence.py')
evidence = importlib.util.module_from_spec(spec); spec.loader.exec_module(evidence)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name); self.state = self.root / 'private-state'
        self.inputs = [{'text': 'synthetic input ' + str(i)} for i in range(20)]
        with evidence.connect(self.state) as db:
            self.created = evidence.initialize(db, self.inputs, 'Protocol fixture outcome', 3_000_000)

    def op(self, command, **kwargs):
        with evidence.connect(self.state) as db:
            return evidence.operate(db, SimpleNamespace(command=command, **kwargs))

    def candidate(self, cid='c'):
        path = self.root / (cid + '.json'); path.write_text('{"rule":"protocol fixture only"}')
        self.op('candidate', id=cid, family='future.extensible.family', artifact=path)
        return path

    def observation(self, candidate, index, source='actual_execution', command='record'):
        output = self.root / 'output.json'; output.write_text('"explicit protocol fixture output"')
        return self.op(command, candidate=candidate, index=index, output=output, latency_ms=1.0, source=source, error=None)

    def test_restart_cannot_reset_initial_budget_or_dataset(self):
        with evidence.connect(self.state) as db:
            self.assertFalse(evidence.initialize(db, self.inputs, 'Protocol fixture outcome', 3_000_000)['created'])
            with self.assertRaises(ValueError): evidence.initialize(db, self.inputs, 'other goal', 3_000_000)
            with self.assertRaises(ValueError): evidence.initialize(db, self.inputs, 'Protocol fixture outcome', 9_000_000)
        self.op('reserve', id='one', purpose='explicit fixture', ceiling_cny='2')
        self.assertEqual(self.op('status')['committed_ceiling'], 2)
        with self.assertRaises(ValueError): self.op('budget', cny='1')
        self.assertEqual(self.op('status')['committed_ceiling'], 2)

    def test_concurrent_reservation_cannot_overspend(self):
        def reserve(i):
            try: return self.op('reserve', id=str(i), purpose='fixture', ceiling_cny='2')['created']
            except ValueError: return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(reserve, range(8))), 1)
        self.assertEqual(self.op('status')['committed_ceiling'], 2)

    def test_duplicate_and_uncertain_operations_are_not_submit_permissions(self):
        self.assertTrue(self.op('reserve', id='once', purpose='fixture', ceiling_cny='2')['submit_permitted'])
        self.op('uncertain', id='once')
        self.assertFalse(self.op('reserve', id='once', purpose='fixture', ceiling_cny='2')['submit_permitted'])
        self.assertEqual(self.op('status')['committed_ceiling'], 2)
        with self.assertRaises(ValueError): self.op('reserve', id='once', purpose='different', ceiling_cny='2')
        self.op('settle', id='once', cost_cny='0.1')
        self.assertEqual(self.op('status')['committed_ceiling'], 0.1)
        self.assertFalse(self.op('reserve', id='once', purpose='fixture', ceiling_cny='2')['submit_permitted'])
        with self.assertRaises(ValueError): self.op('settle', id='once', cost_cny='0')
        self.assertFalse(self.op('status')['provider_bill_verified'])

    def test_duplicate_inputs_share_one_split(self):
        state = self.root / 'duplicate-state'; inputs = self.inputs + self.inputs
        with evidence.connect(state) as db:
            evidence.initialize(db, inputs, 'fixture', 0)
            rows = db.execute('SELECT input_hash,COUNT(DISTINCT split) FROM samples GROUP BY input_hash').fetchall()
            self.assertTrue(all(row[1] == 1 for row in rows))
        self.assertEqual(sum(len(v) for v in self.created['splits'].values()), 20)

    def test_final_holdout_cannot_be_recorded_before_freeze(self):
        self.candidate()
        with self.assertRaises(ValueError): self.observation('c', self.created['splits']['final'][0])
        with self.assertRaises(ValueError): self.op('freeze', candidate='c')
        self.observation('c', self.created['splits']['validation'][0], source='protocol_fixture')
        with self.assertRaises(ValueError): self.op('freeze', candidate='c')

    def test_freeze_closes_search_and_final_observations_are_immutable(self):
        self.candidate(); self.observation('c', self.created['splits']['validation'][0])
        self.assertTrue(self.op('freeze', candidate='c')['execute_final_permitted'])
        self.assertFalse(self.op('freeze', candidate='c')['execute_final_permitted'])
        with self.assertRaises(ValueError): self.candidate('another')
        with self.assertRaises(ValueError): self.observation('c', self.created['splits']['train'][0])
        index = self.created['splits']['final'][0]
        self.assertTrue(self.observation('c', index, command='final-record')['created'])
        self.assertFalse(self.observation('c', index, command='final-record')['created'])
        output = self.root / 'changed-output.json'; output.write_text('42')
        with self.assertRaises(ValueError):
            self.op('final-record', candidate='c', index=index, output=output, latency_ms=1.0, source='actual_execution', error=None)

    def test_changed_artifacts_and_symlink_state_are_refused(self):
        path = self.candidate(); path.write_text('{"changed":true}')
        with self.assertRaises(ValueError): self.op('candidate', id='c', family='future.extensible.family', artifact=path)
        with self.assertRaises(ValueError): self.observation('c', self.created['splits']['validation'][0])
        with self.assertRaises(ValueError): self.op('freeze', candidate='c')
        link = self.root / 'symlink'; link.symlink_to(self.state)
        with self.assertRaises(ValueError):
            with evidence.connect(link): pass
        self.assertEqual((self.state / 'evidence.sqlite3').stat().st_mode & 0o777, 0o600)

    def test_money_rejects_nan_negative_and_unrecordable_precision(self):
        for value in ('NaN', 'Infinity', '-1', '0.0000001'):
            with self.subTest(value=value), self.assertRaises(ValueError): evidence.money(value)
        self.assertEqual(evidence.money('0.000001'), 1)


class DistributionTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup); self.root = Path(temp.name)

    def test_installer_preserves_existing_changes_and_is_idempotent(self):
        parent = self.root / 'skills'
        self.assertEqual(install(parent)['status'], 'installed')
        self.assertEqual(install(parent)['status'], 'already_installed')
        target = parent / 'solve2ship/SKILL.md'; target.write_text('User-authored change')
        with self.assertRaises(ValueError): install(parent)
        self.assertEqual(target.read_text(), 'User-authored change')

    def test_symlink_install_target_is_refused(self):
        parent = self.root / 'skills'; parent.mkdir(); external = self.root / 'external'; external.mkdir()
        (parent / 'solve2ship').symlink_to(external)
        with self.assertRaises(ValueError): install(parent)
        self.assertEqual(list(external.iterdir()), [])

    def test_package_is_reproducible_allowlisted_and_manifest_checks_out(self):
        a = build(self.root / 'first.zip'); b = build(self.root / 'second.zip')
        self.assertEqual(a['sha256'], b['sha256'])
        import hashlib
        with zipfile.ZipFile(a['path']) as archive:
            self.assertEqual(set(archive.namelist()), {'solve2ship/' + name for name in FILES} | {'solve2ship/manifest.json'})
            manifest = json.loads(archive.read('solve2ship/manifest.json'))
            for name, digest in manifest['files_sha256'].items():
                self.assertEqual(hashlib.sha256(archive.read('solve2ship/' + name)).hexdigest(), digest)
            self.assertIn('solve2ship/LICENSE', archive.namelist())
            self.assertFalse(any(x in archive.namelist() for x in ('AGENTS.md', 'CODEX_CONTEXT.md', '.sts/evidence.sqlite3')))


if __name__ == '__main__': unittest.main()
