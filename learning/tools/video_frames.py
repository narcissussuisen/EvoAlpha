# -*- coding: utf-8 -*-
"""
视频抽帧工具（EvoAlpha 选手研究）

两种模式：
  1) 单帧序列：--interval 8  每个视频按固定间隔存 jpg
  2) 拼图：    --sheet 3x3 --interval 6  把连续帧拼成网格图，每帧左上角标注时间戳

用法：
    python video_frames.py --match "2026-09-03" --interval 8
    python video_frames.py --match "2026-09-03" --sheet 2x2 --interval 5
"""
import argparse
import os
import sys
import time

import av
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding='utf-8')

VID_DIR = (r'C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档\EvoAlpha'
           r'\选手学习资料\人工录入资料\视频资料')
OUT_ROOT = r'C:\Users\YZP\AppData\Local\Temp\vframes'


def fmt_ts(sec):
    m = int(sec // 60)
    s = int(sec % 60)
    return '{}:{:02d}'.format(m, s)


def grab(video_path, interval, out_dir, tag):
    """按间隔抽帧，返回 [(t, PIL.Image)]"""
    frames = []
    with av.open(video_path) as c:
        st = c.streams.video[0]
        st.thread_type = 'AUTO'
        tb = st.time_base
        nxt = 0.0
        max_w = 0
        for fr in c.decode(st):
            if fr.pts is None:
                continue
            t = float(fr.pts * tb)
            if t + 1e-6 < nxt:
                continue
            img = fr.to_image()
            frames.append((t, img))
            max_w = max(max_w, img.width)
            nxt = t + interval
    return frames


def make_sheets(frames, cols, rows, out_dir, tag):
    per = cols * rows
    paths = []
    for i in range(0, len(frames), per):
        chunk = frames[i:i + per]
        if not chunk:
            continue
        w, h = chunk[0][1].size
        sheet = Image.new('RGB', (w * cols, h * rows), (0, 0, 0))
        d = ImageDraw.Draw(sheet)
        for j, (t, img) in enumerate(chunk):
            r, cc = divmod(j, cols)
            sheet.paste(img, (cc * w, r * h))
            d.rectangle([cc * w, r * h, cc * w + 92, r * h + 26], fill=(0, 0, 0))
            d.text((cc * w + 6, r * h + 6), fmt_ts(t), fill=(255, 255, 0))
        p = os.path.join(out_dir, '{}_sheet{:02d}.jpg'.format(tag, i // per + 1))
        sheet.save(p, quality=86)
        paths.append(p)
    return paths


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--match', default='')
    ap.add_argument('--interval', type=float, default=8.0)
    ap.add_argument('--sheet', default='')
    ap.add_argument('--out', default=OUT_ROOT)
    args = ap.parse_args()

    pats = [p.strip() for p in args.match.split(',') if p.strip()]
    files = sorted(
        f for f in os.listdir(VID_DIR)
        if f.lower().endswith('.mp4') and (not pats or any(p in f for p in pats))
    )
    if not files:
        print('无匹配视频')
        return

    cols = rows = 0
    if args.sheet:
        cols, rows = (int(x) for x in args.sheet.lower().split('x'))

    for fn in files:
        tag = fn.split()[0].replace('-', '')
        out_dir = os.path.join(args.out, tag)
        os.makedirs(out_dir, exist_ok=True)
        t0 = time.time()
        frames = grab(os.path.join(VID_DIR, fn), args.interval, out_dir, tag)
        if cols:
            paths = make_sheets(frames, cols, rows, out_dir, tag)
            print('[{}] {} 帧 -> {} 张拼图 ({:.1f}s)'.format(
                tag, len(frames), len(paths), time.time() - t0))
            for p in paths:
                print('   ', p)
        else:
            paths = []
            for t, img in frames:
                p = os.path.join(out_dir, '{}_{:04d}s.jpg'.format(tag, int(t)))
                img.save(p, quality=86)
                paths.append(p)
            print('[{}] {} 帧 -> {} ({:.1f}s)'.format(
                tag, len(frames), out_dir, time.time() - t0))


if __name__ == '__main__':
    main()
