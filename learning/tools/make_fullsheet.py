# -*- coding: utf-8 -*-
"""全帧原尺寸拼图：把完整帧按原分辨率纵向堆叠（每张 n 帧），用于读文章正文 / 表格 / K 线细节。

用法：
    python make_fullsheet.py --dir "<full 帧目录>" --out "<输出目录>" [--per 2] [--pick 12] [--th 2.2]
        --pick  N  先去重，再等距抽 N 帧（默认全部去重帧）
"""
import argparse
import os
import signal
import sys

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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--per', type=int, default=2)
    ap.add_argument('--pick', type=int, default=0)
    ap.add_argument('--th', type=float, default=2.2)
    args = ap.parse_args()

    d = os.path.abspath(args.dir)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    files = sorted(f for f in os.listdir(d) if f.endswith('.png'))
    kept = vp.dedupe(files, d, th=args.th)
    if args.pick and len(kept) > args.pick:
        step = len(kept) / float(args.pick)
        kept = [kept[int(i * step)] for i in range(args.pick)]
    print('去重后 {} 帧 → 采用 {} 帧'.format(len(files), len(kept)))

    font = ImageFont.truetype(FONT, 24)
    per = args.per
    n = 0
    for si in range(0, len(kept), per):
        chunk = kept[si:si + per]
        ims = [Image.open(os.path.join(d, f)).convert('RGB') for f in chunk]
        w = max(i.width for i in ims)
        h = sum(i.height + 30 for i in ims)
        sheet = Image.new('RGB', (w, h), (245, 245, 245))
        dr = ImageDraw.Draw(sheet)
        yy = 0
        for f, im in zip(chunk, ims):
            sec = int(f.split('.')[0])
            dr.text((6, yy + 3), 't={}:{:02d}  (#{})'.format(sec // 60, sec % 60, f.split('.')[0]),
                    fill=(0, 0, 0), font=font)
            sheet.paste(im, (0, yy + 30))
            yy += im.height + 30
        p = os.path.join(out, 'full_{:02d}.png'.format(si // per + 1))
        if sheet.height > 1500:
            f2 = 1500.0 / sheet.height
            sheet = sheet.resize((int(sheet.width * f2), 1500), Image.LANCZOS)
        sheet.save(p)
        n += 1
    print('生成 {} 张 → {}'.format(n, out))


if __name__ == '__main__':
    main()
