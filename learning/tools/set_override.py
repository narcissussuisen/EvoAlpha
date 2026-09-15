# -*- coding: utf-8 -*-
"""把批次产物写入 status_override.json（读同目录 _override_pick.json）。

_override_pick.json 格式：
    {
      "batch": "04_仓位风控心态",
      "pick": [
        ["2026-05-17", "标题唯一子串", "归档目录名"],
        ...
      ]
    }
每条 = [日期前缀, 标题关键字, 归档目录名]；匹配 rel 同时含日期前缀与标题关键字。
"""
import json
import os
import sys

if sys.stdout is not None:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (AttributeError, ValueError):
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = r'C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档\EvoAlpha\选手学习资料\妖板选手视频拆解'
SCAN = os.path.join(DEST, '_meta', 'library_scan.json')
OVR = os.path.join(DEST, '_meta', 'status_override.json')
PICK_FILE = os.path.join(HERE, '_override_pick.json')


def main():
    with open(PICK_FILE, encoding='utf-8') as fp:
        cfg = json.load(fp)
    batch = cfg['batch']
    picks = cfg['pick']

    with open(SCAN, encoding='utf-8') as fp:
        rows = json.load(fp)
    with open(OVR, encoding='utf-8') as fp:
        ovr = json.load(fp)

    hit, miss = 0, []
    for date, key, folder in picks:
        found = None
        for r in rows:
            if date in r['rel'] and key in r['rel']:
                found = r['rel']
                break
        if not found:
            miss.append('{} / {}'.format(date, key))
            continue
        ovr[found] = {'status': '√',
                      'record': '`{}/{}/record.md`'.format(batch, folder)}
        hit += 1

    with open(OVR, 'w', encoding='utf-8') as fp:
        json.dump(ovr, fp, ensure_ascii=False, indent=2)

    print('batch = {}'.format(batch))
    print('matched {}/{}'.format(hit, len(picks)))
    print('miss: {}'.format(miss))
    print('override total = {}'.format(len(ovr)))


if __name__ == '__main__':
    main()
