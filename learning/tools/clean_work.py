# -*- coding: utf-8 -*-
"""清理抽帧中间产物（保留 sheet / grid / fullsheet / meta.json）。

用法：python clean_work.py [--apply]
默认仅报告；加 --apply 才真删。只删 _work 与 _meta/_sweep 下的 sub/ full/ _sample/ 目录。
"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档\EvoAlpha'
ROOTS = [
    os.path.join(BASE, '选手学习资料', '妖板选手视频拆解', '_work'),
    os.path.join(BASE, '选手学习资料', '妖板选手视频拆解', '_meta'),
    os.path.join(BASE, '选手学习资料', '妖板选手视频拆解', '_calib'),
]
TEMPS = ('sub', 'full', '_sample', '_probe', '_sweep')


def dsize(p):
    t = 0
    for dp, _d, fs in os.walk(p):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return t


def main():
    apply = '--apply' in sys.argv
    total = 0
    targets = []
    for root in ROOTS:
        if not os.path.isdir(root):
            continue
        for dp, dns, _fs in os.walk(root):
            for d in list(dns):
                if d in TEMPS:
                    targets.append(os.path.join(dp, d))
    for t in sorted(set(targets)):
        s = dsize(t)
        total += s
        print('{:>9.1f} MB  {}'.format(s / 1048576.0, t.replace(BASE, '.')))
    print('合计 {:.1f} MB，{} 个目录'.format(total / 1048576.0, len(set(targets))))
    if apply:
        for t in sorted(set(targets)):
            shutil.rmtree(t, ignore_errors=True)
        print('已清理。剩余：')
        for root in ROOTS:
            if os.path.isdir(root):
                print('  {:.1f} MB  {}'.format(dsize(root) / 1048576.0, root.replace(BASE, '.')))
    else:
        print('（未执行，加 --apply 生效）')


if __name__ == '__main__':
    main()
