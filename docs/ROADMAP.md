# EvoAlpha 差距分析与达标路线图

> 目标定义：EvoAlpha 作为由多个 AI 专业智能体组成的自主进化型量化投资团队，在模拟盘中独立完成**研究 → 决策 → 组合管理 → 交易执行 → 风险控制 → 复盘迭代**的完整系统。
>
> 本文档基于 2026-08-31（首个实盘交易日）的运行核查，给出差距矩阵与分阶段路线图。核查证据详见当日运行报告（计划任务状态、yaoban-system/outputs/、outputs/team_decisions/、agents/、Vibe-Research/.local/doctor/）。

---

## 一、目标能力分解

按 agents/artifact-contract.v1.json 的 7 角色与闭环 6 环节：

| 环节 | 责任角色 | 目标行为 | 每日/周期产物 |
|---|---|---|---|
| 研究 | researcher | 基于行情、新闻、行业链、情绪做市场研究 | researcher artifact（facts/hypotheses/data_gaps） |
| 策略 | strategy_researcher | 规则/因子验证、回测、walk-forward、晋级 | strategy_researcher artifact（promotion_status） |
| 决策 | trader + coordinator | 交易计划、执行假设、团队冲突裁决 | trader artifact + team_decision（decision/gates） |
| 组合 | portfolio_manager | 资金分配、持仓构建、组合约束 | portfolio_manager artifact |
| 风控 | risk_manager | 仓位/回撤/流动性/数据新鲜度门禁，独立阻断权 | risk_manager artifact（risk_status/blocking_reasons） |
| 执行 | yaoban 引擎 | 模拟成交、交易日志、净值 | ledger / fills / close_decision |
| 复盘 | reviewer | 绩效归因、失效模式、迭代提案 | reviewer artifact（iteration_proposal） |
| 进化 | evolution 域 | 提案 → 回测+样本外 → 模拟灰度 → 版本化 | 版本提案（promotion_requires 三项） |

---

## 二、现状 vs 目标差距矩阵（2026-08-31 核查）

图例：✅ 已达标 · 🟡 部分达标 · ❌ 未达标/缺失

| # | 能力 | 现状 | 差距 |
|---|---|---|---|
| 1 | **模拟交易执行** | ✅ yaoban 引擎自主执行：8/31 买入 300489@247（e4_support）→ 收盘净值 99,244.12（-0.76%），ledger/fills/close_decision 完整 | 无 |
| 2 | **规则风控** | ✅ 持仓/回撤/熔断阈值、盘中 risk_events（vwap_halve×3 alert_only）、preflight 门禁（TDX/日历/账本/看板 13 项） | 无 |
| 3 | **计划任务调度** | 🟡 19 个 Yaoban 任务+2 个 Vibe 任务注册并运行；3 处异常：PlanGate TDX bars=0 失败（08:55）、NextPlan mode 错误（17:10）、Rebuild 首日耗时 30min+、trader_daily rc=1 | 容错与配置修正 |
| 4 | **数据层（Vibe-Research）** | 🟡 交易日历 skill 被 yaoban 真实调用；RSS 新闻采集正常；看板 8766/5930 在线；**DEEPSEEK_API_KEY 未设置 → Agent 研究运行时不可用（doctor 2 fail）**；行情走 TDX/腾讯直连未入 Vibe | 研究运行时未启用；行情数据未统一 |
| 5 | **研究员（每日研究）** | 🟡 仅 1 个真实 researcher artifact（8/29 转化），**无每日研究产物**；Vibe 6 个 skills、117 个数据源端点未投入每日循环 | 研究层未进闭环 |
| 6 | **策略研究员** | 🟡 策略 v5.0（R1' 上升回档选手 v24、抄底买点 4 规则、R2' 回踩低吸）已落地并接入生产；walk-forward 验证为历史产物；**无新策略验证循环** | 无周期验证、无晋级流程 |
| 7 | **交易员（LLM 决策）** | ❌ 交易决策=引擎规则直接执行（autonomous_paper 授权），**无交易员 artifact 参与每日决策**（现有 trader artifact 为 paper 测试） | 智能体决策缺失 |
| 8 | **组合经理** | ❌ 组合约束为 policy 硬编码（max_positions=2、max_new_buys_per_day=1 等），**无组合层智能体意见**（现有 artifact 为 paper 测试） | 智能体组合层缺失 |
| 9 | **风控员（独立裁决）** | 🟡 规则风控在跑，但 **risk_manager artifact 为零**，无独立风险意见与阻断记录（阻断权仅实现为代码 gate） | 风控角色产物缺失 |
| 10 | **团队协调器** | 🟡 确定性 coordinator 已实现（契约校验+风控门禁，paper_only 不提交真实订单）；**仅 1 次 smoke 测试（08:53），无真实输入**；未注册任何计划任务 | 未接入每日流程 |
| 11 | **复盘学习** | ❌ trader_daily 生成失败（rc=1）；**无 reviewer 复盘产物**（仅 1 份 historical 转化）；"计划外标的（盘中捕捉）偏离"审计已出现但无归因动作 | 复盘闭环缺失 |
| 12 | **进化迭代** | ❌ outputs/iterations/ 仅 8/24 旧提案；**无 8/31 之后任何迭代提案/版本记录**；学习资料（成交量六种形态）未进入验证管线 | 进化闭环缺失 |
| 13 | **自主度治理** | 🟡 autonomous_paper 授权 + 风控熔断（drawdown 10% 暂停 / 15% 终止）雏形在；无"人审—半自主—自主"分级与升级/回滚机制 | 治理机制未建立 |

**差距根因归纳：**

1. **运行时缺口**：模型运行时（Vibe-Research run.ts / function-calling）因密钥缺失不可用，导致"智能体产出角色意见"这一环节整体空转 —— 团队协议（contract）就绪但无人供数。
2. **流程缺口**：计划任务只覆盖 yaoban 引擎（数据→信号→执行），**没有 EvoAlpha 团队任务**（无盘前研究任务、无盘后团队门禁任务、无复盘任务）。
3. **闭环缺口**：执行与规则风控已闭环，但"研究→决策→复盘→进化"四环未接；复盘失败（trader_daily rc=1）会直接中断进化输入。
4. **能力缺口**：协调器为确定性门禁（正确设计），但角色意见生成、冲突裁决、迭代提案等 LLM 能力尚未实例化。

---

## 三、路线图（四阶段）

### Phase 0 — 基线稳固（第 1–2 周）｜目标：零任务失败、运行时可用

| 任务 | 说明 | 完成标准 |
|---|---|---|
| 修 YaobanNextPlan | 删除或改 mode（next-plan 已并入 rebuild 链） | 17:10 不再报错/推送 |
| 修 trader_daily rc=1 | 排查收盘子任务失败根因（day_pnl null 路径） | close 全子任务 rc=0 |
| TDX 开盘前容错 | bars=0 时允许重试/降级而非 fail-closed（仅开市前） | 无 08:55 类连锁阻塞 |
| 启用模型运行时 | 设置 DEEPSEEK_API_KEY 环境变量，跑通 1 次 Vibe-Research 研究 run | doctor 0 fail；产出 1 个真实 researcher artifact |
| Rebuild 耗时观察 | fetch_daily_minute_rebuild 增量/并行化评估 | 收盘后 30 分钟内完成 |
| 确认 acceptance 首跑 | 19:10 YaobanDailyAcceptance 连续 3 日通过 | acceptance_<date>.json 归档 |

**验收**：连续 5 个交易日计划任务 0 失败、doctor 全绿、每日产物完整。

### Phase 1 — 研究层进闭环（第 2–4 周）｜目标：智能体开始供数

| 任务 | 说明 | 完成标准 |
|---|---|---|
| 盘前研究任务 | 新增计划任务（如 07:30）：Vibe-Research run → adapt-run → researcher artifact（evidence/manifest 保留） | 每个交易日自动生成 researcher artifact |
| 盘后报告转化 | adapt-report（walkforward→strategy_researcher）、adapt-paper（paper_trade→trader/portfolio_manager）、复盘转化（→reviewer）定时执行 | 5 类角色 artifact 自动归档 |
| 研究→策略衔接 | researcher facts/hypotheses 进入 plan_daily 候选池或情绪表更新流程（先只读参考） | 研究产物被引用（引用计数>0） |
| 数据源接入 | 接入行业链/催化剂/估值等 Vibe 端点，形成每日研究包 | 研究包含 ≥3 类外部数据证据 |

**验收**：连续 10 个交易日研究产物自动生成、进入团队输入目录且 schema 校验通过。

### Phase 2 — 团队每日决策链（第 3–6 周）｜目标：智能体团队真实参与决策

| 任务 | 说明 | 完成标准 |
|---|---|---|
| 盘后团队门禁任务 | 新增计划任务（如 16:15）：汇总当日 artifacts → cli.py team → team_decisions/<date>.json | 每日真实 team_decision（非 fixture） |
| 风控员裁决 | risk_manager artifact：基于 risk_events/drawdown/数据新鲜度给出 risk_status 与阻断理由 | 每日风险意见归档；与引擎 gate 结果交叉验证 |
| 组合经理意见 | 基于策略信号+研究员输入给出组合建议（advisory，只读） | 每日组合建议归档 |
| 决策一致性验证 | team_decision 与 yaoban 引擎执行对比（方向/标的/仓位） | ≥10 日一致率报告 |
| 看板集成 | 团队决策/风控裁决/复盘展示进 Vibe 看板 | 看板新增团队区块 |

**验收**：连续 10 个交易日真实团队决策产出，决策链完整（研究→决策→执行→日志），一致率≥80%（不一致需解释记录）。

### Phase 3 — 复盘进化闭环（第 2 个月起）｜目标：学习→验证→晋级→版本化跑通

| 任务 | 说明 | 完成标准 |
|---|---|---|
| 每日/每周复盘 | reviewer 聚合 trader_daily+绩效归因（基准 000852.SH）→ 复盘报告 → iteration_proposal | 每周复盘报告+提案入库（evolution/proposals/） |
| 学习资料转化 | 成交量六种形态等知识卡片 → 规则草稿 → 案例回归 → 回测+walk-forward → 模拟灰度 | 首个"学习→策略版本"晋级案例 |
| 晋级门禁 | 落实 promotion_requires 三项（样本外验证+风控门禁+版本化记录） | 晋级记录含证据链与回滚路径 |
| 失败可见 | 计划外买入（如 8/31 300489"偏离"）进入归因与规则修正流程 | 每次偏离有归因记录与规则动作 |

**验收**：第一个学习驱动的策略版本晋级完成；月度进化报告；绩效归因周报自动化。

### Phase 4 — 自主度升级与治理（第 3 个月起）｜目标：渐进自主、可治理

| 任务 | 说明 | 完成标准 |
|---|---|---|
| 自主度分级 | advisory（研究参考）→ co-sign（团队决策与引擎一致才执行）→ autonomous（团队裁决覆盖规则信号，风控保留阻断权），逐级灰度 | 分级矩阵文档+每级≥20 交易日验证 |
| 组合管理自动化 | 组合经理进入资金分配/持仓构建决策（受 policy 硬约束） | 组合层决策可归因 |
| 熔断与回滚 | 完善 circuit_break（暂停/终止）与提案回滚机制 | 压测演练通过 |
| 季度评估 | 智能体决策 vs 规则引擎的独立盈亏贡献归因 | 季度评估报告 |

**验收**：完整闭环（研究→决策→组合→执行→风控→复盘→进化）连续运行一个季度，各角色产物可追溯、决策贡献可归因。

---

## 四、里程碑总览

| 里程碑 | 时间 | 关键交付 |
|---|---|---|
| M0 基线稳固 | 2026-09 第 1–2 周 | 任务 0 失败、运行时可用 |
| M1 研究闭环 | 2026-09 第 3–4 周 | 每日 5 类角色 artifact 自动生成 |
| M2 团队决策 | 2026-10 第 1–4 周 | 每日真实 team_decision + 风控/组合意见 |
| M3 进化闭环 | 2026-11 起 | 首个学习→策略版本晋级、周复盘 |
| M4 自主升级 | 2026-12 起 | 分级自主、季度评估报告 |

---

## 五、风险与治理

| 风险 | 应对 |
|---|---|
| 智能体研究产出数据漂移/幻觉 | artifact-contract 强制 evidence_refs；historical/complete 状态校验；风控阻断权保留在确定性层 |
| 团队决策与引擎不一致 | Phase 2 先 advisory + 一致率报告；Phase 4 才允许覆盖 |
| 密钥/运行时不可用导致空转 | Phase 0 硬性前置（DEEPSEEK_API_KEY）；doctor 纳入每日 preflight 检查项 |
| 复盘中断进化输入 | trader_daily rc=1 列入 Phase 0 P0 修复；复盘产物缺失自动告警 |
| 过度自主 | 分级灰度 + 熔断阈值（10%/15%）+ 版本回滚路径 |

---

## 六、立即行动清单（本周）

1. 修 YaobanNextPlan（mode 配置）与 trader_daily rc=1 —— 运营止损
2. 配置 DEEPSEEK_API_KEY 并跑通一次 Vibe-Research run —— 解锁智能体运行时
3. 新增第一个团队任务原型：盘后 16:15 汇总当日报告 → 转化 artifacts → coordinator 冒烟（advisory）
4. 建立每日"闭环健康检查"：preflight 增加团队产物存在性检查
