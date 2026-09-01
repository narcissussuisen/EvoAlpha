# -*- coding: utf-8 -*-
"""normalize_stock 测试：纯确定性匹配契约（禁止 LLM 语义猜测的机械保证）。"""
from __future__ import annotations
import pathlib, sys, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import normalize_stock as ns

ALIAS = ROOT / 'labels' / 'reference' / 'stock_alias.json'


@unittest.skipUnless(ALIAS.exists(), '词典未构建（先跑 --build）')
class NormalizeStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = ns.load_dict()

    def test_dict_is_equity_only(self):
        # 全部 code 为 A 股权益前缀（0/3/6 开头）
        for codes in self.doc['names'].values():
            for c in codes:
                self.assertTrue(c[0] in ('0', '3', '6'), f'非权益代码混入: {c}')
        self.assertGreater(len(self.doc['names']), 5000)

    def test_exact_match(self):
        r = ns.match_stock('圣阳股份', self.doc)
        self.assertEqual((r['code'], r['match']), ('002580', 'exact'))
        r = ns.match_stock('平安银行', self.doc)  # 债券同名条目已剔除
        self.assertEqual((r['code'], r['match']), ('000001', 'exact'))

    def test_prefix_unique_for_ocr_truncation(self):
        # OCR 截断场景: "圣阳股"/"新宝股" → 唯一前缀命中
        r = ns.match_stock('圣阳股', self.doc)
        self.assertEqual((r['code'], r['match']), ('002580', 'prefix_unique'))
        r = ns.match_stock('新宝股', self.doc)
        self.assertEqual((r['code'], r['match']), ('002705', 'prefix_unique'))

    def test_alias_collision_is_ambiguous(self):
        # 宏昌电子(603002) + 宏昌科技(301008) → '宏昌' 必须 ambiguous（碰撞合并）
        r = ns.match_stock('宏昌', self.doc)
        self.assertEqual(r['match'], 'ambiguous')
        self.assertCountEqual(r['alternatives'], ['301008', '603002'])

    def test_not_found_for_unknown(self):
        r = ns.match_stock('不存在的股票名XYZ', self.doc)
        self.assertEqual(r['match'], 'not_found')
        self.assertIsNone(r['code'])

    def test_fullwidth_and_null_cleaned(self):
        # 全角/空格/控制字符清洗后仍能精确匹配
        r = ns.match_stock(' 圣阳股份　', self.doc)
        self.assertEqual((r['code'], r['match']), ('002580', 'exact'))

    def test_human_addition_mapping(self):
        doc = {'names': {'002580': ['圣阳股份']},
               'aliases': {},
               '_meta': {'human_additions': {'烽火通信Z': '600498'}}}
        r = ns.match_stock('烽火通信Z', doc)
        self.assertEqual(r['code'], '600498')

    def test_no_llm_semantic_guess(self):
        # 语义猜测禁止的机械保证: 模块源码无任何 LLM/网络调用
        src = (ROOT / 'tools' / 'normalize_stock.py').read_text(encoding='utf-8')
        for banned in ('openai', 'requests', 'urllib', 'http', 'deepseek', 'anthropic'):
            self.assertNotIn(banned, src.lower(), f'规范化层禁止 {banned} 调用')


if __name__ == '__main__':
    unittest.main(verbosity=2)
