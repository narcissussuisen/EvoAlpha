# EvoAlpha 系统地图

> status: active
> verified_at: 2026-09-15

> **2026-09-12 更新（v2.0 全系统重构）**：架构由「学习→因子→数据→策略→团队→进化」链式模型，
> 改为**五层架构**（人格 / 决策环 / 执行 / 数据 / 学习与治理）。
> 权威：`docs/EVOALPHA_V2_RESTRUCTURE_PLAN.md`。
> 最终目标：**EvoAlpha = 妖板选手决策过程的可执行复刻体，在一套可审计的账本上自主跑 A 股短线，用它自己的前向净值证明有效。**

## 目标架构（五层）

```
L1 人格层 Persona
   SOP 知识库(战法谱系 × 决策环六段) · 裁量点定义 · 容差带 · 记忆 · 自述 · 版本
        ↓ 决策环定义 + SOP 约束
L2 决策环 Decision Loop（盘中实时，六段）
   环境闸门 → 定主线 → 选真龙 → 找低吸 → 稳持仓 → 仓位
        ↓ 结构化决策 artifact（含 LLM 裁量理由，可重放）
L3 执行层 Execution
   订单 / 单一主账本 · 风控 veto · 秒级 tick 守护 · 盘后价格窗口 · 费用模型
        ↓ fills / 净值
L4 数据层 Data
   全市场日线 · 候选池实时 1m · 板块题材 · 资金流 · 情绪表
        ↓
L5 学习与治理 Learning & Governance
   选手标签库 · 归因 · 净值判定器(vs 市场基准臂) · 版本分段 · 回滚 · 诊断轨(命中率)
```

> 命名沿革：EvoAlpha 是同一项目三次命名——逐妖交易团队（2026-08-29）→ 妖板系统（策略内核）→ EvoAlpha（2026-08-31）。详见 `EVOALPHA_VISION_ALIGNMENT.md §1.7`。
> ⚠️ 架构级分离（必须守住）：**行为复刻 ≠ 收益来源**。命中率只作诊断轨，净值才是晋级闸门。

## 模块职责

| 层 | 权威模块 | 主要输出 | 状态 |
|---|---|---|---|
| L1 人格 | `yaoban-system/config/parameters.toml`（**已有 37 条规则 + 证据等级 + 视频出处**）、`选手学习资料/` | SOP 规则表、裁量点清单、容差带、人格记忆与自述 | 素材就绪，结构化待施工（R1） |
| L2 决策环 | `yaoban-system/scripts/plan_daily.py`、`scan_and_confirm.py`、`src/core/sell.py` | 六段决策 artifact（含 LLM 裁量理由） | 现为固定阈值规则引擎；LLM 裁量层 + 盘中决策服务待建（R3/R4） |
| L3 执行 | `yaoban-system/portfolio/`、`scripts/tick_monitor.py`、`scripts/_tick_watch.py` | fills、持仓、净值、风控裁决 | 生产在跑；主账本 / 卖点接入 / 盘后窗口待建（R0） |
| L4 数据 | `yaoban-system/src/data/qfq_store.py`、`scripts/fetch_daily_*`、`Vibe-Research/` | 日线、分钟、板块、资金流、情绪 | 日线仅 112 交易日、分钟仅 970 只（R2 扩建） |
| L5 学习治理 | `yaoban-system/src/iteration/`（cards/gate/intraday/shadow/rules/proposals） | 选手标签库、归因、净值判定、版本 registry | 自迭代内核已成型；净值判定器待建（R5） |

## 归档区

同级 `../evoalpha_all/` = 冗余资料外迁区（因子研究 / 妖板选手方法论拆解 / 抽帧中间产物 / 依赖回滚备份）。
见 `../evoalpha_all/MANIFEST.md`。EvoAlpha 保留范围的唯一判据 = 是否服务于最终目标。

## 状态

冗余已外迁，EvoAlpha 收敛为 yao 本体（30 GB → 2.71 GB）。**生产不暂停**，18 个 Yaoban 计划任务照常运行。
控制平面（`agents/` 契约与协调器）、学习入口（`learning/`）、自迭代内核（`yaoban-system/src/iteration/`）已就绪；
v2.0 施工待批准后按 **R0 →（R1 ∥ R2）→ R3 → R4 → R5** 推进。
