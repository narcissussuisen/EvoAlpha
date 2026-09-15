# EvoAlpha 运行手册

> status: active
> verified_at: 2026-09-15

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

## 每日自迭代批（22:00，YaobanDailyIteration）

流程：资料扫描 → 知识卡片 → 画像 → 提案（门槛判定）→ 影子回归。

手动运行（在 yaoban-system 目录，使用项目 venv 解释器）：

```
python scripts/daily_iteration.py --market-codes 1200 --market-cap 3000
```

常用参数：`--date`（批次日期）、`--market-start`（回测起点，默认 2026-04-01）、
`--no-portfolio`（跳过影子盘）、`--rules huigui,zthuicai`（只跑指定规则）。

产物：

| 文件 | 内容 |
|---|---|
| `outputs/iteration/<date>/digest.md` | **人读摘要（先看这个）** |
| `outputs/iteration/<date>/proposals.json` | 提案全量（含逐项门槛明细） |
| `outputs/iteration/<date>/shadow_regression.json` | 影子回归原始结果 |
| `outputs/iteration/<date>/knowledge_cards.md` | 累计知识卡片库 |
| `outputs/iteration/<date>/profile.md` | 选手画像（机读版） |
| `outputs/iteration_proposals/<date>.json` | 兼容既有消费方的同日提案 |
| `outputs/iteration/ledger.jsonl` | **参数生效台账（append-only）** |
| `outputs/iteration/<date>/parameter_patch.json` | 参数补丁**预览**（不自动落盘） |

红线与边界：

1. **parameter 类**过门槛自动生效——但只写台账 + 补丁预览，**不改写 `config/parameters.toml`**；
   落盘需人工确认（改 config 必须 bump `src/config.py` 的 `RULES_VERSION`）。
2. **rule / code / data 类**恒为 `pending_confirm`，永不自动生效。
3. 批处理只读资料与行情：**不写账本、不改门禁判定、不改生产代码**。
4. 证据不足（样本量/窗口未达门槛）判 `insufficient_evidence`，**不作为结论**，不得当作"通过"。

## 因子与模型研究

在 因子研究 中按对应实验 README 或脚本运行。实验产物与生产策略分离，未经验证不得直接进入组合。

## 行情、Agent 与监控

Vibe-Research 当前服务：API http://127.0.0.1:8766；UI http://127.0.0.1:5930；DSH Web http://127.0.0.1:3080。具体启动和验收以 Vibe-Research/README.md 与 VALIDATION_GATES.md 为准。

## 闭环

数据和看板 → 策略信号 → 模拟组合 → 风控与日志 → 周/月/季度复盘。
