# -*- coding: utf-8 -*-
"""
视频资料转写工具（EvoAlpha 选手研究）

用途：把选手复盘视频（mp4）批量转成带时间戳的文字稿，供后续归档/学习。
依赖：faster-whisper + av（都在 C:\\Users\\YZP\\.workbuddy\\binaries\\python\\envs\\default）

用法：
    python video_transcribe.py                # 转写 VIDEO_DIR 下全部视频
    python video_transcribe.py --match 2026-09   # 只转写文件名含该串的视频
    python video_transcribe.py --model medium --out <dir>

说明：
- HuggingFace 直连被墙，默认走 hf-mirror.com
- 视频自带烧录字幕，ASR 用于快速取全文；图表/截图信息另用抽帧人工核对
- 顶部忽略 SIGINT/SIGBREAK/SIGTERM，避免宿主超时强杀时连带子进程
"""
import argparse
import json
import os
import signal
import sys
import time

# —— Windows 长跑保命：忽略控制台信号 ——
for _s in ('SIGINT', 'SIGBREAK', 'SIGTERM'):
    try:
        signal.signal(getattr(signal, _s), signal.SIG_IGN)
    except (AttributeError, ValueError, OSError):
        pass

os.environ.setdefault('HF_ENDPOINT', 'https://hf-mirror.com')
os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')

sys.stdout.reconfigure(encoding='utf-8')

VID_DIR = (r'C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档\EvoAlpha'
           r'\选手学习资料\人工录入资料\视频资料')

# 领域词表 —— 提升财经/交易术语识别率
INITIAL_PROMPT = (
    '妖板选手，上升回档战法，涨停回踩低吸，倍量涨停，缩量回踩，分时均价线，'
    '龙虎榜，换手率，量比，封单额，炸板，反包，梯量，主力，游资，首板，连板，'
    '打板，低吸，止盈，止损，背离，支撑位，压力位，板块，主线，妖股，'
    '上证指数，创业板，量能，缩量，放量，均价线，五日线，十日线，二十日线。'
)


def fmt_ts(seconds):
    m = int(seconds // 60)
    s = int(seconds % 60)
    return '{}:{:02d}'.format(m, s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--match', default='', help='逗号分隔的子串，命中任一即转写；留空=全部')
    ap.add_argument('--model', default='medium')
    ap.add_argument('--out', default=os.path.join(VID_DIR, '_asr'))
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)

    pats = [p.strip() for p in args.match.split(',') if p.strip()]
    files = sorted(
        f for f in os.listdir(VID_DIR)
        if f.lower().endswith('.mp4') and (not pats or any(p in f for p in pats))
    )
    if not files:
        print('没有匹配的视频')
        return

    print('[{}] 待转写 {} 个视频，模型={}'.format(
        time.strftime('%H:%M:%S'), len(files), args.model), flush=True)

    from faster_whisper import WhisperModel
    t0 = time.time()
    model = WhisperModel(args.model, device='cpu', compute_type='int8', cpu_threads=6)
    print('[{}] 模型就绪，耗时 {:.1f}s'.format(
        time.strftime('%H:%M:%S'), time.time() - t0), flush=True)

    for i, fn in enumerate(files, 1):
        stem = os.path.splitext(fn)[0]
        txt_path = os.path.join(args.out, stem + '.txt')
        json_path = os.path.join(args.out, stem + '.json')
        if os.path.exists(json_path) and not args.force:
            print('[{}] ({}/{}) 已存在，跳过：{}'.format(
                time.strftime('%H:%M:%S'), i, len(files), fn), flush=True)
            continue

        src = os.path.join(VID_DIR, fn)
        print('\n[{}] ({}/{}) 开始：{}'.format(
            time.strftime('%H:%M:%S'), i, len(files), fn), flush=True)
        t1 = time.time()
        segments, info = model.transcribe(
            src,
            language='zh',
            beam_size=5,
            vad_filter=True,
            vad_parameters={'min_silence_duration_ms': 400},
            initial_prompt=INITIAL_PROMPT,
            condition_on_previous_text=False,
        )

        rows = []
        lines = []
        for seg in segments:
            text = seg.text.strip()
            if not text:
                continue
            rows.append({'start': round(seg.start, 2), 'end': round(seg.end, 2), 'text': text})
            lines.append('[{}] {}'.format(fmt_ts(seg.start), text))
            if len(rows) % 10 == 0:
                print('    ...{} 段 (t={})'.format(len(rows), fmt_ts(seg.end)), flush=True)

        with open(txt_path, 'w', encoding='utf-8') as fp:
            fp.write('\n'.join(lines))
        with open(json_path, 'w', encoding='utf-8') as fp:
            json.dump({'file': fn, 'model': args.model, 'language': 'zh',
                       'duration': info.duration, 'segments': rows},
                      fp, ensure_ascii=False, indent=1)
        print('[{}] 完成 ({} 段, {:.1f}s, 耗时 {:.1f}s) -> {}'.format(
            time.strftime('%H:%M:%S'), len(rows), info.duration,
            time.time() - t1, os.path.basename(txt_path)), flush=True)

    print('\n[{}] 全部完成'.format(time.strftime('%H:%M:%S')), flush=True)


if __name__ == '__main__':
    main()
