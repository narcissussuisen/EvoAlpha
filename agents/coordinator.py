"""Deterministic EvoAlpha team coordinator for paper-trading decisions.

The model runtime may provide role opinions, but this module owns the final
contract checks and risk gate. It never submits real orders.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "agents" / "artifact-contract.v1.json"
REQUIRED_ROLES = [
    "researcher",
    "strategy_researcher",
    "trader",
    "portfolio_manager",
    "risk_manager",
    "coordinator",
]


def load_payload(path: pathlib.Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("team input must be a JSON object")
    return payload


def coordinate(payload: dict) -> dict:
    roles = payload.get("roles", {})
    if not isinstance(roles, dict):
        roles = {}
    missing = [role for role in REQUIRED_ROLES if not isinstance(roles.get(role), dict)]
    risk = roles.get("risk_manager") if isinstance(roles.get("risk_manager"), dict) else {}
    blocks = list(payload.get("blocking_reasons", [])) if isinstance(payload.get("blocking_reasons", []), list) else []
    blocks.extend(risk.get("blocking_reasons", []))
    risk_status = str(risk.get("risk_status", "unknown"))
    if risk_status in {"blocked", "fail", "failed"}:
        blocks.append(f"risk_manager status={risk_status}")
    for role, artifact in roles.items():
        if not isinstance(artifact, dict) or role == "risk_manager":
            continue
        if "status" not in artifact:
            continue
        artifact_status = str(artifact["status"])
        if artifact_status != "complete":
            blocks.append(f"{role} artifact status={artifact_status}")
    if missing:
        blocks.append("missing roles: " + ", ".join(missing))
    trader = roles.get("trader") if isinstance(roles.get("trader"), dict) else {}
    orders = payload.get("orders", [])
    if not orders and isinstance(trader.get("orders"), list):
        orders = trader["orders"]
    decision = "blocked" if blocks else "paper_execute"
    return {
        "schema_version": "evoalpha.team-decision.v1",
        "run_id": str(payload.get("run_id", "")),
        "as_of": str(payload.get("as_of", dt.date.today().isoformat())),
        "mode": "paper_only",
        "decision": decision,
        "roles_present": sorted(roles),
        "required_roles": REQUIRED_ROLES,
        "risk_status": risk_status,
        "blocking_reasons": blocks,
        "orders": [] if decision == "blocked" else orders,
        "real_order_submission": False,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def persist(path: pathlib.Path, encoded: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp") as handle:
        handle.write(encoded)
        handle.flush()
        temp = pathlib.Path(handle.name)
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Coordinate EvoAlpha paper-trading role artifacts")
    parser.add_argument("input", type=pathlib.Path, help="team input JSON")
    parser.add_argument("--output", type=pathlib.Path, help="write decision JSON")
    parser.add_argument("--researcher-artifact", type=pathlib.Path, help="legacy researcher artifact option")
    parser.add_argument("--artifact", action="append", default=[], help="role=path JSON artifact; repeatable")
    args = parser.parse_args()
    payload = load_payload(args.input)
    if args.researcher_artifact:
        payload.setdefault("roles", {})["researcher"] = load_payload(args.researcher_artifact)
    for spec in args.artifact:
        role, separator, raw_path = spec.partition("=")
        if not separator or not role or not raw_path:
            raise ValueError(f"invalid --artifact {spec!r}; expected role=path")
        payload.setdefault("roles", {})[role] = load_payload(pathlib.Path(raw_path))
    result = coordinate(payload)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    output = args.output
    if output is None:
        run_id = result["run_id"] or dt.datetime.now().strftime("run-%Y%m%dT%H%M%S")
        output = ROOT / "outputs" / "team_decisions" / f"{run_id}.json"
    persist(output, encoded)
    print(f"decision={result['decision']} output={output}")
    return 0 if result["decision"] == "paper_execute" else 2


if __name__ == "__main__":
    raise SystemExit(main())
