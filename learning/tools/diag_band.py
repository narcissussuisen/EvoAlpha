# -*- coding: utf-8 -*-
"""字幕带诊断：打印下半幅逐行特征，人工判定字幕带真实位置。

特征（跨 12 帧中位数）：
  grad  行内水平梯度均值（笔画密度）
  bright/ink  亮/暗像素占比
  warm  暖色像素占比（R 明显大于 B，用于识别黄/橙底字幕条）
  flat  该行是否恒定（黑边/白底）

用法：python diag_band.py --src "<video>" [--lo 0.55]
"""
import argparse
import os
import sys
import signal
import tempfile

for _s in ('SIGINT', 'SIGBREAK', 'SIGTERM'):
    try:
        signal.signal(getattr(signal, _s), signal.SIG_IGN)
    except (AttributeError, ValueError, OSError):
        pass

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
import video_pipeline as vp  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--lo', type=float, default=0.55)
    ap.add_argument('--stride', type=int, default=4)
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    dur, w, h = vp.probe(src)
    work = os.path.join(tempfile.gettempdir(), 'diagband')
    frames = vp.sample_frames(src, dur, work, n=12)

    gs, bs, ks, ws = [], [], [], []
    for p in frames:
        im = Image.open(p).convert('RGB')
        a = np.asarray(im, dtype=np.float32)
        g = a.mean(axis=2)
        gs.append(np.abs(np.diff(g, axis=1)).mean(axis=1))
        bs.append((g > 170).mean(axis=1))
        ks.append((g < 85).mean(axis=1))
        warm = (a[:, :, 0] > 140) & (a[:, :, 0] > a[:, :, 2] + 55) & (a[:, :, 1] > a[:, :, 2] + 25)
        ws.append(warm.mean(axis=1))
    G = np.median(np.stack(gs), 0)
    B = np.median(np.stack(bs), 0)
    K = np.median(np.stack(ks), 0)
    W = np.median(np.stack(ws), 0)

    print('{}  {}x{}  {:.0f}s'.format(os.path.basename(src)[:50], w, h, dur))
    y0 = int(h * args.lo)
    print('区域 y[{}:{}]'.format(y0, h))
    print('{:>5s} {:>8s} {:>8s} {:>8s} {:>8s}'.format('y', 'grad', 'bright', 'ink', 'warm'))
    for y in range(y0, h, args.stride):
        star = ''
        print('{:>5d} {:>8.2f} {:>8.4f} {:>8.4f} {:>8.4f} {}'.format(
            y, G[y], B[y], K[y], W[y], star))
    for nm, arr in (('grad', G), ('warm', W), ('bright', B)):
        seg = arr[y0:]
        ty = y0 + int(np.argmax(seg))
        print('  argmax {:<7s} -> y={}  val={:.4f}'.format(nm, ty, arr[ty]))
    # 暖色带的整体范围
    mask = W > 0.02
    seg = mask[y0:]
    runs = []
    cur = -1
    for i, v in enumerate(seg):
        if v and cur < 0:
            cur = i
        elif not v and cur >= 0:
            runs.append((y0 + cur, y0 + i - 1)); cur = -1
    if cur >= 0:
        runs.append((y0 + cur, h - 1))
    print('  暖色带 (warm>2%)：' + (', '.join('{}-{}'.format(a, b) for a, b in runs) or '无'))


if __name__ == '__main__':
    main()
