"""生成「选手候选池」真值基准 `learning/labels/player_pool/<date>.json`。

【为什么有这个模块】
新选股层的**核对尺子**：系统战法池是否捕获了选手当日候选池名单（召回 = 必要条件）。
数据源 = `选手学习资料/文字资料/<date>_<HHMM>_候选池*/record.md`（人工转录，**带 6 位代码**）。

【口径（关键，勿改）】
1. `date` 取**发布日**，不取原文里的文字日期 —— 9/9 那条原文写「9月8日符合…」
   但发布于 9/9 09:46（`2026-09-09_0946_候选池与复盘/record.md:12-13`）。
2. 只有 **8 天**有带代码的候选池记录（8/31 与 9/1 无候选池目录，故不收录）；
   8 天 = 32 只，**全部带代码**，无需走 `stock_alias.json` 之类的名称映射（零歧义）。
3. `executed` 只标 record.md 里有**明文证据**的项，其余为 `null`（不猜）。
4. 每项带 `source`（文件:行号），便于回溯核对。

用法:
    python build_player_pool.py            # 生成 + 打印汇总
    python build_player_pool.py --check    # 只校验已落盘文件与内置数据一致
"""
from __future__ import annotations

import argparse
import io
import json
import os

EA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTDIR = os.path.join(EA, "learning", "labels", "player_pool")
REL = "选手学习资料/文字资料"


def _d(d, hm, items):
    return {
        "date": d,
        "publish_ts": f"{d} {hm[:2]}:{hm[2:]}",
        "source_dir": f"{REL}/{d}_{hm}_候选池" if d not in ("2026-09-09", "2026-09-10")
                      else f"{REL}/{d}_{hm}_" + ("候选池与复盘" if d == "2026-09-09" else "候选池与纪律"),
        "items": items,
    }


def _it(name, sym, executed, evidence, note=None):
    r = {"name": name, "sym": sym, "executed": executed, "evidence": evidence}
    if note:
        r["note"] = note
    return r


DATA = [
    _d("2026-09-02", "0942", [
        _it("黄河旋风", "600172", True, f"{REL}/2026-09-02_0942_候选池/record.md:24", "已建仓，成本 15.095"),
        _it("诺德股份", "600110", None, f"{REL}/2026-09-02_0942_候选池/record.md:25"),
        _it("浪潮信息", "000977", None, f"{REL}/2026-09-02_0942_候选池/record.md:26"),
        _it("利君股份", "002651", True, f"{REL}/2026-09-02_0942_候选池/record.md:27", "已建仓，成本 8.963"),
    ]),
    _d("2026-09-03", "0940", [
        _it("佳力图", "603912", None, f"{REL}/2026-09-03_0940_候选池/record.md:23", "数据中心精密空调/液冷"),
        _it("力鼎光电", "605118", None, f"{REL}/2026-09-03_0940_候选池/record.md:24", "光通信/光器件"),
        _it("金富科技", "003018", None, f"{REL}/2026-09-03_0940_候选池/record.md:25", "金属易拉盖"),
        _it("科德教育", "300192", None, f"{REL}/2026-09-03_0940_候选池/record.md:26", "职业教育"),
    ]),
    _d("2026-09-04", "0947", [
        _it("欢瑞世纪", "000892", True, f"{REL}/2026-09-04_0947_候选池/record.md:19", "6000 股 @5.272"),
        _it("高新发展", "000628", True, f"{REL}/2026-09-04_0947_候选池/record.md:20", "600 股 @54.806"),
        _it("协鑫能科", "002015", True, f"{REL}/2026-09-04_0947_候选池/record.md:21", "2000 股 @17.535"),
        _it("远大控股", "000626", False, f"{REL}/2026-09-04_0947_候选池/record.md:22"),
        _it("久其软件", "002279", False, f"{REL}/2026-09-04_0947_候选池/record.md:23"),
    ]),
    _d("2026-09-07", "0941", [
        _it("光洋股份", "002708", True, f"{REL}/2026-09-07_0941_候选池/record.md:19", "2000 股 @16.065，当日涨停"),
        _it("东材科技", "601208", True, f"{REL}/2026-09-07_0941_候选池/record.md:20", "1000 股 @48.255"),
        _it("隆平高科", "000998", False, f"{REL}/2026-09-07_0941_候选池/record.md:21"),
        _it("泸天化", "000912", False, f"{REL}/2026-09-07_0941_候选池/record.md:22", "著名弃买案例：拉的太快没上车"),
    ]),
    _d("2026-09-09", "0946", [
        _it("金帝股份", "603270", False, f"{REL}/2026-09-09_0946_候选池与复盘/record.md:34", "分时跌破均价线不玩"),
        _it("武汉凡谷", "002194", False, f"{REL}/2026-09-09_0946_候选池与复盘/record.md:35", "分时跌破均价线不玩"),
        _it("金富科技", "003018", False, f"{REL}/2026-09-09_0946_候选池与复盘/record.md:36", "分时跌破均价线不玩"),
        _it("海通发展", "603162", True, f"{REL}/2026-09-09_0946_候选池与复盘/record.md:37", "4000 股 @14.585，当日涨停封板"),
    ]),
    _d("2026-09-10", "0935", [
        _it("山东玻纤", "605006", True, f"{REL}/2026-09-10_0935_候选池与纪律/record.md:38", "6500 股 @16.875"),
        _it("沃特股份", "002886", True, f"{REL}/2026-09-10_0935_候选池与纪律/record.md:39", "4000 股 @26.838"),
        _it("金能科技", "603113", False, f"{REL}/2026-09-10_0935_候选池与纪律/record.md:40", "分时第一波回落破均价线"),
        _it("南华期货", "603093", False, f"{REL}/2026-09-10_0935_候选池与纪律/record.md:41", "同上"),
    ]),
    _d("2026-09-11", "0943", [
        _it("特发信息", "000070", None, f"{REL}/2026-09-11_0943_候选池/record.md:23"),
        _it("依顿电子", "603328", True, f"{REL}/2026-09-11_0943_候选池/record.md:24", "9/11 买入 @12.304（画像:1128）"),
        _it("博云新材", "002297", None, f"{REL}/2026-09-11_0943_候选池/record.md:25"),
    ]),
    _d("2026-09-14", "0946", [
        _it("兴森科技", "002436", False, f"{REL}/2026-09-14_0946_候选池/record.md:23"),
        _it("博敏电子", "603936", True, f"{REL}/2026-09-14_0946_候选池/record.md:24", "5000 股 @21.42664"),
        _it("乐山电力", "600644", False, f"{REL}/2026-09-14_0946_候选池/record.md:25", "跌破均价线"),
        _it("新中港", "605162", False, f"{REL}/2026-09-14_0946_候选池/record.md:26", "跌破均价线"),
    ]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验已落盘文件与内置数据一致")
    a = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    bad = 0
    total = 0
    for d in DATA:
        fp = os.path.join(OUTDIR, d["date"] + ".json")
        total += len(d["items"])
        if a.check:
            try:
                with io.open(fp, "r", encoding="utf-8") as f:
                    cur = json.load(f)
                same = cur.get("items") == d["items"]
                print(("OK   " if same else "DIFF ") + d["date"] + f"  items={len(d['items'])}")
                bad += 0 if same else 1
            except Exception as e:
                print("MISS " + d["date"] + "  %r" % (e,))
                bad += 1
            continue
        doc = dict(d)
        doc["n_items"] = len(doc["items"])
        doc["note"] = ("核对尺子：系统战法池须**捕获**本列表每一只（召回 = 必要条件）。"
                       "缺失即说明池层筛掉了真值，判 FAIL。")
        with io.open(fp, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False, indent=1)
        print("WROTE %s  items=%d" % (os.path.basename(fp), len(doc["items"])))
    print("---")
    print("days=%d items=%d dir=%s%s" % (len(DATA), total, OUTDIR, ("  DIFF=%d" % bad) if a.check else ""))


if __name__ == "__main__":
    raise SystemExit(main())
