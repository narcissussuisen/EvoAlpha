# EvoAlpha 系统地图

## 目标架构

选手学习资料
  ↓ 知识卡片、案例、规则草稿
因子研究 → 因子、模型、回测和假设验证
  ↓
Vibe-Research 数据与 Agent 运行时 → 实时行情、外部数据、研究工具、监控 UI
  ↓
yaoban-system 策略与组合内核 → A 股短线策略、信号、模拟组合、交易日志
  ↓
EvoAlpha 多智能体团队 → 研究、交易、组合、风控、复盘协作
  ↓
模拟交易进化闭环 → 绩效归因、门禁、提案、版本化

> 命名沿革：EvoAlpha 是同一项目三次命名——逐妖交易团队（2026-08-29）→ 妖板系统（策略内核）→ EvoAlpha（2026-08-31）。详见 EVOALPHA_VISION_ALIGNMENT.md §1.7。

## 模块职责

| 域 | 权威模块 | 主要输出 |
|---|---|---|
| 学习 | EvoAlpha/learning/ + 选手学习资料/ | 方法论、知识卡片、案例 |
| 因子与模型 | EvoAlpha/research/ + 因子研究/ | 因子、模型、实验报告 |
| 数据与监控 | Vibe-Research/ | 结构化证据、实时快照、监控 UI |
| 策略与信号 | yaoban-system/src/core/ | 信号、环境分、候选池 |
| 组合与模拟交易 | EvoAlpha/trading/ + yaoban-system/ | 模拟成交、持仓、绩效、合规记录 |
| 进化与复盘 | EvoAlpha/evolution/ | 绩效归因、迭代提案、版本记录 |
| 团队控制 | EvoAlpha/agents/ | 决策记录、冲突、风控裁决 |

## 状态

控制平面已建立；学习入口已接入；策略核心、因子实验室、数据采集与看板通过索引接入；多智能体角色协议已建立，编排层优先复用 Vibe-Research 的 DSH/function-calling 运行时。
