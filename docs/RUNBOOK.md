# EvoAlpha 运行手册

## A 股策略与模拟盘

在 yaoban-system 目录运行：

- python scripts/verify_env.py
- python scripts/daily_pipeline.py --update
- python scripts/paper_trade.py --start YYYY-MM-DD --end YYYY-MM-DD
- python scripts/run_walkforward.py

Phase 0（2026-09-01）后新增契约：

- **买入时序与决策 provenance**（P0.2/P0.4）：所有买入必须携带可解析 decision_id + signal_ts/decision_ts（120 秒新鲜度、成交因果、单调性，见 `yaoban-system/portfolio/timing_contract.py`）；计划外买入须显式理由。盘中扫描读取当日计划，计划缺失 fail-closed。
- **卖出执行契约**（B0-P0-3）：触发源×生产/影子状态×执行契约矩阵见 `yaoban-system/docs/SELL_EXECUTION_CONTRACT.md`；盘中卖出唯一执行器为 tick_monitor（--execute-risk）。
- **日验收**（P0.5）：正式验收报告仅由 16:30 盘后链产出（`--final`，首份优先不可覆盖）；手动/凌晨运行一律写 probe 文件。证据失效表：`yaoban-system/docs/loops/evidence_invalidation.json`（晋级器经 `src/evidence_guard.py` 硬拒命中路径）。
- **账本红线**：ledger.json append-only；历史 fill（含两笔 pre-fix 缺陷证据）永不回改。

## 因子与模型研究

在 因子研究 中按对应实验 README 或脚本运行。实验产物与生产策略分离，未经验证不得直接进入组合。

## 行情、Agent 与监控

Vibe-Research 当前服务：API http://127.0.0.1:8766；UI http://127.0.0.1:5930；DSH Web http://127.0.0.1:3080。具体启动和验收以 Vibe-Research/README.md 与 VALIDATION_GATES.md 为准。

## 闭环

数据和看板 → 策略信号 → 模拟组合 → 风控与日志 → 周/月/季度复盘。
