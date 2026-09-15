# -*- coding: utf-8 -*-
"""
妖板选手视频抽帧管线（EvoAlpha 选手研究）

适配 26 种分辨率的自适应字幕带定位 + 抽帧 + 去重 + 拼图。
**不做语音转写**（视频自带烧录字幕，抽帧即可全文取证）。

用法：
    python video_pipeline.py --src "<video.mp4>" --out "<dir>" --tag 20260428
    python video_pipeline.py --src "<video.mp4>" --probe-only
    python video_pipeline.py --src "<video.mp4>" --out "<dir>" --tag X --manual-y 628 --manual-h 84

流程：
    1. probe      → 时长 / 分辨率
    2. locate     → 采样 12 帧，逐行算水平梯度，取帧间中位数，
                    在下半幅找"稳定高梯度带"= 字幕带（字幕位置固定、笔画高频）
    3. extract    → 字幕带 fps=2（保证不漏句）+ 完整帧 fps=1（看 K 线/表格）
    4. dedupe     → 相邻帧平均绝对差去重
    5. sheet      → 纵向拼图，每张 ≤18 条（超过会在读图侧被降采样导致字幕发虚）

保命设计：
    顶部忽略 SIGINT/SIGBREAK/SIGTERM，避免宿主超时强杀连带子进程。
"""
import argparse
import os
import signal
import subprocess
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

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FFMPEG = r'F:\ffmpeg.exe'
FONT_PATH = r'C:\Windows\Fonts\msyh.ttc'

# ⚠️⚠️ Windows 弹窗根因修复：不指定 CREATE_NO_WINDOW 时，若父进程没有 console
# （被 GUI / 工具宿主启动的情形），Windows 会为**每一个**子进程新建一个控制台窗口。
# 抽帧一次要调几百次 ffmpeg → 满屏 cmd 弹窗。必须显式加此标志。
CREATE_NO_WINDOW = 0x08000000 if os.name == 'nt' else 0
if not os.path.exists(FONT_PATH):
    FONT_PATH = r'C:\Windows\Fonts\simhei.ttf'

PER_SHEET = 18      # 每张拼图条数上限（会被 build_sheet 按裁切高度自适应下调/上调）
SHEET_TARGET_H = 1400   # 拼图目标总高（超过会在读图侧被降采样导致字幕发虚）
SUB_FPS = 2         # 字幕带抽帧密度
FULL_FPS = 1        # 完整帧抽帧密度
DIFF_TH = 1.6       # 去重阈值（平均绝对差）


def log(msg):
    print('[{}] {}'.format(time.strftime('%H:%M:%S'), msg), flush=True)


def run(cmd, expect=None):
    """执行 ffmpeg。

    ⚠️ **输出路径含半角 '%' 会静默失败**（实测确认）：ffmpeg 的 image2 muxer
    把 '%' 当序列占位符解析，遇到非法 pattern 时既不写文件、也不报错，
    returncode 仍为 0。因此凡有确定预期产出的调用，一律传 expect 做硬校验，
    杜绝"rc=0 却什么都没生成"的静默崩溃。
    """
    p = subprocess.run(cmd, capture_output=True, creationflags=CREATE_NO_WINDOW)
    if p.returncode != 0:
        raise RuntimeError('ffmpeg failed: {}'.format(
            p.stderr.decode('utf-8', 'ignore')[-500:]))
    if expect:
        missing = [e for e in expect if not os.path.exists(e)]
        if missing:
            raise RuntimeError(
                'ffmpeg rc=0 但未产出文件（疑似输出路径含 % 等特殊字符）: {} | tail={}'.format(
                    [os.path.basename(m) for m in missing[:3]], cmd[-2:]))
    return p


def probe(src):
    import av
    with av.open(src) as c:
        dur = float(c.duration or 0) / av.time_base
        vs = c.streams.video[0]
        w, h = vs.codec_context.width, vs.codec_context.height
    return dur, w, h


def sample_frames(src, dur, workdir, n=12):
    """均匀抽 n 帧用于字幕带定位。"""
    d = os.path.join(workdir, '_sample')
    os.makedirs(d, exist_ok=True)
    paths = []
    for i in range(n):
        t = dur * (i + 1) / (n + 1)
        out = os.path.join(d, 's{:02d}.png'.format(i))
        if os.path.exists(out):
            os.remove(out)
        run([FFMPEG, '-v', 'error', '-ss', '{:.2f}'.format(t), '-i', src,
             '-frames:v', '1', '-y', out], expect=[out])
        paths.append(out)
    return paths


MIN_PEAK = 4.0        # 梯度峰值分数下限
WARM_MIN = 0.05       # 暖色峰值下限（低于此认为该期字幕非暖色，转梯度兜底）
WARM_THR = 0.03       # 暖色掩码阈值
BOT_START = 0.46      # 梯度兜底候选区起始
WARM_START = 0.35     # 暖色候选区起始
TONE_W = 3.0
TAU_RATIO = 0.45
HT_MIN = 14
HT_FRAC_MAX = 0.34


def row_profile(frame_paths):
    """逐行特征（跨帧中位数）：水平梯度 / 亮占比 / 暗占比 / 暖色占比。

    ⭐ 暖色占比是本库最干净的字幕判据：妖板选手的烧录字幕统一为
    **黄底/橙字**，而 K 线图（黑底红绿柱）、文章正文（白底黑字）几乎不产生
    暖色像素（实测字幕行 warm ≈ 0.10~0.28，图表行 ≈ 0.00~0.03）。
    梯度作兜底，服务于字幕非暖色的少数版式。
    """
    grads, brights, inks, warms = [], [], [], []
    for p in frame_paths:
        a = np.asarray(Image.open(p).convert('RGB'), dtype=np.float32)
        g = a.mean(axis=2)
        grads.append(np.abs(np.diff(g, axis=1)).mean(axis=1))
        brights.append((g > 170).mean(axis=1))
        inks.append((g < 85).mean(axis=1))
        warm = ((a[:, :, 0] > 140) & (a[:, :, 0] > a[:, :, 2] + 55)
                & (a[:, :, 1] > a[:, :, 2] + 25))
        warms.append(warm.mean(axis=1))
    st = lambda L: np.median(np.stack(L, axis=0), axis=0)  # noqa: E731
    return st(grads), st(brights), st(inks), st(warms)


def _runs(mask, gap=3):
    """返回连续段列表 [(start, end)]，允许 <=gap 行的断点。"""
    idx = np.flatnonzero(mask)
    if idx.size == 0:
        return []
    runs, s, prev = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - prev <= gap + 1:
            prev = i
        else:
            runs.append((int(s), int(prev)))
            s = prev = i
    runs.append((int(s), int(prev)))
    return runs


def locate_subtitle(frame_paths, h, w, return_score=False):
    """自适应定位烧录字幕带，返回 (y, height)；失败返回 None。

    两级判据：
      A. **暖色带**（主）：黄底/橙字字幕 → 暖色像素占比在该行显著抬升；
         取候选区内"暖色总量"最大的连续段
      B. **梯度峰锚定**（兜底）：无暖色字幕时，取下部梯度峰值行向两侧扩展
    """
    if not frame_paths:
        return None
    med_g, med_b, med_i, med_w = row_profile(frame_paths)
    info = {'method': '', 'peak_y': -1, 'peak': 0.0, 'env': 0.0, 'conf': 0.0}

    # ---------- A. 暖色带 ----------
    y0 = int(h * WARM_START)
    y1 = max(y0 + 1, int(h * 0.995))
    wseg = med_w[y0:y1]
    if wseg.size and float(wseg.max()) >= WARM_MIN:
        thr = max(WARM_THR, 0.30 * float(wseg.max()))
        runs = [r for r in _runs(wseg > thr, gap=3)
                if HT_MIN <= (r[1] - r[0] + 1) <= int(h * HT_FRAC_MAX)]
        if runs:
            best = max(runs, key=lambda r: float(wseg[r[0]:r[1] + 1].sum()))
            top, bot = y0 + best[0], y0 + best[1]
            hm = bot - top + 1
            # 字幕为底端锚定：长句折成两行时向上生长，故上方多留 0.85hm
            pad_top = max(8, int(0.85 * hm))
            pad_bot = max(6, int(0.30 * hm))
            top, bot = max(0, top - pad_top), min(h, bot + 1 + pad_bot)
            if bot - top > int(h * HT_FRAC_MAX):
                top = max(0, bot - int(h * HT_FRAC_MAX))
            info.update({'method': 'warm', 'peak_y': y0 + int(np.argmax(wseg)),
                         'peak': float(wseg.max()),
                         'env': float(np.median(wseg)),
                         'conf': float(wseg.max()) / max(1e-6, float(np.median(wseg)) or 1e-6)})
            if bot - top >= HT_MIN:
                if return_score:
                    return (top, bot - top), info
                return top, bot - top

    # ---------- B. 梯度峰锚定 ----------
    flat = (med_g < 0.8) & (med_b < 0.004) & (med_i < 0.004)
    tone = np.maximum(med_b, med_i)
    score = np.where(~flat, med_g * (1.0 + TONE_W * tone), 0.0)
    gy0 = int(h * BOT_START)
    gy1 = max(gy0 + 1, int(h * 0.995))
    region = score[gy0:gy1]
    if region.size < HT_MIN:
        return None
    ypk = gy0 + int(np.argmax(region))
    pk = float(score[ypk])
    if pk < MIN_PEAK:
        return None
    tau = TAU_RATIO * pk
    top = bot = ypk
    gap = 0
    while top - 1 >= gy0:
        if score[top - 1] > tau:
            top -= 1
            gap = 0
        elif gap < 2 and (top - 2) >= gy0 and score[top - 2] > tau:
            top -= 1
            gap += 1
        else:
            break
    gap = 0
    while bot + 1 < gy1:
        if score[bot + 1] > tau:
            bot += 1
            gap = 0
        elif gap < 2 and (bot + 2) < gy1 and score[bot + 2] > tau:
            bot += 1
            gap += 1
        else:
            break
    if bot - top + 1 < HT_MIN:
        pad = (HT_MIN - (bot - top + 1)) // 2 + 3
        top, bot = top - pad, bot + pad
    ht_max = int(h * HT_FRAC_MAX)
    if bot - top + 1 > ht_max:
        half = ht_max // 2
        top = max(gy0, ypk - half)
        bot = min(h - 1, top + ht_max - 1)
    hm = bot - top + 1
    pad = max(4, int(0.18 * hm))
    top, bot = max(0, top - pad), min(h, bot + 1 + pad)
    if bot - top < HT_MIN:
        return None
    env = float(np.median(region))
    info.update({'method': 'grad', 'peak_y': ypk, 'peak': pk, 'env': env,
                 'conf': (pk / env) if env > 0 else 999.0})
    out = (top, bot - top)
    return (out, info) if return_score else out


def extract_sub(src, outdir, y, ht):
    os.makedirs(outdir, exist_ok=True)
    run([FFMPEG, '-v', 'error', '-i', src,
         '-vf', 'fps={},crop=iw:{}:0:{}'.format(SUB_FPS, ht, y),
         '-y', os.path.join(outdir, '%05d.png')])
    n = len([f for f in os.listdir(outdir) if f.endswith('.png')])
    if n == 0:
        raise RuntimeError('extract_sub 未产出帧（疑似 outdir 含 % 等特殊字符）: {}'.format(outdir))
    return n


def extract_full(src, outdir):
    os.makedirs(outdir, exist_ok=True)
    run([FFMPEG, '-v', 'error', '-i', src,
         '-vf', 'fps={}'.format(FULL_FPS),
         '-y', os.path.join(outdir, '%05d.png')])
    n = len([f for f in os.listdir(outdir) if f.endswith('.png')])
    if n == 0:
        raise RuntimeError('extract_full 未产出帧（疑似 outdir 含 % 等特殊字符）: {}'.format(outdir))
    return n


def dedupe(files, srcdir, th=DIFF_TH):
    kept, prev = [], None
    for fn in files:
        arr = np.asarray(Image.open(os.path.join(srcdir, fn)).convert('L'), dtype=np.int16)
        if prev is not None and arr.shape == prev.shape:
            if float(np.abs(arr - prev).mean()) < th:
                continue
        prev = arr
        kept.append(fn)
    return kept


def build_sheet(srcdir, files, outdir, fps, gutter=118, per=None):
    """纵向拼图。per=None 时按裁切高度自适应，保证单张总高 ≈ SHEET_TARGET_H。"""
    os.makedirs(outdir, exist_ok=True)
    if not files:
        return 0
    font = ImageFont.truetype(FONT_PATH, 26)
    font_small = ImageFont.truetype(FONT_PATH, 20)
    base = Image.open(os.path.join(srcdir, files[0]))
    w, h = base.size
    if per is None:
        per = max(6, min(60, SHEET_TARGET_H // max(1, h)))
    sheet_w = w + gutter
    n = 0
    for si in range(0, len(files), per):
        chunk = files[si:si + per]
        sheet = Image.new('RGB', (sheet_w, h * len(chunk)), (255, 255, 255))
        dr = ImageDraw.Draw(sheet)
        for j, fn in enumerate(chunk):
            im = Image.open(os.path.join(srcdir, fn))
            y = j * h
            sheet.paste(im, (gutter, y))
            sec = (int(fn.split('.')[0]) - 1) / fps
            dr.text((6, y + 8), '{}:{:05.2f}'.format(int(sec // 60), sec % 60),
                    fill=(20, 20, 20), font=font)
            dr.text((6, y + 40), fn.split('.')[0], fill=(120, 120, 120), font=font_small)
            dr.line([(0, y), (sheet_w, y)], fill=(200, 200, 200), width=1)
        dr.line([(gutter, 0), (gutter, sheet.height)], fill=(220, 220, 220), width=1)
        sheet.save(os.path.join(outdir, 'sheet_{:02d}.png'.format(si // per + 1)))
        n += 1
    return n


def build_grid_sheet(srcdir, files, outdir, cols=4, cell_w=430, per=None):
    """完整帧网格总览：每张 cols×rows 排布，用于快速把握整期画面演进。"""
    os.makedirs(outdir, exist_ok=True)
    if not files:
        return 0
    font = ImageFont.truetype(FONT_PATH, 22)
    base = Image.open(os.path.join(srcdir, files[0]))
    bw, bh = base.size
    cw = cell_w
    ch = max(1, int(bh * cw / float(bw)))
    if per is None:
        rows = max(2, min(6, 2500 // max(1, ch)))
        per = cols * rows
    n = 0
    for si in range(0, len(files), per):
        chunk = files[si:si + per]
        rows = (len(chunk) + cols - 1) // cols
        sheet = Image.new('RGB', (cw * cols, (ch + 26) * rows), (255, 255, 255))
        dr = ImageDraw.Draw(sheet)
        for j, fn in enumerate(chunk):
            im = Image.open(os.path.join(srcdir, fn)).convert('RGB').resize((cw, ch), Image.LANCZOS)
            r, c = divmod(j, cols)
            x, y = c * cw, r * (ch + 26)
            sheet.paste(im, (x, y + 26))
            dr.text((x + 4, y + 2), '{}:{}'.format(int(int(fn.split('.')[0]) // 60),
                                                  int(int(fn.split('.')[0]) % 60)),
                     fill=(20, 20, 20), font=font)
            dr.rectangle([x, y + 26, x + cw - 1, y + 26 + ch - 1], outline=(210, 210, 210))
        sheet.save(os.path.join(outdir, 'grid_{:02d}.png'.format(si // per + 1)))
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', default='')
    ap.add_argument('--tag', default='')
    ap.add_argument('--probe-only', action='store_true')
    ap.add_argument('--manual-y', type=int, default=-1)
    ap.add_argument('--manual-h', type=int, default=-1)
    ap.add_argument('--keep-full', action='store_true', help='保留完整帧目录')
    ap.add_argument('--with-full', action='store_true', help='抽完整帧并生成网格总览')
    ap.add_argument('--locate-only', action='store_true', help='只做定位并输出诊断，不抽帧')
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    dur, w, h = probe(src)
    log('{}  {:.1f}s  {}x{}'.format(os.path.basename(src)[:50], dur, w, h))

    if args.probe_only:
        print('duration={:.2f} width={} height={}'.format(dur, w, h))
        return

    if not args.out and not args.locate_only:
        raise SystemExit('--out required')
    out = os.path.abspath(args.out) if args.out else os.path.dirname(src)
    os.makedirs(out, exist_ok=True)

    info = {'method': 'manual', 'peak_y': -1, 'peak': 0.0, 'env': 0.0, 'conf': 0.0}
    if args.manual_y >= 0 and args.manual_h > 0:
        y, ht = args.manual_y, args.manual_h
        log('字幕带（手动）：y={} h={}'.format(y, ht))
    else:
        frames = sample_frames(src, dur, out)
        r = locate_subtitle(frames, h, w, return_score=True)
        if r is None:
            log('⚠️ 字幕带定位失败 → 回退完整帧模式')
            y, ht = None, None
            if args.locate_only:
                print('FAIL\t{}\t{}x{}\t{:.1f}s'.format(os.path.basename(src), w, h, dur))
                return
        else:
            (y, ht), info = r
            log('字幕带（{}）：y={} h={}  峰值@y{} ={:.3f}  对比{:.2f}x'.format(
                info['method'], y, ht, info['peak_y'], info['peak'], info['conf']))
            if args.locate_only:
                print('OK\t{}\ty={}\th={}\t{}x{}\tpeak_y={}\tpeak={:.4f}\tconf={:.2f}\t{}'.format(
                    info['method'], y, ht, w, h, info['peak_y'], info['peak'], info['conf'],
                    os.path.basename(src)))
                with open(os.path.join(out, '_subtitle_band.txt'), 'w', encoding='utf-8') as fp:
                    fp.write('method={} y={} h={} video_h={}\n'.format(
                        info['method'], y, ht, h))
                return

    if y is not None:
        subdir = os.path.join(out, 'sub')
        n_sub = extract_sub(src, subdir, y, ht)
        files = sorted(f for f in os.listdir(subdir) if f.endswith('.png'))
        kept = dedupe(files, subdir)
        n_sheet = build_sheet(subdir, kept, os.path.join(out, 'sheet'), SUB_FPS)
        log('字幕带：抽 {} → 去重 {} → 拼图 {} 张'.format(n_sub, len(kept), n_sheet))
        if n_sub >= 60 and len(kept) / float(n_sub) < 0.08:
            log('⚠️ 去重率异常（{:.1f}%）——字幕带疑似误检为静态条，建议人工复核'.format(
                100.0 * len(kept) / n_sub))
        with open(os.path.join(out, '_subtitle_band.txt'), 'w', encoding='utf-8') as fp:
            fp.write('method={} y={} h={} video_h={}\n'.format(
                info.get('method', 'manual') if y is not None else 'none', y, ht, h))

    n_grid = 0
    if args.with_full or y is None:
        fulldir = os.path.join(out, 'full')
        n_full = extract_full(src, fulldir)
        ffiles = sorted(f for f in os.listdir(fulldir) if f.endswith('.png'))
        fkept = dedupe(ffiles, fulldir, th=2.2)
        n_grid = build_grid_sheet(fulldir, fkept, os.path.join(out, 'grid'))
        log('完整帧：抽 {} → 去重 {} → 网格 {} 张'.format(n_full, len(fkept), n_grid))
        if not args.keep_full:
            pass  # 目录保留，由调用方决定何时清理

    log('完成 → {}'.format(out))


if __name__ == '__main__':
    main()
