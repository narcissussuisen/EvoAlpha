# EvoAlpha 交易与组合域

这里定义模拟交易、组合管理、交易日志和绩效复盘的统一归属。当前权威实现仍在 yaoban-system/，本目录作为 EvoAlpha 的正式入口和后续迁移目标。

## 当前权威实现

- 每日信号：yaoban-system/scripts/daily_pipeline.py
- 模拟回放：yaoban-system/scripts/paper_trade.py
- 交易日志：yaoban-system/src/journal/journal.py
- 盘前、盘中和组合看板：Vibe-Research/orchestrator/src/vr_trader.ts 与 desktop/
- 团队决策：EvoAlpha/agents/coordinator.py

## 运行边界

默认模式为 paper_only。交易计划、成交、持仓、盈亏和风控阻断必须持久化；任何策略晋级都需要样本外验证和风险门禁。
