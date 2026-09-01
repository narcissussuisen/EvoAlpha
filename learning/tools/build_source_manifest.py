# -*- coding: utf-8 -*-
"""Phase 1A-RO: 学习资料源清单 + SHA-256 + 去重 + 覆盖率报告（只读施工）。

蓝图依据: YAOBAN_AGENT_BASELINE_AND_PHASE1_BLUEPRINT.md §5.1/§9 Phase 1A
（只读部分已批准与 Phase 0 并行; 零生产账本/交易代码写入）。

三个资料源:
  desktop_videos      C:\\Users\\YZP\\Desktop\\妖板选手（82 个 MP4 原件, E0）
  learning_materials  EvoAlpha/选手学习资料（当日结构化资料 + 文字资料, E0/E2）
  methodology         EvoAlpha/妖板选手方法论拆解（OCR/帧/表格/报告, E1/E3; 排除环境目录）

产物: learning/manifests/source_manifest_<date>/
  manifest.jsonl   每文件一行 {source, path, size, mtime, sha256}
  summary.json     规模统计 + 跨源重复哈希分析（去重依据）
  coverage_report.md  人类可读覆盖率报告 v1（日期分布 + 已知缺口引用）

用法: python learning/tools/build_source_manifest.py [--skip-hash]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys
from collections import Counter, defaultdict

EVOALPHA = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_ROOT = EVOALPHA / 'learning' / 'manifests'

DESKTOP_VIDEOS = pathlib.Path(r'C:\Users\YZP\Desktop\妖板选手')
LEARNING = EVOALPHA / '选手学习资料'
METHODOLOGY = EVOALPHA / '妖板选手方法论拆解'

# methodology 源内排除（环境/缓存/损坏残留, 非学习资产）
METH_EXCLUDE_DIRS = {'ocrenv', 'ocrenv2', 'videoenv', '__pycache__',
                     'UsersYZPWorkBuddyClaw方法论与研究文档妖板选手方法论拆解dense_frames',
                     'new_frames', 'new_frames_ascii'}  # new_frames* 为空目录族
METH_EXCLUDE_SUBDIRS = {'venv', '__pycache__'}  # 任意层级
METH_EXCLUDE_SUFFIXES = {'.pyc'}

DATE_RE = re.compile(r'(20\d{2})[-_.年]?(\d{1,2})[-_.月]?(\d{1,2})')


def _extract_date(name: str):
    m = DATE_RE.search(name)
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (2020 <= y <= 2030 and 1 <= mo <= 12 and 1 <= d <= 31):
        return None
    return f'{y:04d}-{mo:02d}-{d:02d}'


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def collect(source: str, root: pathlib.Path):
    if not root.exists():
        return []
    out = []
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        rel_parts = p.relative_to(root).parts
        if any(part in METH_EXCLUDE_SUBDIRS for part in rel_parts) and source == 'methodology':
            continue
        if source == 'methodology':
            if rel_parts[0] in METH_EXCLUDE_DIRS:
                continue
            if p.suffix.lower() in METH_EXCLUDE_SUFFIXES:
                continue
        out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--skip-hash', action='store_true', help='只清点不哈希（快速）')
    args = ap.parse_args()

    run_id = dt.datetime.now().strftime('%Y%m%d_%H%M')
    out_dir = OUT_ROOT / f'source_manifest_{run_id}'
    out_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for source, root in (('desktop_videos', DESKTOP_VIDEOS),
                         ('learning_materials', LEARNING),
                         ('methodology', METHODOLOGY)):
        for p in collect(source, root):
            st = p.stat()
            entries.append({
                'source': source,
                'path': str(p),
                'name': p.name,
                'size': st.st_size,
                'mtime': dt.datetime.fromtimestamp(st.st_mtime).isoformat(timespec='seconds'),
                'sha256': '' if args.skip_hash else sha256_file(p),
            })

    manifest_path = out_dir / 'manifest.jsonl'
    with manifest_path.open('w', encoding='utf-8') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + '\n')

    # ---- 统计与去重 ----
    by_source = defaultdict(lambda: {'files': 0, 'bytes': 0})
    for e in entries:
        d = by_source[e['source']]
        d['files'] += 1
        d['bytes'] += e['size']

    dup_groups = []
    if not args.skip_hash:
        by_hash = defaultdict(list)
        for e in entries:
            if e['sha256']:
                by_hash[e['sha256']].append(e)
        for h, group in by_hash.items():
            if len(group) > 1:
                sources = sorted({g['source'] for g in group})
                dup_groups.append({'sha256': h[:16], 'count': len(group),
                                   'sources': sources,
                                   'wasted_bytes': sum(g['size'] for g in group[1:]),
                                   'sample': group[0]['name'][:60]})
        dup_groups.sort(key=lambda g: -g['wasted_bytes'])

    # ---- 覆盖率: 日期分布 ----
    mp4s = [e for e in entries if e['path'].lower().endswith('.mp4')]
    mp4_dates = Counter(_extract_date(e['name']) for e in mp4s)
    ocr_mds = [e for e in entries if pathlib.Path(e['path']).parent.name == 'ocr_text'
               and e['name'].endswith('.md')]
    ocr_dates = Counter(_extract_date(e['name']) for e in ocr_mds)
    ocr_nonempty = 0
    for e in ocr_mds:
        try:
            if pathlib.Path(e['path']).stat().st_size > 100:
                ocr_nonempty += 1
        except OSError:
            pass
    frames = [e for e in entries if '\\dense_frames\\' in e['path'] or '/dense_frames/' in e['path']]
    all_days = sorted((set(mp4_dates) | set(ocr_dates)) - {None})

    summary = {
        'run_id': run_id,
        'generated_at': dt.datetime.now().isoformat(timespec='seconds'),
        'skip_hash': args.skip_hash,
        'total_files': len(entries),
        'total_bytes': sum(e['size'] for e in entries),
        'by_source': dict(by_source),
        'dedup': {
            'duplicate_groups': len(dup_groups),
            'wasted_bytes_total': sum(g['wasted_bytes'] for g in dup_groups),
            'top10': dup_groups[:10],
        },
        'coverage': {
            'mp4_count': len(mp4s),
            'mp4_unique_dates': len([d for d in mp4_dates if d]),
            'mp4_date_range': [min(d for d in mp4_dates if d), max(d for d in mp4_dates if d)] if any(mp4_dates) else None,
            'ocr_md_count': len(ocr_mds),
            'ocr_md_nonempty_gt100b': ocr_nonempty,
            'ocr_unique_dates': len([d for d in ocr_dates if d]),
            'dense_frames': len(frames),
            'all_asset_dates': len(all_days),
        },
    }
    (out_dir / 'summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')

    # ---- 人类可读报告 ----
    cov = summary['coverage']
    lines = [
        '# 学习资料源覆盖率报告 v1（1A-RO 只读施工）', '',
        f'> 生成: {summary["generated_at"]} | 清单: manifest.jsonl（{len(entries)} 文件）',
        f'> 依据蓝图 §5.1 资产审计; 本报告为文件级覆盖, 标签级覆盖（7 组完整标签/28 净值点）',
        f'> 属 Phase 1A 正式施工范围, 引用蓝图 08-31 审计结论。', '',
        '## 1. 资产规模', '',
        '| 源 | 文件数 | 字节 | 说明 |', '|---|---|---|---|',
        f'| desktop_videos | {by_source["desktop_videos"]["files"]} | {by_source["desktop_videos"]["bytes"]:,} | E0 原始视频 |',
        f'| learning_materials | {by_source["learning_materials"]["files"]} | {by_source["learning_materials"]["bytes"]:,} | E0/E2 当日资料 |',
        f'| methodology | {by_source["methodology"]["files"]} | {by_source["methodology"]["bytes"]:,} | E1 结构化产物(排除环境) |',
        f'| **合计** | {len(entries)} | {summary["total_bytes"]:,} | |', '',
        '## 2. 视频日期覆盖', '',
        f'- MP4 总数 {cov["mp4_count"]}, 可解析日期 {cov["mp4_unique_dates"]} 个, 范围 {cov["mp4_date_range"]}',
        f'- OCR MD {cov["ocr_md_count"]} 份（非空 {cov["ocr_md_nonempty_gt100b"]}）, 唯一日期 {cov["ocr_unique_dates"]} 个',
        f'- dense_frames {cov["dense_frames"]} 帧',
        f'- 全部资产唯一天数 {cov["all_asset_dates"]}', '',
        '## 3. 跨源重复（去重依据）', '',
        f'- 重复组 {summary["dedup"]["duplicate_groups"]} 个, 冗余字节 {summary["dedup"]["wasted_bytes_total"]:,}',
    ]
    for g in dup_groups[:10]:
        lines.append(f'  - [{g["sha256"]}...] ×{g["count"]} ({"+".join(g["sources"])}) 冗余 {g["wasted_bytes"]:,}B — {g["sample"]}')
    lines += ['', '## 4. 已知缺口（蓝图 §5.1 审计, 待 1A 正式施工补齐）', '',
              '- 73 个日期中仅 7 组完整严格候选标签（12.3%）；2 组名单截断',
              '- 可解析净值点 28 天（38.4%），含 2 个周末伪点待剔除、3 个同日多值待处理',
              '- 分钟级发布时间仅 28/82 视频（34.1%）；零音频转写',
              '- 4 个视频完全未处理；3 张图片未 OCR；DOCX 未结构化',
              '- 1A 后续: ASR 补齐、10 个未处理视频、自动校对管线（五项检查）', '']
    (out_dir / 'coverage_report.md').write_text('\n'.join(lines), encoding='utf-8')

    print(f'OK files={len(entries)} bytes={summary["total_bytes"]} '
          f'dup_groups={summary["dedup"]["duplicate_groups"]} → {out_dir}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
