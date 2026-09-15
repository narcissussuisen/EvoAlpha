# -*- coding: utf-8 -*-
"""盘点妖板选手视频库：时长 / 分辨率 / 体积，输出 JSON + 可读清单。

用法：
    python scan_library.py --root "<妖板选手目录>" --out "<输出目录>"
"""
import argparse
import json
import os
import sys
import signal
import time
from collections import Counter, defaultdict

for _s in ('SIGINT', 'SIGBREAK', 'SIGTERM'):
    try:
        signal.signal(getattr(signal, _s), signal.SIG_IGN)
    except (AttributeError, ValueError, OSError):
        pass

sys.stdout.reconfigure(encoding='utf-8')


def probe(src):
    import av
    with av.open(src) as c:
        dur = float(c.duration or 0) / av.time_base
        vs = c.streams.video[0]
        w, h = vs.codec_context.width, vs.codec_context.height
    return dur, w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    outdir = os.path.abspath(args.out)
    os.makedirs(outdir, exist_ok=True)

    rows = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if not fn.lower().endswith('.mp4'):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            try:
                dur, w, h = probe(full)
                err = ''
            except Exception as e:  # noqa: BLE001
                dur, w, h, err = 0.0, 0, 0, repr(e)[:200]
            rows.append({
                'rel': rel,
                'full': full,
                'size': os.path.getsize(full),
                'dur': round(dur, 2),
                'w': w, 'h': h,
                'res': '{}x{}'.format(w, h),
                'err': err,
                'group': os.path.dirname(rel) or '.',
            })

    rows.sort(key=lambda r: r['rel'])
    with open(os.path.join(outdir, 'library_scan.json'), 'w', encoding='utf-8') as fp:
        json.dump(rows, fp, ensure_ascii=False, indent=1)

    total_dur = sum(r['dur'] for r in rows)
    total_sz = sum(r['size'] for r in rows)
    res_cnt = Counter(r['res'] for r in rows)
    grp_cnt = Counter(r['group'] for r in rows)
    errs = [r for r in rows if r['err']]

    lines = []
    lines.append('# 妖板选手视频库盘点')
    lines.append('')
    lines.append('- 期数：**{}**'.format(len(rows)))
    lines.append('- 总时长：**{:.1f} 分钟**（{:.2f} 小时）'.format(total_dur / 60.0, total_dur / 3600.0))
    lines.append('- 总体积：**{:.1f} MB**'.format(total_sz / 1048576.0))
    lines.append('- 分辨率种类：**{}**'.format(len(res_cnt)))
    lines.append('- 解析失败：{}'.format(len(errs)))
    lines.append('')
    lines.append('## 目录分布')
    lines.append('')
    lines.append('| 子目录 | 期数 |')
    lines.append('|---|---|')
    for g, c in sorted(grp_cnt.items()):
        lines.append('| `{}` | {} |'.format(g, c))
    lines.append('')
    lines.append('## 分辨率分布')
    lines.append('')
    lines.append('| 分辨率 | 期数 | 占比 | 画幅判定 |')
    lines.append('|---|---|---|---|')
    for res, c in sorted(res_cnt.items(), key=lambda kv: -kv[1]):
        w, h = (int(x) for x in res.split('x'))
        ar = w / float(h) if h else 0
        kind = '横屏' if ar > 1.15 else ('正方形' if ar > 0.9 else '竖屏')
        lines.append('| {} | {} | {:.0f}% | {} |'.format(res, c, 100.0 * c / len(rows), kind))
    lines.append('')
    lines.append('## 逐期清单')
    lines.append('')
    lines.append('| # | 子目录 | 文件名 | 时长(s) | 分辨率 | MB |')
    lines.append('|---|---|---|---|---|---|')
    for i, r in enumerate(rows, 1):
        lines.append('| {} | `{}` | {} | {:.0f} | {} | {:.1f} |'.format(
            i, r['group'], r['rel'].replace('\\', '/'), r['dur'], r['res'], r['size'] / 1048576.0))
    if errs:
        lines.append('')
        lines.append('## 解析失败')
        lines.append('')
        for r in errs:
            lines.append('- `{}` → {}'.format(r['rel'], r['err']))

    with open(os.path.join(outdir, 'library_scan.md'), 'w', encoding='utf-8') as fp:
        fp.write('\n'.join(lines) + '\n')

    print('期数={} 总时长={:.1f}min 分辨率种类={} 失败={}'.format(
        len(rows), total_dur / 60.0, len(res_cnt), len(errs)))
    print('→ {}'.format(os.path.join(outdir, 'library_scan.md')))
    for res, c in sorted(res_cnt.items(), key=lambda kv: -kv[1]):
        print('  {:12s} x{}'.format(res, c))


if __name__ == '__main__':
    main()
