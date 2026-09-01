"""Adapt validated yaoban markdown reports into EvoAlpha role artifacts."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.resolve()


def atomic_write(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as handle:
        handle.write(encoded)
        handle.flush()
        temp = pathlib.Path(handle.name)
    temp.replace(path)


def adapt(report_path: pathlib.Path, role: str) -> dict:
    report_path = report_path.resolve()
    text = report_path.read_text(encoding="utf-8")
    title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.startswith("#")), report_path.stem)
    date_match = re.search(r"20\\d{2}[-_]\\d{2}[-_]\\d{2}", text)
    as_of = date_match.group(0).replace("_", "-") if date_match else "historical"
    return {
        "schema_version": "evoalpha.agent-artifact.v1",
        "run_id": f"historical-{report_path.stem}",
        "as_of": as_of,
        "role": role,
        "status": "complete",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "historical": True,
        "report_title": title,
        "facts": {"report_bytes": len(text.encode("utf-8")), "source_type": "yaoban_markdown"},
        "evidence_refs": [str(report_path.relative_to(WORKSPACE))],
        "report_ref": str(report_path.relative_to(WORKSPACE)),
        "source": "yaoban-system",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Adapt a yaoban report into an EvoAlpha role artifact")
    parser.add_argument("report", type=pathlib.Path)
    parser.add_argument("--role", choices=["strategy_researcher", "reviewer"], required=True)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = adapt(args.report, args.role)
    output = args.output or ROOT / "outputs" / "team_artifacts" / f"{result['run_id']}-{args.role}.json"
    atomic_write(output, result)
    print(f"artifact={output} status={result['status']} role={args.role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
