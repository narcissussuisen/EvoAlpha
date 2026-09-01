"""EvoAlpha unified workspace entrypoint."""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
YAOBAN = ROOT / "yaoban-system"
VIBE = ROOT / "Vibe-Research"


def run_python(script: str, args: list[str]) -> int:
    command = [sys.executable, str(YAOBAN / "scripts" / script), *args]
    return subprocess.run(command, cwd=YAOBAN, check=False).returncode


def run_node(script: pathlib.Path, args: list[str]) -> int:
    command = ["node", str(script), *args]
    return subprocess.run(command, cwd=VIBE, check=False).returncode


def show_status() -> int:
    decisions = ROOT / "outputs" / "team_decisions"
    decision_count = len(list(decisions.glob("*.json"))) if decisions.exists() else 0
    print("EvoAlpha")
    print("  mission: multi-agent autonomous A-share quant team")
    print("  mode: simulated trading and continuous strategy evolution")
    print(f"  learning: {ROOT / '选手学习资料'}")
    print(f"  strategy_core: {YAOBAN}")
    print(f"  factor_lab: {ROOT / '因子研究'}")
    print(f"  data_and_dashboard: {VIBE}")
    print("  compatibility: enabled")
    print(f"  team_decisions: {decision_count}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="evoalpha", description="EvoAlpha unified workspace CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status", help="show module map and migration status")
    sub.add_parser("learning", help="show the player-methodology learning entry")
    sub.add_parser("health", help="run the Vibe-Research environment doctor")
    sub.add_parser("compat", help="run the parallel-validation compatibility check")
    research = sub.add_parser("research", help="start a structured Vibe-Research run")
    research.add_argument("--symbol", required=True)
    research.add_argument("--market", default="SZ")
    research.add_argument("--run-id", default="")
    scan = sub.add_parser("scan", help="run the existing A-share daily signal pipeline")
    scan.add_argument("--date", default="")
    scan.add_argument("--update", action="store_true")
    scan.add_argument("--top", type=int, default=0)
    paper = sub.add_parser("paper-trade", help="run the existing simulated portfolio replay")
    paper.add_argument("--start", required=True)
    paper.add_argument("--end", required=True)
    review = sub.add_parser("review", help="run a simulated portfolio review")
    review.add_argument("--start", required=True)
    review.add_argument("--end", required=True)
    team = sub.add_parser("team", help="coordinate role artifacts through the paper-trading risk gate")
    team.add_argument("input", type=pathlib.Path)
    team.add_argument("--researcher-artifact", type=pathlib.Path, default=None)
    team.add_argument("--artifact", action="append", default=[], help="role=path JSON artifact; repeatable")
    team.add_argument("--output", type=pathlib.Path, default=None)
    adapt = sub.add_parser("adapt-run", help="adapt a Vibe-Research run into a researcher artifact")
    adapt.add_argument("run_dir", type=pathlib.Path)
    adapt.add_argument("--output", type=pathlib.Path, default=None)
    adapt_report = sub.add_parser("adapt-report", help="adapt a yaoban report into a role artifact")
    adapt_report.add_argument("report", type=pathlib.Path)
    adapt_report.add_argument("--role", choices=["strategy_researcher", "reviewer"], required=True)
    adapt_report.add_argument("--output", type=pathlib.Path, default=None)
    adapt_paper = sub.add_parser("adapt-paper", help="adapt a paper-trade report into trader/portfolio artifacts")
    adapt_paper.add_argument("report", type=pathlib.Path)
    adapt_paper.add_argument("--role", choices=["trader", "portfolio_manager"], required=True)
    adapt_paper.add_argument("--output", type=pathlib.Path, default=None)
    sub.add_parser("walkforward", help="run the existing out-of-sample validation")

    args = parser.parse_args()
    if args.command == "status":
        return show_status()
    if args.command == "learning":
        print(ROOT / "learning" / "README.md")
        print(ROOT / "选手学习资料" / "README.md")
        return 0
    if args.command == "health":
        return run_node(VIBE / "orchestrator" / "src" / "doctor.ts", [])
    if args.command == "compat":
        return subprocess.run([sys.executable, str(ROOT / "agents" / "compat_check.py")], cwd=ROOT, check=False).returncode
    if args.command == "research":
        forwarded = ["--symbol", args.symbol, "--market", args.market]
        if args.run_id:
            forwarded += ["--run-id", args.run_id]
        return run_node(VIBE / "orchestrator" / "src" / "run.ts", forwarded)
    if args.command == "scan":
        forwarded = []
        if args.date:
            forwarded += ["--date", args.date]
        if args.update:
            forwarded.append("--update")
        if args.top:
            forwarded += ["--top", str(args.top)]
        return run_python("daily_pipeline.py", forwarded)
    if args.command in {"paper-trade", "review"}:
        return run_python("paper_trade.py", ["--start", args.start, "--end", args.end])
    if args.command == "team":
        command = [sys.executable, str(ROOT / "agents" / "coordinator.py"), str(args.input.resolve())]
        if args.researcher_artifact:
            command += ["--researcher-artifact", str(args.researcher_artifact.resolve())]
        for artifact in args.artifact:
            command += ["--artifact", artifact]
        if args.output:
            command += ["--output", str(args.output.resolve())]
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    if args.command == "adapt-run":
        command = [sys.executable, str(ROOT / "agents" / "adapt_vibe_run.py"), str(args.run_dir.resolve())]
        if args.output:
            command += ["--output", str(args.output.resolve())]
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    if args.command == "adapt-report":
        command = [sys.executable, str(ROOT / "agents" / "adapt_yaoban_report.py"), str(args.report.resolve()), "--role", args.role]
        if args.output:
            command += ["--output", str(args.output.resolve())]
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    if args.command == "adapt-paper":
        command = [sys.executable, str(ROOT / "agents" / "adapt_paper_trade.py"), str(args.report.resolve()), "--role", args.role]
        if args.output:
            command += ["--output", str(args.output.resolve())]
        return subprocess.run(command, cwd=ROOT, check=False).returncode
    if args.command == "walkforward":
        return run_python("run_walkforward.py", [])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
