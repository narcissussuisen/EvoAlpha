# -*- coding: utf-8 -*-
"""1A 标签层公共库测试：写保护 fail-closed + schema 契约。"""
from __future__ import annotations
import pathlib, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import label_common as lc

EVO = ROOT.parent


class WriteGuardTests(unittest.TestCase):
    def test_blacklist_ledger_raises(self):
        with self.assertRaises(lc.WriteGuardError):
            lc.guard_write(EVO / 'yaoban-system' / 'portfolio' / 'ledger.json')

    def test_blacklist_control_plane_raises(self):
        for rel in ('agents/coordinator.py', 'trading/x.md', 'evolution/x.md',
                    'cli.py'):
            with self.assertRaises(lc.WriteGuardError, msg=rel):
                lc.guard_write(EVO / rel)

    def test_whitelist_learning_passes(self):
        p = lc.guard_write(ROOT / 'labels' / 'seed' / 'labels.jsonl')
        self.assertTrue(str(p).startswith(str(ROOT)))

    def test_whitelist_text_material_passes(self):
        p = lc.guard_write(EVO / '选手学习资料' / '文字资料' / 'record.md')
        self.assertTrue('文字资料' in str(p))

    def test_outside_domains_raise(self):
        with self.assertRaises(lc.WriteGuardError):
            lc.guard_write(EVO / 'docs' / 'x.md')          # 文档域不可写
        with self.assertRaises(lc.WriteGuardError):
            lc.guard_write(pathlib.Path(tempfile.gettempdir()) / 'x.txt')  # 仓库外

    def test_safe_write_text_atomic_and_guarded(self):
        with tempfile.TemporaryDirectory() as td:
            # 白名单内的临时文件（模拟 learning/ 下）
            target = ROOT / 'labels' / 'audit' / '_test_guard.tmp'
            try:
                lc.safe_write_text(target, 'hello')
                self.assertEqual(target.read_text(encoding='utf-8'), 'hello')
            finally:
                target.unlink(missing_ok=True)
            # 黑名单写入必须 raise
            with self.assertRaises(lc.WriteGuardError):
                lc.safe_write_text(EVO / 'yaoban-system' / 'x.txt', 'bad')


class SchemaContractTests(unittest.TestCase):
    def test_kind_to_level_covers_all_levels(self):
        used = set(lc.KIND_TO_LEVEL.values())
        self.assertTrue(used.issubset(set(lc.EVIDENCE_LEVELS)))
        self.assertIn('E0', used)
        self.assertIn('E1', used)

    def test_numeric_ok_levels_e0_e1_e2(self):
        self.assertEqual(lc.NUMERIC_OK_LEVELS, ('E0', 'E1', 'E2'))

    def test_make_source_ref_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            lc.make_source_ref('llm_guess', 'x')  # 语义猜测禁止入 ref

    def test_make_source_ref_carries_level(self):
        ref = lc.make_source_ref('ocr_jsonl', 'a/b.jsonl', line_no=3)
        self.assertEqual(ref['evidence_level'], 'E1')
        self.assertEqual(ref['line_no'], 3)

    def test_label_evidence_level_takes_strongest(self):
        refs = [lc.make_source_ref('md', 'x.md'),
                lc.make_source_ref('png', 'y.png')]
        self.assertEqual(lc.label_evidence_level(refs), 'E0')

    def test_label_evidence_level_requires_refs(self):
        with self.assertRaises(ValueError):
            lc.label_evidence_level([])

    def test_make_label_id_format(self):
        self.assertEqual(lc.make_label_id('2026-04-17', 'idea_set', 3),
                         '20260417#idea_set#003')

    def test_label_types_match_blueprint(self):
        self.assertEqual(set(lc.LABEL_TYPES),
                         {'idea_set', 'execution', 'portfolio_snapshot', 'method_claim'})

    def test_five_checks_match_blueprint(self):
        self.assertEqual(set(lc.FIVE_CHECKS),
                         {'confidence', 'frame_traceback', 'code_normalized',
                          'time_boundary', 'cross_source'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
