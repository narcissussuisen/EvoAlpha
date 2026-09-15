# -*- coding: utf-8 -*-
"""把工作目录里的关键证据帧按语义命名复制到归档目录。"""
import os
import shutil
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = r'C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档\EvoAlpha'
WORK = os.path.join(BASE, '选手学习资料', '妖板选手视频拆解', '_work')
DEST = os.path.join(BASE, '选手学习资料', '妖板选手视频拆解')

TAGS = {
    '20260428': '20260428_01_小资金最强选漂战法，涨停回踩',
    '20260605': '20260605_02_立志每天抓板：趋势反包战法，',
    '20260816': '20260816_03_一年只讲一次，仙人指路选漂战',
}

PLAN = [
    # (tag, 源相对路径, 目标子目录, 目标文件名)
    ('20260428', 'sheet/sheet_01.png', '01_战法核心/20260428_涨停回踩低吸/frames', '01_总纲_五句口诀_涨停后回踩第二波.png'),
    ('20260428', 'sheet/sheet_02.png', '01_战法核心/20260428_涨停回踩低吸/frames', '02_形态1-4_箱体回踩_巨量阴线_三小阴_缩量三连板.png'),
    ('20260428', 'sheet/sheet_03.png', '01_战法核心/20260428_涨停回踩低吸/frames', '03_形态5_震荡5到7天缩量到极致.png'),
    ('20260605', 'sheet/sheet_01.png', '01_战法核心/20260605_趋势反包战法/frames', '01_6月5日盘面_血雨腥风_科技电力调整.png'),
    ('20260605', 'sheet/sheet_02.png', '01_战法核心/20260605_趋势反包战法/frames', '02_止盈落袋与辽宁能源亏损出局.png'),
    ('20260605', 'sheet/sheet_03.png', '01_战法核心/20260605_趋势反包战法/frames', '03_北证脉冲信号与切换方向.png'),
    ('20260816', 'fullsheet/full_03.png', '01_战法核心/20260816_仙人指路选股战法/frames', '01_三个条件_位置_上影线_反包确认.png'),
    ('20260816', 'fullsheet/full_05.png', '01_战法核心/20260816_仙人指路选股战法/frames', '02_盘中细节_量能温柔放量_分时急拉缓跌.png'),
    ('20260816', 'fullsheet/full_06.png', '01_战法核心/20260816_仙人指路选股战法/frames', '03_形态图解与通达信选股公式源码.png'),
    ('20260816', 'fullsheet/full_07.png', '01_战法核心/20260816_仙人指路选股战法/frames', '04_用法_次日确认打底仓_止损位置.png'),
    ('20260816', 'fullsheet/full_02.png', '01_战法核心/20260816_仙人指路选股战法/frames', '05_实战教训_兴民智通一条上影线洗掉70%利润.png'),
]


def main():
    n = 0
    for tag, rel, dst_sub, name in PLAN:
        src = os.path.join(WORK, TAGS[tag], rel)
        if not os.path.exists(src):
            print('缺失 {}'.format(src))
            continue
        dstd = os.path.join(DEST, dst_sub)
        os.makedirs(dstd, exist_ok=True)
        shutil.copy2(src, os.path.join(dstd, name))
        n += 1
        print('ok {} -> {}'.format(rel, os.path.join(dst_sub, name)))
    print('共复制 {} 个证据帧'.format(n))


if __name__ == '__main__':
    main()
