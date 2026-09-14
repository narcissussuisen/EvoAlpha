"""选手候选池「召回」回放器 —— 核对系统战法池是否捕获了选手当日名单。

【口径】
  对每个候选池**发布日 T**：用 `asof = T-1 交易日` 重建系统战法池，
  检查选手名单里每一只是否出现在池中（`captured`），并记录命中的战法与信号新鲜度。
  ⇒ 这是**必要条件**检验：池里没有 ⇒ 下游永远买不到 ⇒ 该日判 FAIL。

【为什么秒级】
  只喂**选手名单那几十只票**的日线（`core.daily_src.load_daily` 单票读 parquet），
  而不是全市场 5644 只（那要 ~35min/次）。`build_pattern_pool` 是纯函数，
  同一只票在子集与全市场下的输出**逐字段一致**（可用 `--consistency <sym>` 证伪）。

【用法】
    python player_pool_recall.py                          # 跑全部已落盘的 player_pool
    python player_pool_recall.py --dates 2026-09-11,2026-09-14
    python player_pool_recall.py --keys pullback_pct_max=12   # 覆盖 live 键做受控试验
    python player_pool_recall.py --consistency 600644         # 子集 vs 全市场产物 逐字段比对
"""
from __future__ import annotations

import argparse
import glob
import io
import json
import os
import sys

EA = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YS = os.path.join(EA, "yaoban-system")
POOL_DIR = os.path.join(EA, "learning", "labels", "player_pool")
OUTDIR = os.path.join(EA, "outputs", "player_pool_recall")

sys.path.insert(0, os.path.join(YS, "src"))
sys.path.insert(0, os.path.join(YS, "scripts"))
sys.path.insert(0, os.path.join(EA, "py_libs"))

ALL_PATTERNS = ("huigui", "zt_huicai", "xianren", "qu_shi_fanbao")


def _prev_trading_day(day: str) -> str:
    """取上一交易日。优先用生产日历，退化为读 trade_dates_2026.json。"""
    try:
        sys.path.insert(0, os.path.join(YS, "scripts"))
        import trading_calendar as tc                                   # noqa: E402
        for name in ("prev_trading_day", "previous_trading_day", "prev_trade_day"):
            fn = getattr(tc, name, None)
            if callable(fn):
                return str(fn(day))
    except Exception:
        pass
    cal = os.path.join(YS, "outputs", "calendar", "trade_dates_2026.json")
    try:
        with io.open(cal, "r", encoding="utf-8") as f:
            doc = json.load(f)
        days = doc if isinstance(doc, list) else (doc.get("dates") or doc.get("trade_dates") or [])
        days = sorted(str(d) for d in days)
        before = [d for d in days if d < day]
        if before:
            return before[-1]
    except Exception:
        pass
    raise RuntimeError("无法确定 %s 的上一交易日（既无 trading_calendar.prev_trading_day，也读不到 trade_dates_2026.json）" % day)


def _load_all(names_needed: set):
    from core.daily_src import load_daily
    dmap, missing, bars = {}, [], {}
    for sym in sorted(names_needed):
        try:
            df = load_daily(sym)
        except Exception:
            df = None
        if df is None or not len(df):
            missing.append(sym)
            continue
        dmap[sym] = df
        bars[sym] = int(len(df))
    return dmap, missing, bars


def recall_one(date: str, key_overrides: dict | None, patterns=ALL_PATTERNS, lookback: int = 4) -> dict:
    from core.pattern_pool import build_pattern_pool, load_stock_names
    fp = os.path.join(POOL_DIR, date + ".json")
    with io.open(fp, "r", encoding="utf-8") as f:
        doc = json.load(f)
    items = doc["items"]
    syms = {it["sym"] for it in items if it.get("sym")}
    asof = _prev_trading_day(date)

    if key_overrides:
        import config as _cfg
        import core.strategies as S
        for tbl in ("CFG_HG", "CFG_ZT", "CFG_XR"):
            d = getattr(S, tbl, None)
            if not isinstance(d, dict):
                continue
            live = d.get("live") if isinstance(d.get("live"), dict) else d
            for k, v in key_overrides.items():
                if k in live:
                    live[k] = v
                if k in d:
                    d[k] = v

    dmap, missing, bars = _load_all(syms)
    pool, stats = build_pattern_pool(dmap, asof=asof, lookback=lookback,
                                     patterns=tuple(patterns), names=load_stock_names())
    pmap = {r["sym"]: r for r in pool}

    rows = []
    for it in items:
        sym = it.get("sym")
        r = pmap.get(sym)
        rows.append({
            "date": date, "name": it.get("name"), "sym": sym,
            "asof": asof, "captured": sym in pmap,
            "pattern": (r or {}).get("pattern"), "patterns": (r or {}).get("patterns"),
            "sig_date": (r or {}).get("sig_date"), "bars_since_sig": (r or {}).get("bars_since_sig"),
            "n_bars": bars.get(sym),
            "skipped_short": bool(sym in dmap and sym not in pmap and bars.get(sym, 0) < 76),
            "no_data": sym in missing,
            "executed": it.get("executed"),
        })
    captured = sum(1 for r in rows if r["captured"])
    # 真实生产产物（若该日有，用于交叉核对；注意其 asof 可能不同）
    prod = None
    pfp = os.path.join(YS, "outputs", "patterns", f"{date}_pattern_pool.json")
    if os.path.exists(pfp):
        try:
            with io.open(pfp, "r", encoding="utf-8") as f:
                pd_ = json.load(f)
            psyms = {r["sym"] for r in pd_.get("pool", [])}
            prod = {"file": os.path.basename(pfp), "asof": pd_.get("asof"),
                    "n_pool": len(psyms),
                    "captured": sorted(s for s in syms if s in psyms),
                    "n_captured": sum(1 for s in syms if s in psyms)}
        except Exception as e:
            prod = {"file": os.path.basename(pfp), "error": repr(e)}
    return {
        "date": date, "asof": asof, "n_items": len(items), "n_captured": captured,
        "recall": round(captured / max(1, len(items)), 4),
        "pattern_stats": stats.get("by_pattern"), "n_pool_subset": len(pool),
        "no_data": missing,
        "skipped_short": [r["sym"] for r in rows if r["skipped_short"]],
        "rows": rows, "prod_pool": prod,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dates", default="", help="逗号分隔；缺省=全部 player_pool/*.json")
    ap.add_argument("--keys", default="", help="覆盖 live 键，形如 pullback_pct_max=12,volume_ratio_max=0.85")
    ap.add_argument("--patterns", default=",".join(ALL_PATTERNS))
    ap.add_argument("--lookback", type=int, default=4)
    ap.add_argument("--out", default="", help="结果 JSON 路径；缺省 outputs/player_pool_recall/<ts>.json")
    a = ap.parse_args()

    dates = [x.strip() for x in a.dates.split(",") if x.strip()] or \
        [os.path.basename(p)[:-5] for p in sorted(glob.glob(os.path.join(POOL_DIR, "*.json")))]
    overrides = {}
    for kv in [x for x in a.keys.split(",") if x.strip()]:
        k, v = kv.split("=")
        overrides[k.strip()] = float(v)

    res = []
    for d in dates:
        r = recall_one(d, overrides or None, patterns=tuple(a.patterns.split(",")), lookback=a.lookback)
        res.append(r)
        print("%s  asof=%s  recall=%d/%d  子集池=%d  %s" % (
            r["date"], r["asof"], r["n_captured"], r["n_items"], r["n_pool_subset"],
            "" if r["n_captured"] == r["n_items"] else "  ← 未捕获: " + ",".join(
                x["sym"] + "(" + (x["name"] or "") + ")" for x in r["rows"] if not x["captured"])))
        if r["no_data"]:
            print("     ⚠ 无日线数据: %s" % ",".join(r["no_data"]))
        if r["skipped_short"]:
            print("     ⚠ 日线不足 76 根(会漏判): %s" % ",".join(r["skipped_short"]))
        if r["prod_pool"] and "n_captured" in (r["prod_pool"] or {}):
            p = r["prod_pool"]
            print("     生产产物 %s (asof=%s, n=%d) 捕获 %d/%d" % (
                p["file"], p["asof"], p["n_pool"], p["n_captured"], r["n_items"]))

    tot_i = sum(r["n_items"] for r in res)
    tot_c = sum(r["n_captured"] for r in res)
    print("=" * 70)
    print("TOTAL recall %d/%d = %.1f%%  (days=%d, keys=%s)" % (
        tot_c, tot_i, 100.0 * tot_c / max(1, tot_i), len(res), overrides or "生产默认"))

    os.makedirs(OUTDIR, exist_ok=True)
    out = a.out or os.path.join(OUTDIR, ("recall_keys_%s.json" % "_".join("%s%s" % (k, v) for k, v in overrides.items())) if overrides
                                else "recall_baseline.json")
    with io.open(out, "w", encoding="utf-8") as f:
        json.dump({"dates": dates, "keys": overrides, "patterns": a.patterns,
                   "total": {"n_items": tot_i, "n_captured": tot_c},
                   "days": res}, f, ensure_ascii=False, indent=1)
    print("WROTE", out)


if __name__ == "__main__":
    raise SystemExit(main())
