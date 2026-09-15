# -*- coding: utf-8 -*-
"""Phase 1A 股票代码/名称规范化：纯确定性词典匹配（禁止 LLM 语义猜测）。

L1 计划 §2.1.2。两步:
  1. build_alias_dict()（一次性）: 从 yaoban-system/data/stock_names_full.json 构建
     反向词典 learning/labels/reference/stock_alias.json——清洗全角/\u0000/空格、
     剔除指数类、剥尾缀变体（圣阳股份→圣阳）、多 code 简称标 ambiguous。
  2. match_stock(raw)（运行时）: exact → prefix_unique → ambiguous → not_found。

CLI: python normalize_stock.py --build          # 构建/重建词典
     python normalize_stock.py "圣阳股"          # 单查询
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata

EVOALPHA = pathlib.Path(__file__).resolve().parent.parent.parent
# R2.8（2026-09-12）：改用只含个股的新表。旧表 stock_names_full.json 共 35086 条，
# 其中 83% 是债/基金/指数，且 `000004` 被写成「工业指数」（真正的 000004 = *ST国华）。
STOCK_NAMES = EVOALPHA / 'yaoban-system' / 'data' / 'stock_names_stocks.json'
ALIAS_JSON = EVOALPHA / 'learning' / 'labels' / 'reference' / 'stock_alias.json'

# 剥除的公司尾缀（生成别名变体；"圣阳股份"→"圣阳"，OCR 截断"圣阳股"同归一）
NAME_SUFFIXES = ('股份', '集团', '科技', '电子', '实业', '控股', '投资', '发展', '股')

# 指数/非个股特征（剔除出词典）
INDEX_MARKERS = ('指数', 'Ｂ股', 'A股指数', '等权', '债', '基本', '180', 'ETF', 'LOF', '基金')

# A 股权益代码前缀（与 yaoban-system `is_equity_code` 对齐）：
#   沪 60/68（含科创板）｜深 000/001/002/003（主板+中小）· 300/301（创业板）｜北 92（原 43x/83x 已统一到 920xxx）
# 剔除：01x-19x 债/基金、15x/16x/50x-58x 基金、200xxx·900xxx B股、399xxx·880xxx 指数/板块。
EQUITY_PREFIXES = ('60', '68', '000', '001', '002', '003', '300', '301', '92')


def norm_text(s: str) -> str:
    """清洗: 全角→半角、去 \u0000、去空格、NFKC 归一。"""
    s = unicodedata.normalize('NFKC', str(s))
    s = s.replace('\x00', '').replace(' ', '').replace('　', '')
    return s.strip()


def _is_index_like(name: str) -> bool:
    return any(m in name for m in INDEX_MARKERS)


def _is_equity_code(code: str) -> bool:
    return (len(code) == 6 and code.isdigit()
            and any(code.startswith(p) for p in EQUITY_PREFIXES))


def build_alias_dict(source: pathlib.Path = STOCK_NAMES,
                     out: pathlib.Path = ALIAS_JSON) -> dict:
    """构建反向词典 {name_norm: [codes]} + 别名变体 + ambiguous 标记。"""
    # 兼容两段式（{_meta, names}）与旧扁平结构
    _doc = json.loads(source.read_text(encoding='utf-8'))
    raw = _doc.get('names', _doc) if isinstance(_doc, dict) else {}
    main: dict[str, list[str]] = {}
    excluded = 0
    for code, name in raw.items():
        if code == '_meta':
            continue
        code = str(code).strip()
        if not _is_equity_code(code):
            continue
        n = norm_text(name)
        if not n or _is_index_like(n):
            excluded += 1
            continue
        if code not in main.setdefault(n, []):
            main[n].append(code)
    # 同名多 code（如沪深退市重用）保留; 简称多 code → ambiguous（调用方必须进 review_queue）

    # 别名变体: 剥尾缀。碰撞时合并 codes（宏昌电子+宏昌科技 → '宏昌'→2 codes→ambiguous）
    alias: dict[str, list[str]] = {}
    for n, codes in main.items():
        for suf in NAME_SUFFIXES:
            if n.endswith(suf) and len(n) > len(suf):
                stem = n[:-len(suf)]
                if len(stem) < 2:
                    break
                merged = sorted(set(alias.get(stem, [])) | set(codes))
                alias[stem] = merged
                break  # 只剥最长的一个尾缀

    ambiguous_names = sorted(n for n, c in main.items() if len(c) > 1) + \
                      sorted(n for n, c in alias.items() if len(c) > 1)

    doc = {
        '_meta': {
            'built_at': __import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds'),
            'source': str(source),
            'total_raw': len(raw),
            'total_names': len(main),
            'total_aliases': len(alias),
            'excluded_index_like': excluded,
            'ambiguous_names': ambiguous_names,
            'human_additions': {},
        },
        'names': main,
        'aliases': alias,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding='utf-8')
    return doc


def load_dict(path: pathlib.Path = ALIAS_JSON) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def match_stock(raw_text: str, dict_doc: dict | None = None) -> dict:
    """纯确定性匹配。返回 {code, name, match, alternatives}。

    match: exact(全名) | alias(别名变体) | prefix_unique(剥尾缀唯一前缀)
           | ambiguous(多命中→调用方必须进 review_queue) | not_found
    """
    doc = dict_doc or load_dict()
    names, aliases = doc['names'], doc.get('aliases', {})
    raw = norm_text(raw_text)
    if not raw:
        return {'code': None, 'name': None, 'match': 'not_found', 'alternatives': []}

    # 人工补充映射优先（review 队列沉淀的确认结果）
    human = doc.get('_meta', {}).get('human_additions', {})
    if raw in human:
        code = human[raw]
        return {'code': code, 'name': names.get(code, [None])[0] if isinstance(names.get(code), list) else names.get(code),
                'match': 'alias', 'alternatives': []}

    if raw in names:
        codes = names[raw]
        if len(codes) == 1:
            return {'code': codes[0], 'name': raw, 'match': 'exact', 'alternatives': []}
        return {'code': None, 'name': raw, 'match': 'ambiguous', 'alternatives': codes}
    if raw in aliases:
        codes = aliases[raw]
        if len(codes) == 1:
            code = codes[0]
            full = next((n for n, cs in names.items() if cs == [code]), raw)
            return {'code': code, 'name': full, 'match': 'alias', 'alternatives': []}
        return {'code': None, 'name': raw, 'match': 'ambiguous', 'alternatives': codes}

    # prefix_unique: 原文是某全名的前缀（OCR 截断，如"圣阳股"→"圣阳股份"）
    # 只认"原文 + 尾缀 ∈ 全名集合"或"全名以原文开头"的唯一命中
    candidates = [n for n in names if n.startswith(raw)] + \
                 [n for n in aliases if n.startswith(raw)]
    uniq_codes = sorted({c for n in candidates
                         for c in (names.get(n) or aliases.get(n) or [])})
    if len(uniq_codes) == 1:
        code = uniq_codes[0]
        full = next((n for n in names if code in names[n]), raw)
        return {'code': code, 'name': full, 'match': 'prefix_unique', 'alternatives': []}
    if len(uniq_codes) > 1:
        return {'code': None, 'name': raw, 'match': 'ambiguous', 'alternatives': uniq_codes}
    return {'code': None, 'name': raw, 'match': 'not_found', 'alternatives': []}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true', help='构建/重建反向词典')
    ap.add_argument('query', nargs='*', help='查询原始股票名')
    a = ap.parse_args(argv)
    if a.build:
        doc = build_alias_dict()
        m = doc['_meta']
        print(f"OK names={m['total_names']} aliases={m['total_aliases']} "
              f"excluded={m['excluded_index_like']} ambiguous={len(m['ambiguous_names'])} → {ALIAS_JSON}")
        return 0
    for q in a.query:
        print(json.dumps(match_stock(q), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    sys.exit(main())
