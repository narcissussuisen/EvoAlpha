"""EvoAlpha parallel-validation / compatibility checker.

Machine-checkable gate that verifies legacy module paths, the EvoAlpha control
plane, local services and CLI wiring. Writes a JSON report; exits 0 when all
required checks pass, 1 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import socket
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT.resolve()

REQUIRED_LEGACY = [
    "yaoban-system",
    "因子研究",
    "Vibe-Research",
    "选手学习资料",
    "妖板选手方法论拆解",
]
REQUIRED_EVO = [
    "README.md",
    "cli.py",
    "docs/SYSTEM_MAP.md",
    "docs/MIGRATION.md",
    "docs/RUNBOOK.md",
    "agents/README.md",
    "agents/artifact-contract.v1.json",
    "agents/coordinator.py",
    "agents/adapt_vibe_run.py",
    "agents/adapt_yaoban_report.py",
    "agents/adapt_paper_trade.py",
    "learning/README.md",
    "research/README.md",
    "trading/README.md",
    "evolution/README.md",
]
CLI_COMMANDS = ["status", "learning", "health", "compat", "research", "scan", "paper-trade", "review", "team", "adapt-run", "adapt-report", "adapt-paper", "walkforward"]
SERVICE_PORTS = [8766, 5930, 8765, 3080]


def check_path(rel: str) -> bool:
    return (WORKSPACE / rel).exists()


def check_port(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def check_cli_help() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "cli.py"), "--help"],
            capture_output=True, text=True, timeout=30,
        )
        ok = proc.returncode == 0 and all(cmd in proc.stdout for cmd in CLI_COMMANDS)
        return ok, (proc.stdout[:200] if ok else proc.stderr[:300])
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="EvoAlpha compatibility check")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    legacy = {rel: check_path(rel) for rel in REQUIRED_LEGACY}
    evo = {rel: check_path(rel) for rel in REQUIRED_EVO}
    services = {str(port): check_port(port) for port in SERVICE_PORTS}
    cli_help_ok, cli_note = check_cli_help()

    report = {
        "schema_version": "evoalpha.compat-check.v1",
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "legacy_paths": legacy,
        "evoalpha_entries": evo,
        "services": services,
        "cli_wiring": {"help_ok": cli_help_ok, "commands": CLI_COMMANDS, "note": cli_note},
        "summary": {
            "legacy_missing": [k for k, v in legacy.items() if not v],
            "evo_missing": [k for k, v in evo.items() if not v],
            "services_down": [k for k, v in services.items() if not v],
            "cli_ok": cli_help_ok,
        },
    }
    output = args.output or ROOT / "outputs" / "validation" / f"compat-check-{dt.date.today().isoformat()}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    tmp = output.with_suffix(".tmp")
    tmp.write_text(encoded, encoding="utf-8")
    tmp.replace(output)
    print(f"report={output}")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    ok = not report["summary"]["legacy_missing"] and not report["summary"]["evo_missing"] and report["summary"]["cli_ok"]
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
