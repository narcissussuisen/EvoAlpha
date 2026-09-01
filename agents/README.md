# EvoAlpha 多智能体团队

EvoAlpha 采用角色分工。每个角色输出结构化意见，团队协调器汇总冲突并形成模拟交易决策。

| 角色 | 职责 | 产物 |
|---|---|---|
| 研究员 | 市场、行业、个股、资金和情绪研究 | 研究包、证据、假设 |
| 策略研究员 | 方法论、因子、规则和回测 | 策略版本、验证报告 |
| 交易员 | 入场、退出和执行时机 | 模拟交易计划、成交记录 |
| 组合经理 | 组合构建、资金分配、持仓和策略配比 | 组合方案、绩效归因 |
| 风控员 | 仓位、回撤、流动性、数据新鲜度和失效门禁 | 风控裁决、阻断理由 |
| 复盘学习员 | 归因交易结果，提出改进 | 复盘报告、迭代提案 |
| 团队协调器 | 汇总意见，保证决策链完整 | 决策记录、运行清单 |

## 决策顺序

研究 → 策略验证 → 交易计划 → 组合审查 → 风控门禁 → 模拟执行 → 复盘学习

风控员拥有阻断权；组合经理负责组合层取舍；交易员不能绕过策略约束；复盘学习员不能直接修改生产参数。

Vibe-Research 的真实研究运行可通过 EvoAlpha/cli.py adapt-run <run-dir> 转换为 researcher artifact，保留 manifest、evidence、calculations、report 引用和 incomplete 状态；yaoban-system 的已验证报告可通过 EvoAlpha/cli.py adapt-report <report.md> --role strategy_researcher|reviewer 转换为带 historical 标记的策略研究员/复盘员 artifact。team 命令通过 --artifact role=path（旧 --researcher-artifact 继续兼容）合并多个角色产物；任何明确声明且不是 complete 的角色 artifact 都会自动阻断模拟执行。具体编排优先复用 Vibe-Research/orchestrator 和 DSH/function-calling，避免重复建设第二套 Agent 基础设施。
