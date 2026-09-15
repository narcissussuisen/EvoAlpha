# -*- coding: utf-8 -*-
"""向 EvoAlpha 专用飞书 hook 推送一行状态（仅用标准库）。

用法：
    python push_evoalpha_feishu.py "<text>"
    python push_evoalpha_feishu.py --file <utf-8 文本文件>

⚠️ 中文长文本建议用 `--file`：PowerShell 向 native exe 传中文 argv 会经 GBK 转换而乱码。
"""
import json
import sys
import urllib.request

HOOK = ('https://open.feishu.cn/open-apis/bot/v2/hook/'
        'f85cb8ae-f72a-425c-a67c-760be29db468')


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == '--file':
        if len(argv) < 2:
            raise SystemExit('usage: push_evoalpha_feishu.py --file <path>')
        with open(argv[1], encoding='utf-8') as fp:
            text = fp.read().strip()
    else:
        text = argv[0] if argv else ''
    if not text:
        raise SystemExit('usage: push_evoalpha_feishu.py "<text>" | --file <path>')
    data = json.dumps({'msg_type': 'text', 'content': {'text': text}}).encode('utf-8')
    req = urllib.request.Request(HOOK, data=data,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as r:
        print(r.read().decode('utf-8')[:200])


if __name__ == '__main__':
    main()
