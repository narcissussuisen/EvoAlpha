"""Adapt a Vibe-Research run into an EvoAlpha researcher artifact."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent


def read_json(path: pathlib.Path) -> dict | list:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, (dict, list)):
        raise ValueError(f"expected JSON object or array: {path}")
    return value


def atomic_write(path: pathlib.Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as handle:
        handle.write(encoded)
        handle.flush()
        temp = pathlib.Path(handle.name)
    temp.replace(path)


def adapt(run_dir: pathlib.Path) -> dict:
    run_dir = run_dir.resolve()
    workspace = ROOT.resolve()
    manifest = read_json(run_dir / "manifest.json")
    evidence = read_json(run_dir / "evidence.json")
    calculations = read_json(run_dir / "calculations.json")
    report = run_dir / "report.md"
    stages = manifest.get("stages", [])
    status = str(manifest.get("status", "incomplete"))
    return {
        "schema_version": "evoalpha.agent-artifact.v1",
        "run_id": str(manifest.get("run_id", run_dir.name)),
        "as_of": str(manifest.get("finished_at", manifest.get("started_at", ""))),
        "role": "researcher",
        "status": status if status in {"complete", "incomplete", "blocked", "failed"} else "incomplete",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "symbol": str(manifest.get("symbol", "")),
        "market": str(manifest.get("market", "")),
        "research_question": f"Vibe-Research run for {manifest.get('symbol', '')}",
        "facts": {
            "evidence_count": manifest.get("evidence_count", len(evidence.get("evidence", evidence)) if isinstance(evidence, dict) else len(evidence)),
            "calculation_count": manifest.get("calculation_count", len(calculations.get("calculations", calculations)) if isinstance(calculations, dict) else len(calculations)),
            "stages": [{"stage": s.get("stage"), "status": s.get("status"), "validator_ok": s.get("validator_ok")} for s in stages if isinstance(s, dict)],
        },
        "hypotheses": [],
        "data_gaps": [f"run status={status}"] if status != "complete" else [],
        "evidence_refs": [
            str((run_dir / "manifest.json").relative_to(workspace)),
            str((run_dir / "evidence.json").relative_to(workspace)),
            str((run_dir / "calculations.json").relative_to(workspace)),
        ],
        "report_ref": str(report.resolve().relative_to(workspace)) if report.exists() else None,
        "source": "Vibe-Research",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Adapt a Vibe-Research run for EvoAlpha")
    parser.add_argument("run_dir", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    result = adapt(args.run_dir)
    output = args.output or ROOT / "outputs" / "team_artifacts" / f"{result['run_id']}-researcher.json"
    atomic_write(output, result)
    print(f"artifact={output} status={result['status']}")
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
