# -*- coding: utf-8 -*-
"""批次抽帧驱动：按关键字匹配视频 → 自适应定位 → 抽帧 → 去重 → 拼图 → 网格总览。

用法：
    python run_batch.py --work "<工作目录>" --batch 1 --pick "04-28" "06-05" "08-16" [--full]

产出：
    <work>/<tag>/sheet/sheet_XX.png     字幕带拼图（主要读图对象）
    <work>/<tag>/grid/grid_XX.png       完整帧网格总览
    <work>/<tag>/meta.json              元信息（含时长/分辨率/字幕带/张数）
    <work>/batch_<n>_manifest.json      批次清单
"""
import argparse
import json
import os
import re
import signal
import sys
import time

for _s in ('SIGINT', 'SIGBREAK', 'SIGTERM'):
    try:
        signal.signal(getattr(signal, _s), signal.SIG_IGN)
    except (AttributeError, ValueError, OSError):
        pass

if sys.stdout is not None:      # pythonw.exe（无控制台）下 sys.stdout 为 None
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import video_pipeline as vp  # noqa: E402

BASE = r'C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档\EvoAlpha'
SCAN = os.path.join(BASE, '选手学习资料', '妖板选手视频拆解', '_meta', 'library_scan.json')


class _Tee(object):
    """把 stdout 同时落到日志文件，避免长批次中断后输出丢失。"""

    def __init__(self, fp):
        self._fp = fp

    def write(self, s):
        self._fp.write(s)
        self._fp.flush()

    def flush(self):
        self._fp.flush()

    def isatty(self):
        return False


def slug(s, n=14):
    # ⚠️ 必须剔除半角 '%'：ffmpeg 的 image2 muxer 把它当序列占位符，
    # 输出路径含 '%' 时 ffmpeg 会静默不写文件且 rc=0（9/11 实测踩坑）。
    s = re.sub(r'[\\/:*?"<>|%\s]+', '', s)
    s = s.replace('\uff05', '')
    return s[:n]


def tag_of(rel, idx):
    name = os.path.basename(rel)
    date = re.search(r'(20\d{2})-(\d{2})-(\d{2})', name)
    d = '{}{}{}'.format(*date.groups()) if date else '00000000'
    title = re.sub(r'^20\d{2}-\d{2}-\d{2}\s*', '', name)
    title = re.sub(r'^\d{6}\s*', '', title)
    title = re.sub(r'\.mp4$', '', title, flags=re.I)
    return '{}_{:02d}_{}'.format(d, idx, slug(title, 14))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--batch', required=True)
    ap.add_argument('--pick', nargs='+', required=True)
    ap.add_argument('--full', action='store_true')
    ap.add_argument('--scan', default=SCAN)
    ap.add_argument('--sweep', action='store_true', help='全库定位体检（只定位不抽帧）')
    ap.add_argument('--log', default='', help='同时把输出落到该 utf-8 日志文件')
    args = ap.parse_args()

    if args.log:
        _lp = os.path.abspath(args.log)
        os.makedirs(os.path.dirname(_lp), exist_ok=True)
        sys.stdout = _Tee(open(_lp, 'w', encoding='utf-8', buffering=1))

    with open(args.scan, encoding='utf-8') as fp:
        rows = json.load(fp)

    work = os.path.abspath(args.work)
    os.makedirs(work, exist_ok=True)

    if args.sweep:
        tmp = os.path.join(work, '_sweep')
        os.makedirs(tmp, exist_ok=True)
        rpt = os.path.join(work, 'sweep_report.txt')
        lines, bad = [], []
        fp = open(rpt, 'w', encoding='utf-8', buffering=1)
        for i, r in enumerate(rows, 1):
            try:
                dur, w, h = vp.probe(r['full'])
            except Exception as e:  # noqa: BLE001
                fp.write('{:>3d}\tPROBE_FAIL\t{}\n'.format(i, e))
                continue
            frames = vp.sample_frames(r['full'], dur, tmp, n=10)
            res = vp.locate_subtitle(frames, h, w, return_score=True)
            name = os.path.basename(r['rel'])[:34]
            if res is None:
                fp.write('{:>3d}\tFAIL\t{}x{}\t{:.0f}s\t{}\n'.format(i, w, h, dur, name))
                bad.append((i, r['rel'], 'FAIL'))
                continue
            (y, ht), info = res
            pct = 100.0 * (y + ht) / h
            fp.write('{:>3d}\t{}\t{}x{}\t{:.0f}s\ty={:<4d}h={:<3d}底端{:.0f}%\t{:.3f}\t{}\n'.format(
                i, info['method'], w, h, dur, y, ht, pct, info['peak'], name))
            if info['method'] == 'grad' or pct < 90:
                bad.append((i, r['rel'], '{} y={} bot%={:.0f}'.format(info['method'], y, pct)))
        fp.write('\n=== 需人工复核 {} 条（grad 兜底 或 底端<90%）===\n'.format(len(bad)))
        for i, rel, why in bad:
            fp.write('{:>3d} {}  <{}>\n'.format(i, rel, why))
        fp.close()
        print('→ {}'.format(rpt))
        return

    picked, used = [], set()
    for key in args.pick:
        hit = None
        for r in rows:
            if key in r['rel'] and r['full'] not in used:
                hit = r
                break
        if hit is None:
            print('[未匹配] {}'.format(key))
            continue
        used.add(hit['full'])
        picked.append(hit)

    print('批次 {} 匹配到 {} 期'.format(args.batch, len(picked)))
    manifest = []
    for i, r in enumerate(picked, 1):
        tag = tag_of(r['rel'], i)
        out = os.path.join(work, tag)
        os.makedirs(out, exist_ok=True)
        src = r['full']
        meta = {'tag': tag, 'rel': r['rel'], 'batch': args.batch}
        try:
            dur, w, h = vp.probe(src)
            meta.update({'dur': round(dur, 2), 'res': '{}x{}'.format(w, h)})
            frames = vp.sample_frames(src, dur, out, n=12)
            res = vp.locate_subtitle(frames, h, w, return_score=True)
            if res is None:
                meta.update({'locate': 'FAIL', 'sub_kept': 0, 'sheets': 0})
                print('[{}] {}  {:.0f}s {}x{}  定位失败→完整帧兜底'.format(i, tag, dur, w, h))
            else:
                (y, ht), info = res
                n_sub = vp.extract_sub(src, os.path.join(out, 'sub'), y, ht)
                files = sorted(f for f in os.listdir(os.path.join(out, 'sub'))
                               if f.endswith('.png'))
                kept = vp.dedupe(files, os.path.join(out, 'sub'))
                n_sheet = vp.build_sheet(os.path.join(out, 'sub'), kept,
                                         os.path.join(out, 'sheet'), vp.SUB_FPS)
                meta.update({'locate': 'OK', 'method': info['method'], 'y': y, 'h': ht,
                             'peak_y': info['peak_y'],
                             'conf': round(info['conf'], 2), 'sub_raw': n_sub,
                             'sub_kept': len(kept), 'sheets': n_sheet})
                warn = ''
                if n_sub >= 60 and len(kept) / float(n_sub) < 0.08:
                    warn = '  ⚠️去重率仅{:.1f}%，疑似误检'.format(100.0 * len(kept) / n_sub)
                    meta['suspect'] = True
                print('[{}] {}  {:.0f}s {}x{}  {}带y={} h={}  抽{}→去重{}→{}图{}'.format(
                    i, tag, dur, w, h, info['method'], y, ht, n_sub, len(kept), n_sheet, warn))
            if args.full:
                n_full = vp.extract_full(src, os.path.join(out, 'full'))
                ffiles = sorted(f for f in os.listdir(os.path.join(out, 'full'))
                                if f.endswith('.png'))
                fkept = vp.dedupe(ffiles, os.path.join(out, 'full'), th=2.2)
                n_grid = vp.build_grid_sheet(os.path.join(out, 'full'), fkept,
                                             os.path.join(out, 'grid'))
                meta.update({'full_raw': n_full, 'full_kept': len(fkept), 'grids': n_grid})
                print('      完整帧 {} → 去重 {} → 网格 {} 张'.format(n_full, len(fkept), n_grid))
        except Exception as e:  # noqa: BLE001
            # 单期失败不拖垮整批：落盘原因后继续下一期
            meta.update({'locate': 'ERROR', 'error': str(e)[:400]})
            print('[{}] {}  异常→跳过本期: {}'.format(i, tag, str(e)[:220]))
        with open(os.path.join(out, 'meta.json'), 'w', encoding='utf-8') as fp:
            json.dump(meta, fp, ensure_ascii=False, indent=1)
        manifest.append(meta)

    mp = os.path.join(work, 'batch_{}_manifest.json'.format(args.batch))
    with open(mp, 'w', encoding='utf-8') as fp:
        json.dump(manifest, fp, ensure_ascii=False, indent=1)
    print('→ {}'.format(mp))


if __name__ == '__main__':
    main()
