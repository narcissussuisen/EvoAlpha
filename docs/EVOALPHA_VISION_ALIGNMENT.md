# EvoAlpha 愿景对齐与双路线图并轨（Vision Alignment）

> 状态：2026-09-01 依据用户提供的重构会话记录（`docs/source_material/session-2026-08-31-evoalpha-restructure.jsonl`，sha256 `f9cf7a4e6f3c3bb49a5b59eef267ea2bb0f8e9b6da0c981b61551dc057fa16f9`，7,137,181 字节）与 ROADMAP.md / SYSTEM_MAP.md 交叉核对后固化
> 用途：为 `YAOBAN_AGENT_BASELINE_AND_PHASE1_BLUEPRINT.md`（已批准施工图）提供愿景锚点；回答"往哪个方向做、如何做"

## 1. EvoAlpha 愿景一页纸（用户原意提炼）

**定位**：面向 A 股短线交易的**多智能体自主量化投资团队与模拟交易进化平台**。

1. **自主性**：团队全权管理模拟盘，独立完成 研究 → 决策 → 组合管理 → 交易执行 → 风险控制 → 复盘迭代 的完整闭环；系统**不是**人工复核辅助工具（用户在会话中明确纠正过这一点）；不含真实资金。
2. **进化机制**：自迭代学习获取稳定超额收益——绩效归因 → 门禁 → 迭代提案 → 版本化晋级/回滚；角色成长影响决策权重、记忆、SOP、工具权限与风险预算。
3. **学习对象**：妖板选手（吸收为 EvoAlpha 自有策略，不建永久模仿人格）。
4. **五层架构**（SYSTEM_MAP 已固化）：
   - 选手学习资料 + 妖板选手方法论拆解 → 学习入口（index + OCR + 规则 + case 库）
   - 因子研究 → 研究员的因子与模型实验室
   - Vibe-Research → 实时行情与外部数据采集层 + **人类监控看板**（8766/5930/8765）
   - yaoban-system → 策略与组合内核（调度、信号、模拟成交、账本）
   - EvoAlpha agents → 团队控制平面（artifact 契约、协调器门禁、统一 CLI）
5. **人类角色**：通过看板监控运行情况；不逐单审批。
6. **现状基线**：控制平面骨架已建（契约/协调器/CLI/compat 全绿），但智能体供数整体空转（无每日 researcher artifact、无 LLM 交易决策、复盘失败、进化闭环缺失）——即蓝图 §1 的审计结论。
7. **命名沿革**：EvoAlpha 是同一项目的三次命名——逐妖（2026-08-29 团队代号，10 万模拟盘）→ 妖板系统/yaoban-system（策略内核名）→ EvoAlpha（2026-08-31 重构确立）。三者同一实体，非并列项目；2026-09-09 生产代码统一改名 EvoAlpha。

## 2. 愿景 → 施工图映射

| 愿景要素 | 蓝图落点（已批准） | ROADMAP 落点（08-31） | 状态 |
|---|---|---|---|
| 真·多智能体团队（独立输入/记忆/观点/权限/绩效） | §6 六角色 + §6.1 决策契约 | 差距矩阵 #5-#10 | 蓝图 1C 施工 |
| 模拟盘全权自主 + 不碰真实资金 | §2 权限、§11 禁区 | autonomous_paper 授权 + paper_only | 一致 |
| 自迭代学习（可证伪、防择优） | §8 实验契约 + 20 标签日门禁 + v0 克隆/4 版本上限 | 差距矩阵 #12-#13 | 蓝图 1B/1D |
| 学习选手 → 自有策略 | §5 证据等级 + §7 双 Top 5 + 选手标签 | 学习入口接入 | 蓝图 1A/1B |
| 进化闭环（归因→提案→版本化→回滚） | §8.3 晋级门禁 + canary + rollback | Phase 3-4 | 蓝图 1D |
| 研究层供数（每日 researcher artifact） | 蓝图未展开（六角色"专属输入"隐含） | Phase 1 盘前研究任务 + adapt-run/ adapt-report | **缺口：排期待定** |
| 模型运行时（DEEPSEEK_API_KEY / function-calling） | 蓝图未覆盖 | Phase 0 任务 | **缺口：排期待定** |
| 数据采集统一入 Vibe | 蓝图未显式（09:14/09:39 快照数据源待定） | 差距 #4"行情未入 Vibe" | 建议随 1B 落实 |

## 3. 双路线图并轨规则（关键澄清）

`ROADMAP.md`（08-31，系统运行能力全景差距）与蓝图（09-01，选股学习闭环施工图）**并存且任务有交叠**，并轨规则：

1. **交叠区以蓝图为准**：close 链修复 / trader_daily rc=1 / 任务失败治理——蓝图 Phase 0 已批准、已开工、已冻结 hash（blueprint v1.0 `cdd22991...3943` + baseline-0-pre-fix manifest `552fa823...5be`），执行粒度更细。
2. **ROADMAP 保留为系统全景层**：其差距矩阵（#1-#13）仍是"离愿景还差什么"的总账；蓝图每完成一个 Phase，对应差距项在 ROADMAP 中勾销。
3. **蓝图未覆盖项两处**（研究层供数任务、模型运行时启用）：默认建议**纳入蓝图 1C 施工序列**（六角色的"专属输入"必须有供数管道，1C 验收"注入角色冲突时能看到独立意见"依赖运行时可用）；是否提前到与 Phase 0 并行，由用户裁决。
4. **命名冲突消歧**：两份文档各有 Phase 0/1 概念，语义不同。引用时必须带文件名（"蓝图 Phase 0" vs "ROADMAP Phase 0"），禁止裸写 Phase N。

## 4. 施工约束（从重构会话固化，蓝图施工必须遵守）

1. **计划任务红线**：不删除任何任务，只更新 action 路径；`C:\Users\YZP\WorkBuddy\yaoban_tasks\root.txt` 是任务路径单一真相源，`launch.ps1 -Mode` 派生一切。
2. **运行时**：yaoban-system 用 workbuddy python envs/default + `PYTHONPATH=..\py_libs`；系统 Python 3.14 缺 numpy/akshare 不可用。
3. **paper-only**：`real_order_submission=false` 永久有效（蓝图 §11 第 8 条同源）。
4. **服务**：Vibe 8766/8765/5930 + DSH web 3080（never kill）；desktop 用 pnpm（junction，移动后需重装依赖），orchestrator 用 npm。
5. **旧入口清理**：按 `LEGACY_CLEANUP.md` 前置条件执行，当前仅一项未满足（跨交易日完整周期观察）。

## 5. 权威源层级（更新）

| 层 | 权威源 | 锚点 |
|---|---|---|
| 愿景与定位 | 本文件 + SYSTEM_MAP.md + session 存证 | session sha256 `f9cf7a4e...a16f9` |
| Phase 1 施工路线 | 蓝图 v1.0 | sha256 `cdd22991...03943` |
| 生产状态基线 | baseline-0-pre-fix manifest | `552fa823...d55be` |
| 系统全景差距总账 | ROADMAP.md | 随勾销动态更新 |
| 历史证据数字 | yaoban-system/docs/reviews/* | 蓝图 §4.1 规则 |

## 6. 平台完成度判定：1D ≠ EvoAlpha 平台完成

**1D 完成只等于"选股学习闭环"这一个垂直切片打穿**，不是平台终点。

1D 完成时已达成：
- ✅ 真实性可信的 baseline-0（回溯成交/收盘链/provenance 修复）
- ✅ 学习入口结构化 + 每日前向标签（自动校对）
- ✅ 选股维度可证伪闭环：双榜冻结 → 标签 → 归因 → 实验 → 20 日门禁 → 晋级/回滚
- ✅ 六角色在**影子账户**（challenger 10 万独立 ledger）真实运转（独立意见、裁决、风控 veto）

1D 完成时仍未达成（剩余路线，ROADMAP Phase 1-4 与蓝图后续扩展并轨）：

| 阶段 | 内容 | 验收 | 对应 |
|---|---|---|---|
| P2-A 研究层供数 | DEEPSEEK_API_KEY + doctor 全绿；盘前 07:30 Vibe run → researcher artifact；盘后 5 类 artifact 自动转化；研究包 ≥3 类外部数据 | 连续 10 个交易日研究产物自动生成 | ROADMAP Phase 1 / M1 |
| P2-B 生产决策链接管 | 盘后 16:15 团队门禁任务（真实输入非 fixture）；team_decision vs 引擎执行一致性对比；看板团队区块 | 连续 10 日真实团队决策，一致率 ≥80% | ROADMAP Phase 2 / M2 |
| P2-C 买卖点/仓位维度扩展 | 买点（R2' 特征→交易员）、卖点引擎全量接入生产、仓位管理（组合经理资金分配，受 policy 硬约束）；各维度独立 20 日门禁（复用 1D 机制） | 各维度独立晋级首个版本 | 蓝图 §2"后续扩展" |
| P2-D 复盘进化全链路 | 每日/每周 reviewer 复盘（基准 000852.SH）；iteration_proposal → 案例回归 → walk-forward → 灰度；计划外交易归因流程 | 首个"学习→策略版本"晋级（全策略面） | ROADMAP Phase 3 / M3 |
| P2-E 自主度分级治理 | advisory → co-sign → autonomous 逐级灰度（每级 ≥20 交易日）；熔断回滚压测；季度评估（智能体 vs 规则引擎独立盈亏贡献） | 完整闭环连续运行一个季度 | ROADMAP Phase 4 / M4 |
| P2-F 平台化 | 多学习对象复制（第二个选手/策略族）；因子研究实验室正式接入闭环；旧入口清理执行 | 多对象并行进化 | 愿景终态 |

结构判断：1D 打穿的版本化/预注册/门禁/canary/回滚机制是**通用进化基础设施**——P2-C 起所有新维度复用同一套机制，边际成本递减。1D 的六角色+影子组合覆盖 ROADMAP 差距 #5-#10 的影子层；#7/#8（生产决策智能体化）在 P2-B/P2-E 才关闭。
