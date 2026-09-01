"""Adapt the yaoban paper-trade report into trader and portfolio_manager artifacts.

Parses the markdown replay report (组合表现 + 交易明细) into structured role
artifacts so simulated fills and performance attribution enter the EvoAlpha
team decision chain.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.resolve()

ROLE_CHOICES = ["trader", "portfolio_manager"]


def atomic_write(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as handle:
        handle.write(encoded)
        handle.flush()
        temp = pathlib.Path(handle.name)
    temp.replace(path)


def _parse_table_rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # separator row
        rows.append(cells)
    return rows


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+{heading}\s*$.*?(?=^##\s|\Z)", text, re.M | re.S)
    return match.group(0) if match else ""


def parse_report(report_path: pathlib.Path) -> dict:
    text = report_path.read_text(encoding="utf-8")
    perf = _section(text, "组合表现")
    trades = _section(text, "交易明细")
    orders: list[dict] = []
    for row in _parse_table_rows(trades)[1:]:
        if len(row) < 6:
            continue
        orders.append({
            "symbol": row[1].split()[0] if row[1] else "",
            "name": row[1].split(maxsplit=1)[-1] if row[1] and " " in row[1] else "",
            "entry_date": row[2],
            "exit_date": row[3],
            "hold_days": row[4],
            "pnl_pct": row[5],
            "exit_reason": row[6] if len(row) > 6 else "",
        })
    facts: dict = {}
    for key, label in [
        ("end_equity", r"期末资金"),
        ("total_return_pct", r"总收益"),
        ("max_drawdown_pct", r"最大回撤"),
        ("trade_count", r"交易笔数"),
        ("win_rate_pct", r"胜率"),
        ("avg_pnl_pct", r"平均盈亏"),
    ]:
        m = re.search(rf"{label}[^\n]*?([-+]?\d[\d,]*(?:\.\d+)?%?)", perf)
        if m:
            facts[key] = m.group(1)
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})\s*~\s*(\d{4}-\d{2}-\d{2})", text)
    window = {"start": date_match.group(1), "end": date_match.group(2)} if date_match else {}
    return {
        "orders": orders,
        "facts": facts,
        "window": window,
        "report_ref": str(report_path.resolve().relative_to(WORKSPACE)),
    }


def adapt(report_path: pathlib.Path, role: str) -> dict:
    parsed = parse_report(report_path)
    common = {
        "schema_version": "evoalpha.agent-artifact.v1",
        "run_id": f"paper-{pathlib.Path(report_path).stem}",
        "as_of": parsed["window"].get("end", "historical"),
        "role": role,
        "status": "complete",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "historical": True,
        "evidence_refs": [parsed["report_ref"]],
        "report_ref": parsed["report_ref"],
        "source": "yaoban-system",
    }
    if role == "trader":
        return {**common, "orders": parsed["orders"], "execution_assumptions": ["日线近似回放，不含分时纪律"], "execution_status": "paper_replay"}
    return {**common, "capital_base": "1,000,000", "positions": [], "portfolio_constraints": {}, "performance": parsed["facts"], "window": parsed["window"]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Adapt a paper-trade report into role artifacts")
    parser.add_argument("report", type=pathlib.Path)
    parser.add_argument("--role", choices=ROLE_CHOICES, required=True)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = adapt(args.report, args.role)
    output = args.output or ROOT / "outputs" / "team_artifacts" / f"{result['run_id']}-{args.role}.json"
    atomic_write(output, result)
    print(f"artifact={output} status={result['status']} role={args.role} orders={len(result.get('orders', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
