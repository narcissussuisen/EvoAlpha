# EvoAlpha 交易日时间链（权威表述 · 2026-09-10 重构后）

> status: active
> verified_at: 2026-09-15

> 本文件是时间表的唯一人工可读表述；机器权威在 `yaoban-system/scripts/register_schedule.ps1` 的 `$Schedule` 表，
> 由 `preflight.py` 的「任务触发器」检查每日比对（漂移为非致命告警）。
> 非交易日（周末+节假日）以 baostock 交易日历为唯一权威，**全线静默**：零任务执行、零推送、零门禁文件。

## 交易日

| 时刻 | 任务 | 系统动作 | 产物 | 失败后果 |
|---|---|---|---|---|
| 08:30 / 09:20 | VibeResearchDashboardServices | 看板服务保活 | 服务健康 | 08:35 体检看板项失败 |
| **08:35** | YaobanPreflight (infra) | 体检（日历/行情/账本守恒/数据表/任务/看板/进程/语法/资源；infra 17 项、post_plan 18 项） | `outputs/preflight_<day>_infra.json` | fail-closed：盘前链中止（tick 除外） |
| **08:36** | YaobanSelfHeal | 读门禁，失败则按剧本自愈并**重跑真实体检** | `outputs/selfheal/<day>.json` + 卡片 | 恒 0；未过项升级告警 |
| **08:36–19:00 每 5 分** | YaobanStatusPush | **只读观测**：关键节点状态卡推送（不参与门禁/账本/计划，可随时停用） | `outputs/notifications/status_push_<day>.json`、`delivery_*.jsonl`(kind=status) | 仅卡片缺失；连续 3 轮未就绪才告警 |
| 08:50 | YaobanPremarket | 刷新当日计划、推盘前卡 | `plans/<day>_plan.json` | gate 未过则 exit 21 |
| 08:55 | YaobanPlanGate | 计划验收（post_plan 门禁） | `preflight_<day>_post_plan.json` | 买入类链停摆（tick 不受影响） |
| 08:58 | YaobanMorningCheck | 唯一盘前自检卡（含自愈结果） | `outputs/selfcheck/` | 卡片显示 FAIL |
| 09:00 起每 30 分 | YaobanTdxProbe | TDX 双判据验活；恢复即通知 | `validation/tdx_state.json` | 恒 0 |
| 09:15–09:30 每分钟 | YaobanAuctionMonitor | 竞价快照/冻结观察名单（只读，缺计划降级纯快照） | `outputs/auction/` | 门禁失败 exit 20 |
| **09:30** | YaobanTickDaemon | 秒级持仓风控（止损/炸板/破 VWAP 减半），**不依赖门禁** | `intraday/pos_live.json`、`tick_guard_state.json` | 重启耗尽→告警+降级观测 |
| 09:30–15:01 每分钟 | YaobanScanConfirm (T2) | 全市场扫描→异动池→形态粗筛→三引擎确认→`--execute` 买入 | `intraday/confirm_*.json` | 漏单 |
| 09:30–15:01 每分钟 | YaobanIntradayMonitor | 持仓/备选分时触发与提醒 | `intraday/alerts_<day>.json` | 漏提醒 |
| 09:15–15:01 每分钟 | YaobanEventNotify | 去重推送盘中风险/成交事件 | — | 通知缺口 |
| 09:35 / 13:05 | VibeResearchLiveTickValidation | 校验 tick 数据实时性（非交易日静默） | `validation/live-ticks/` | live_tick 验收项 |
| 09:35–11:26、13:05–14:56 每 3 分 | YaobanBoardRefresh | 看板快照重建（非交易日静默） | `intraday/board_refresh.latest.log` | 看板滞后 |
| **15:10** | YaobanClosePipeline | 回填→全天决策重建→记账+收盘估值+看板+归因 | `close_decision_<day>.json`、ledger | 净值不落账 |
| **15:35** | YaobanPostCloseChain | rebuild→r5p→r6p→next_plan→acceptance→log-review | `chain_manifest_<day>.jsonl`、次日计划、验收、复盘 | 数据段失败=failure；仅验收非零=alert |
| **17:30** | YaobanEveningCheck | 八项合并核验（链/收盘/情绪/候选/计划/rebuilt/验收/成交合规） | `validation/evening_check_<day>.json` | 恒 0；卡片承载结论 |
| **22:00** | YaobanDailyIteration（内核已实现，待注册任务） | 资料解析→知识卡片→画像→提案→影子回归；参数类过门槛自动生效（写台账+补丁预览），规则/代码/数据类恒待人工确认 | `iteration_proposals/<date>.json`、`iteration/<date>/digest.md` | 恒 0；结论承载在摘要卡片 |
| 周六 10:00 | YaobanTdxServerVerify | TDX 候选池全量验活 + 交易日历刷新（维护类，非交易日仍运行） | `validation/tdx_servers_<date>.json` | 节点轮换失效风险 |

注：`YaobanLoopEngine`（16:35 循环工程）**当前为 Disabled**，不在运行时间链内。
注：22:00 自迭代批的内核已实现于 `yaoban-system/scripts/daily_iteration.py`（可手动跑通，
产物见 `outputs/iteration/<date>/digest.md`）；**计划任务尚未注册**，注册需人工确认。
其硬边界：参数类过门槛自动生效但只写台账与补丁预览，不改写 `config/parameters.toml`；
规则/代码/数据类变更恒为 `pending_confirm`。
注：`YaobanStatusPush` 是**只读观测者**（关键节点状态卡），不写门禁、不碰账本与计划；其节点卡时刻为 08:36 体检 / 08:50 盘前 / 08:55 验收 / 09:30 开盘 / 11:30 上午小结 / 13:05 午后就绪 / 15:05 收盘 / 17:45 晚间核验 / 18:30 盘后链·次日计划，清单见 `docs/HUMAN_MACHINE_INTERFACE.md`。

注：**tick 守护为双信号**（2026-09-11 修复后）。`outputs/intraday/_tick_daemon.beat` 是 daemon 心跳（每轮无条件写，证明"循环在转"），`pos_live.json` 是数据产物（证明"风控在算"）。
`outputs/intraday/tick_guard_state.json` 同时给出 `daemon_alive`（心跳新鲜）与 `tick_fresh`（数据新鲜）两个独立字段 —— **排障时先看 `daemon_alive`：`false` 才是进程真死（守护停摆），`true` 而 `tick_fresh=false` 属数据路径卡住**。二者处置完全不同：前者需人工/自动拉起进程，后者只需重跑数据路径，且 `scan` 对 `tick_fresh=false` 一律 fail-closed 拒新仓。`state` 为 `degraded`/`restart_exhausted` 时，双信号恢复新鲜会自动清除隔离并回补重启预算。

## 关键性质

1. **tick 与门禁解耦**：任何门禁失败都不再让持仓失去秒级止损保护（9/4 事故的结构性根因）。
2. **自愈边界**：只做服务/进程重启、r5p/r6p 重建、计划重生成、任务重注册、TDX 探活；**不改账本、不写门禁判定、不改生产代码**；每次自愈在晨检卡可见。
3. **数据最终化**：15:00 收盘价固定；盘后固定价格交易（15:05–15:30）量额随后落定，故盘后链 15:35 起跑，并在 rebuild 前做「末根 60m bar=15:00 且收盘价==实时价」断言。
4. **日历不可用时 fail-open**：按交易日继续执行并推一次告警（宁多跑，不误停）。
5. **人工介入点**：08:58 晨检卡（FAIL 需在 09:30 前处置）、盘中 tick 守护降级告警、17:30 晚间核验卡（有阻断项则夜间修复窗口 ≥15 小时）。
