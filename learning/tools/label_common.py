# -*- coding: utf-8 -*-
"""Phase 1A 标签层公共库：schema 常量 + 写保护 + 证据等级 + source_ref 构造。

蓝图依据: YAOBAN_AGENT_BASELINE_AND_PHASE1_BLUEPRINT.md §5.2/§5.4/§9 Phase 1A
L1 计划: blazing-beacon-darwin §2.0/§2.1.1

零生产写入的第一道防线（fail-closed）:
    guard_write(path) —— resolve 后路径必须在白名单内，黑名单直接 raise。
    所有 1A 工具的文件写操作必须经过本函数。
"""
from __future__ import annotations

import json
import pathlib
import datetime as dt

EVOALPHA = pathlib.Path(__file__).resolve().parent.parent.parent

# ---- 写保护：白名单（1A 施工唯一允许写入的域） ----
WRITE_WHITELIST = [
    EVOALPHA / 'learning',
    EVOALPHA / '选手学习资料' / '文字资料',
    EVOALPHA / '妖板选手方法论拆解' / 'transcripts',  # ASR 产物域（批次3）
]
# 黑名单（生产与控制平面——命中即违规）
WRITE_BLACKLIST = [
    EVOALPHA / 'yaoban-system',
    EVOALPHA / 'agents',
    EVOALPHA / 'trading',
    EVOALPHA / 'evolution',
    EVOALPHA / 'risk',
    EVOALPHA / 'cli.py',
]

# ---- 证据等级（蓝图 §5.2）----
EVIDENCE_LEVELS = ('E0', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6')
# 数值字段只接受的可回溯等级
NUMERIC_OK_LEVELS = ('E0', 'E1', 'E2')
# source_refs.kind → 证据等级映射（溯源指针契约）
KIND_TO_LEVEL = {
    'mp4': 'E0', 'png': 'E0', 'jpg': 'E0',
    'ocr_jsonl': 'E1', 'md': 'E1', 'transcript': 'E1',
    'docx_md': 'E2',
    'video_analysis': 'E3',       # 标题级——仅线索不可单独成正式标签
    'player_log': 'E4', 'table': 'E4',
    'library_note': 'E5',
    'old_code': 'E6',
}
# 语义冲突裁决顺序（蓝图 §5.2，与 E 等级正交）
SEMANTIC_ORDER = ['execution_evidence', 'contemporaneous_quote',
                  'later_summary', 'old_code']

# ---- 标签类型（蓝图 §5.4）----
LABEL_TYPES = ('idea_set', 'execution', 'portfolio_snapshot', 'method_claim')
LABEL_STATUS = ('candidate', 'verified', 'review_queue', 'disputed', 'superseded')

# ---- 自动校对五项检查（蓝图 §9 1A；1A-formal 实装）----
FIVE_CHECKS = ('confidence', 'frame_traceback', 'code_normalized',
               'time_boundary', 'cross_source')

# 置信度阈值（首版锁定；改动需 config 版本号）
CONF_THRESHOLD_NUMERIC = 0.90   # 数值字段行
CONF_THRESHOLD_TEXT = 0.80      # 文本行
CROSS_SOURCE_REL_TOL = 0.005    # 跨源数值冲突线 0.5%


class WriteGuardError(PermissionError):
    """1A 施工写保护违规（fail-closed）。"""


def guard_write(path) -> pathlib.Path:
    """写保护闸门：白名单域放行，黑名单/域外 raise WriteGuardError。"""
    p = pathlib.Path(path).resolve()
    for black in WRITE_BLACKLIST:
        try:
            p.relative_to(black)
        except ValueError:
            continue
        raise WriteGuardError(f'1A 施工禁止写入生产/控制平面: {p}')
    for white in WRITE_WHITELIST:
        try:
            p.relative_to(white)
            return p
        except ValueError:
            continue
    raise WriteGuardError(f'1A 施工写路径不在白名单域: {p}（白名单: learning/, 选手学习资料/文字资料/, transcripts/）')


def safe_write_text(path, text: str, encoding: str = 'utf-8') -> pathlib.Path:
    """经写保护的文本落盘（原子写）。"""
    p = guard_write(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f'{p.name}.{__import__("os").getpid()}.tmp')
    tmp.write_text(text, encoding=encoding)
    __import__("os").replace(tmp, p)
    return p


def safe_write_jsonl(path, rows: list[dict], mode: str = 'a') -> pathlib.Path:
    """经写保护的 JSONL 追加/覆写。"""
    p = guard_write(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open(mode, encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n')
    return p


def make_label_id(trade_date: str, label_type: str, seq: int) -> str:
    return f'{trade_date.replace("-", "")}#{label_type}#{seq:03d}'


def make_source_ref(kind: str, path: str, **extra) -> dict:
    """构造溯源指针。kind 必须在 KIND_TO_LEVEL 内（防止未知等级标签）。"""
    if kind not in KIND_TO_LEVEL:
        raise ValueError(f'未知 source_ref kind: {kind}（合法: {sorted(KIND_TO_LEVEL)}）')
    ref = {'kind': kind, 'path': path, 'evidence_level': KIND_TO_LEVEL[kind]}
    ref.update({k: v for k, v in extra.items() if v is not None})
    return ref


def label_evidence_level(source_refs: list[dict]) -> str:
    """多源引用取最可回溯等级（E0 最强）。"""
    if not source_refs:
        raise ValueError('label 必须至少携带一个 source_ref')
    levels = [r.get('evidence_level') or KIND_TO_LEVEL.get(r.get('kind', ''), 'E6')
              for r in source_refs]
    return min(levels, key=lambda l: EVIDENCE_LEVELS.index(l))


def now_iso() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')
