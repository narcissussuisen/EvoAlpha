# -*- coding: utf-8 -*-
"""字幕带定位标定：对若干代表视频跑定位，渲染「整帧标注 + 原生尺度裁切」对照图，
供人工视觉核验（判断红框是否正好套住烧录字幕）。

用法：
    python calib_locate.py --root "<妖板选手目录>" --out "<标定输出目录>" --pick "04-28" "06-05" ...
"""
import argparse
import glob
import json
import os
import sys
import signal
import time

for _s in ('SIGINT', 'SIGBREAK', 'SIGTERM'):
    try:
        signal.signal(getattr(signal, _s), signal.SIG_IGN)
    except (AttributeError, ValueError, OSError):
        pass

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import video_pipeline as vp  # noqa: E402

FONT = r'C:\Windows\Fonts\msyh.ttc'
PANEL_W = 340
CROP_W = 700


def pick_videos(root, picks):
    idx = os.path.join(root, '..', '..', '..', '妖板选手视频拆解', '_meta', 'library_scan.json')
    rows = None
    cand = os.path.join(os.path.dirname(root), '..', '..', '妖板选手视频拆解', '_meta', 'library_scan.json')
    for p in (cand, idx):
        if os.path.exists(p):
            with open(p, encoding='utf-8') as fp:
                rows = json.load(fp)
            break
    if rows is None:
        rows = []
        for dirpath, _d, files in os.walk(root):
            for fn in files:
                if fn.lower().endswith('.mp4'):
                    rows.append({'full': os.path.join(dirpath, fn), 'rel': fn})
    out, used = [], set()
    for key in picks:
        for r in rows:
            if key in r['rel'] or key in os.path.basename(r['full']):
                if r['full'] in used:
                    continue
                out.append(r)
                used.add(r['full'])
                break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--pick', nargs='+', required=True)
    ap.add_argument('--rows-per-sheet', type=int, default=6)
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    outdir = os.path.abspath(args.out)
    os.makedirs(outdir, exist_ok=True)

    videos = pick_videos(root, args.pick)
    print('待标定 {} 个'.format(len(videos)))

    items = []
    for v in videos:
        src = v['full']
        try:
            dur, w, h = vp.probe(src)
        except Exception as e:  # noqa: BLE001
            print('SKIP {} {}'.format(os.path.basename(src)[:40], e))
            continue
        work = os.path.join(outdir, '_probe')
        frames = vp.sample_frames(src, dur, work, n=12)
        r = vp.locate_subtitle(frames, h, w, return_score=True)
        mid = frames[len(frames) // 2]
        im = Image.open(mid).convert('RGB')
        if r is None:
            print('FAIL  {}x{}  {}'.format(w, h, os.path.basename(src)[:44]))
            items.append((im, None, w, h, os.path.basename(src), None))
        else:
            (y, ht), info = r
            print('OK    {}  {}x{}  y={:<4d} h={:<3d} peak_y={:<4d} peak={:.2f} conf={:.2f}  {}'.format(
                info['method'], w, h, y, ht, info['peak_y'], info['peak'], info['conf'],
                os.path.basename(src)[:40]))
            items.append((im, (y, ht), w, h, os.path.basename(src), info))

    # 渲染对照图
    font = ImageFont.truetype(FONT, 20)
    font_b = ImageFont.truetype(FONT, 24)
    per = args.rows_per_sheet
    sheet_i = 0
    for si in range(0, len(items), per):
        chunk = items[si:si + per]
        rows_img = []
        for (im, loc, w, h, name, info) in chunk:
            sc = PANEL_W / float(w)
            ph = int(h * sc)
            panel = im.resize((PANEL_W, ph), Image.LANCZOS)
            dr = ImageDraw.Draw(panel)
            if loc:
                y, ht = loc
                dr.rectangle([0, int(y * sc), PANEL_W - 1, int((y + ht) * sc)],
                             outline=(255, 0, 0), width=2)
            else:
                dr.rectangle([2, 2, PANEL_W - 3, ph - 3], outline=(0, 128, 255), width=2)
            # 原生尺度裁切
            if loc:
                y, ht = loc
                crop = im.crop((0, max(0, y - 6), w, min(h, y + ht + 6)))
            else:
                crop = im.crop((0, int(h * 0.5), w, h))
            csc = min(1.0, CROP_W / float(crop.width))
            crop = crop.resize((int(crop.width * csc), int(crop.height * csc)), Image.LANCZOS)
            row_h = max(ph, crop.height)
            row = Image.new('RGB', (PANEL_W + CROP_W + 24, row_h + 6), (250, 250, 250))
            row.paste(panel, (4, 2))
            row.paste(crop, (PANEL_W + 20, 2))
            dr2 = ImageDraw.Draw(row)
            tag = '{}x{}'.format(w, h) + ('  y={} h={}'.format(loc[0], loc[1]) if loc else '  FAIL')
            dr2.text((PANEL_W + 20, row_h - 26 if crop.height < row_h - 26 else 2),
                     tag, fill=(0, 0, 0), font=font)
            dr2.text((4, row_h - 24 if row_h - 24 > ph else ph - 24),
                     name[:38], fill=(60, 60, 60), font=font)
            rows_img.append(row)
        total_h = sum(r.height + 8 for r in rows_img) + 30
        sheet = Image.new('RGB', (PANEL_W + CROP_W + 30, total_h), (255, 255, 255))
        dr = ImageDraw.Draw(sheet)
        dr.text((6, 4), '左=整帧(红框=检出字幕带)  右=原生尺度裁切', fill=(0, 0, 0), font=font_b)
        yy = 30
        for r in rows_img:
            sheet.paste(r, (2, yy))
            yy += r.height + 8
        if sheet.height > 2600:
            f = 2600.0 / sheet.height
            sheet = sheet.resize((int(sheet.width * f), 2600), Image.LANCZOS)
        p = os.path.join(outdir, 'calib_{:02d}.png'.format(si // per + 1))
        sheet.save(p)
        print('→ {}'.format(p))
        sheet_i += 1


if __name__ == '__main__':
    main()
