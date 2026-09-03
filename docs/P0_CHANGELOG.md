# P0 基线稳固 · 变更日志（2026-08-31 晚）

> 原则：失败可见、版本化、可回滚。每项修复含根因、改动、验证。

## P0-1 计划任务修复
- **YaobanNextPlan**：17:10 报错 "unknown mode next-plan"（RES=22）。根因：任务 -Mode next-plan 而 runner 无此 mode（next-plan 生成已并入 rebuild 链）。
  处置：**禁用任务**（保留 XML 可回滚）；run_trading_task.ps1 已被外部更新支持 next-plan mode，如后续需要独立 next-plan 可重新启用。
- 验证：schtasks 显示 Disabled；preflight 任务Action 检查通过（该任务不在 EXPECTED 内）。

## P0-2 复盘子任务修复（trader_daily rc=1）
- 根因：trader_daily.py:118 对 day_pnl=None（首日无前日净值）执行 f'{None:+.2f}' 抛 TypeError；avg_win/avg_loss 存在同类隐患。
- 改动：`yaoban-system/scripts/trader_daily.py` None 安全格式化（N/A 占位）。
- 验证：重跑 `python scripts/trader_daily.py --date 2026-08-31` → EXIT=0，JSON+MD 均生成。

## P0-3 preflight 门禁修复（4 处，scripts/preflight.py）
1. **TDX 行情检查**：失败重试 2 次（间隔 8s）；开盘前（<09:15）失败降级 WARN（不再 fail-closed 连锁阻塞 auction/scan），盘中/盘后保持 FAIL。
   - 背景：8/31 08:55 TDX bars=0 → PlanGate RES=1 → auction/scan 被 gate 挡至 09:55 人工恢复。
2. **ASCII_TASKS 路径**：BASE.parents[2]（=Claw）→ parents[3]（=WorkBuddy）+ 存在性候选回退；否则任务Action 恒 FAIL。
3. **root.txt BOM**：read_text('utf-8') → 'utf-8-sig'；root.txt 文件本身已去 BOM（Python 重写）。根因：16:46 root.txt 更新时带 UTF-8 BOM，Path 比较恒 False → 任务Action 全 FAIL。
4. **账本/持仓检查口径**：last != pday → last not in (pday, day)。收盘后 rebuild 完成时数据含当日属正常（8/31 17:43 rebuild 完成后 300489 已含 8/31），不应判缺失。
- 验证：preflight 重跑 11 PASS / 0 FAIL（账本修复后待全市场数据就绪复验）。

## P0-4 模型运行时启用
- `DEEPSEEK_API_KEY` 已写入**用户级**环境变量（注册表 User 作用域）；计划任务进程验证可读（35 chars 完整）。
  - 注意：DSH 沙箱进程不继承 User 环境变量（隔离），通过 DSH 跑 doctor 需显式注入 `$env:DEEPSEEK_API_KEY`；计划任务/独立进程正常。
- Vibe-Research doctor：15:54 为 16 ok/2 fail → **注入后 17 ok/1 warn/0 fail**（warn: api.token ACL，已 icacls 收紧为当前用户）。
- 首次真实研究 run 已启动：`node orchestrator/src/run.ts --symbol 300489 --market SZ --provider deepseek --run-id p0-20260831-300489`（6 阶段，function_calling 运行时）。产物：.local/runs/p0-20260831-300489/。

## P0-5 盘后数据链缺口修复（重大）
- **发现的缺口**：分钟线（F:/WorkBuddyItem/a股分钟线/parquet_qfq_2026）停留在 **8/21**；daily/（qfq 日线）停留在 **8/28**；daily_tencent 停留 8/28。QFQStore 日线聚合=分钟聚合 → 情绪表/候选表/信号全面滞后 8 个交易日。且**无任何计划任务更新这些数据**（r5p/r6p build 上次为 8/29 手动运行）。
- **新增 `yaoban-system/scripts/fetch_daily_incremental.py`**：腾讯 ifzq qfqday 源拉取 8/28+ 缺口；**复权因子锚定**（新8/28 ÷ 旧8/28，如 300489 ratio≈9.205）对新行调权后合并入 daily/；amount 缺失用 volume×close 近似（ADJ_AMT_EST）；因子异常（ratio≤0 或 >5 或 <0.2）跳过该股等稳定。
- **QFQStore._agg_daily 改造**（src/data/qfq_store.py）：分钟聚合（历史，≤8/21）+ daily/（近端，>分钟线最后日期）动态拼接；调用方（r5p/r6p/plan_daily/scan）无需改动。
- **新增计划任务 YaobanDataRefresh**（工作日 16:45，data-refresh mode）：r5p_sentiment_build → r6p_candidates_build；run_trading_task.ps1 增加 data-refresh 分支；preflight EXPECTED 已纳入。
- rebuild 首日实测 **43 分钟**（17:00-17:43，TDX 60m 全市场拉取）> 30 分钟目标 —— 待观察是否因首日全量；明日计时后再评估增量优化。
- 验证：fetch_daily_incremental 10 只冒烟 ok=9；300489 调权结果 8/31 qfq=26.04（与 8/28=25.43 平滑衔接）；全市场后台运行中。

## P0-6 每日验收（acceptance）
- 8/31 19:10 首跑 **RES=2（fail）**：13 项检查 5 项 false —— auction_latest/auction_freeze/auction_delivery（早盘 TDX 连锁，auction RES=21）、live_tick（VibeResearchLiveTickValidation 11:39 午休窗口 fail-closed，RES=2）、task_log_continuity（09:50-09:58 scan 中断）。
- 均为当日早盘事件遗留；P0-3 TDX 容错 + P0-5 数据链修复后，明早（9/1）应为首次全绿窗口。9/1 收盘后 acceptance 复验。


### P0-5 补充（22:30-23:10 数据链施工实录）
- 腾讯 ifzq 全量拉取约 700 只后被限流（HTTP 501）—— 反爬，需间隔恢复；已处理的 700 只将在恢复后重跑覆盖（keep=last 幂等）。
- **baostock 验证结论**：其 qfq 为发行价基准，与 daily/（最新价基准）不兼容——除权股调权后 OHLC 关系异常（000001 8/31 close>high）。**不可作为 qfq 日线写入源**；保留 fetch_bs 仅作参考。
- 单位统一：daily/ 文件存储 volume=手（东财旧数据已是手）；fetch_daily_incremental 腾讯源 volume=手直接用；QFQStore._agg_daily 对 daily 行 ×100 转股（与分钟聚合口径一致，保证 vr 跨边界自洽）。amount 缺失（腾讯回退）时近似 = 手×100×close。
- 已修正的正式链路：腾讯主源（最新价基准 qfq）→ 锚定日(8/28)双口径 ratio 调权 → 合并 daily/。300489 调权验证：8/31 qfq close=26.04 与 8/28=25.43 平滑衔接（+2.4%），OHLC 关系有效。
## 待办（明早验证）
1. 全市场 daily 增量完成后：重跑 r5p_sentiment_build + r6p_candidates_build → generate_next_plan（9/1 计划基于 8/31 数据）
2. preflight 全绿复验（含账本 300489 数据）
3. 9/1 08:45-09:15 计划任务链观察（Preflight/Premarket/PlanGate/Auction 应全部 PASS）
4. 研究 run 产物归档 → adapt-run 转化为 researcher artifact
5. 9/1 收盘后 acceptance 复验（期望 pass）
## 最终验收（23:50）
- **preflight 全绿：11 PASS / 0 FAIL / 1 WARN**（WARN=YaobanDataRefresh 未首跑，属预期）。
- 9/1 计划已基于 8/31 数据生成（mode=输入≤2026-08-31收盘；picks 002760/300420/000816/002239；情绪 zt=89/温度69.5/高潮），published_at 23:42:53。
- sentiment_full_2026.csv 已更新至 8/31（zt=90/dt=15/炸板率28.6%/温度70）；daily/ 全市场 4686 只含 8/31（QA：均值+0.72%，>25% 异常仅 2 只北交所涨停）。
- **data-refresh 模式实跑验证通过**（launch.ps1 -Mode data-refresh → LAUNCH_EXIT=0，r5p+r6p 全链路）。
- **研究 run 收尾**：p0-20260831-300489（30 分钟，6 阶段，743 证据/15 计算）→ adapt-run → `outputs/team_artifacts/p0-20260831-300489-researcher.json`（status=failed 诚实标记：estimates/valuation incomplete——一致预期机构数 2<3）。
- **情绪表检查口径修复**（preflight.py）：last==pday → last in (pday, day)，与账本口径一致。

## 明早（9/1）验证清单
1. 08:45 Preflight / 08:50 Premarket / 08:55 PlanGate / 09:15 Auction 全部 PASS（TDX 容错生效）。
2. 08:45 任务历史 unproven 应只剩 YaobanDataRefresh（16:45 首跑后消除）。
3. 09:30-11:30 盘中 scan/notify/monitor 无 monitor-gap 失败推送。
4. 16:45 YaobanDataRefresh 首跑（data-refresh mode，已实跑验证）。
5. 17:00 rebuild 计时（首日 43min > 30min 目标；次日观察是否回落，仍超则评估 TDX 拉取并行化）。
6. 19:10 acceptance 复验（8/31 首日 5 项 fail 均为早盘 TDX 连锁与午休 tick 校验，应随 9/1 正常窗口转 pass）。
7. 连续 5 个交易日 0 失败后，P0 验收正式关闭。
## 9/1 开盘前预检（00:05）
- 9/1 确认为交易日（baostock 日历 ok，prev=8/31）；9/1 计划就绪（输入≤8/31 收盘，23:42 生成）。
- 全部任务状态符合预期：Next Run 均为 9/1 定时；YaobanNextPlan 保持 Disabled；YaobanDataRefresh 待 16:45 首跑。
- 新增晨检脚本 `yaoban-system/scripts/check_morning.py`：09:40 后运行一次，检查 08:45-09:35 链（LR 日期+RES=0）、preflight infra/post_plan 状态、当日 delivery 失败推送、次日任务就绪；8/31 历史数据验证逻辑正确（EXIT=2 正确判定历史失败）。
- 下轮验证：09:40 后运行 check_morning.py --date 2026-09-01，期望 summary.pass=true。
## 9/1 00:10 验证自动化
- check_morning.py 增加报告落盘：outputs/validation/morning_check_<date>.json（供定时任务无窗口留痕）。
- 注册计划任务 **YaobanMorningCheck**（工作日 09:40，pythonw 直接运行）：每天自动生成晨检报告，跨日验证自动归档。
- 手动验证：morning_check_2026-08-31.json 已生成（EXIT=2 正确反映历史失败）。
- 9/1 验证路径：09:40 晨检自动落盘 → 09:40 后人工/下轮复核 morning_check_2026-09-01.json（期望 pass=true）。
## 9/1 00:15 就绪终检
- 8 个关键任务全部 Enabled，Next Run 正确：Preflight 08:45 / PlanGate 08:55 / Auction 09:15 / **MorningCheck 09:40** / Close 15:40 / **DataRefresh 16:45** / Rebuild 17:00 / Acceptance 19:10。
- 9/1 计划存在（输入≤8/31 收盘）；DEEPSEEK_API_KEY User 级持久有效。
- **9/1 验证完全自动化**：早晨链由计划任务驱动，晨检由 YaobanMorningCheck 09:40 自动落盘 `outputs/validation/morning_check_2026-09-01.json`；盘后 data-refresh/rebuild/acceptance 自动运行留痕。任何会话中断均不影响验证留痕。
- 9/1 09:40 后验证入口：读取 morning_check_2026-09-01.json（期望 summary.pass=true）+ task_logs/2026-09-01/ 复核 + acceptance_2026-09-01.json。
## 9/1 00:05 计划任务路径演练
- `schtasks /run` 手动触发 YaobanMorningCheck：**Last Result=2（正确判定）+ morning_check_2026-09-01.json 自动落盘（00:04:59）**——pythonw 无窗口环境下脚本+落盘全链路真实可用（消除了静默失败盲区）。
- 9/1 报告基线：delivery_failures=[]，chain_ok/preflight_ok=false（08:45 前属预期）；09:40 任务再次触发后将自动更新为真实结果。
## 9/1 00:25 P0-6 根因修复：live_tick 校验触发窗口错位
- **根因**：VibeResearchLiveTickValidation 每天 09:32 触发一次，但 validate-live-ticks.mjs 的校验窗口为 **09:35-11:30 / 13:05-15:00**（shanghaiTradingWindow）→ 09:32 运行必判 in_session=false → 写失败结果；8/31 09:32 失败后 11:39（午休）再失败覆盖 → latest.json 恒失败 → acceptance live_tick 恒 false（8/31 acceptance fail 的 5 项之一）。
- **修复**：任务 StartBoundary 09:32 → **09:35**（窗口起点）；失败时 RestartOnFailure 在 09:36-09:38 窗口内重试 3 次兜底。run-live-tick-validation.ps1 已有 existingValid 保护（当日已 pass 则不覆盖）。
- 验证：任务已更新（Next Run 9/1 09:35）；成功路径需 9/1 09:35 实际运行确认（若 tick 数据就绪 → pass → acceptance live_tick=true）。
## 9/1 00:35 acceptance 全项审查（预防性）
- **continuity exit=6 修复**：collect_daily_acceptance.task_log_times 接受 exit in (0,6)——scan 的 exit=6=“伴随监控失效·安全拒绝新仓”（tick 数据源间歇超时的 fail-closed 正确行为），任务已运行应计入连续性。8/31 验证：scan 285 条全时段计入；剩余 continuity=false 仅因早盘 09:40-09:56 缺口（TDX 连锁历史，9/1 无）。
- **auction 链路确认**：auction_latest（read_only:True，每次运行写）/ auction_freeze（09:25 后写 orders_allowed:False）/ auction_delivery（notify_trading_events 读 freeze → 推 kind=auction 事件）三者 9/1 均有明确满足路径。
- **9/1 acceptance 13 项检查全部确认可满足**：continuity（修复后）/auction×3/live_tick（09:35 触发修复）/tick_snapshot/双 gate/delivery×2/ledger×2/next_plan/tasks。
## 9/1 00:50 r6p 候选表硬编码上限修复（重要）
- **根因**：r6p_candidates_build.py 第 79/82 行硬编码 `date <= 2026-08-28`（8/28 晚注释“重建日线库已覆盖8/28”）→ daily/ 增量方案打通后候选表仍永远滞后一天（8/31 修复前 max=8/28；9/1 计划 picks 的 8/31 信号只来自 plan_daily 实时扫描，双轨不一致）。
- **修复**：上限改为数据驱动（`_maxd = df['date'].max()`），信号窗口 `04-01 ~ maxd`。
- **验证**：重跑后候选表 max=2026-08-31（30876 条，8/31 信号 903 条）。r6p 全量耗时 746s（含 2025 预热），YaobanDataRefresh 16:45 总耗时预算 ≈15min < PT90M 限制 ✓。
- **口径差异确认（非故障）**：plan_daily 的 load_all_daily 用 daily_rebuilt（TDX 实盘价）覆盖 QFQStore，r6p 仅用 QFQStore（qfq）→ 002760 在实盘口径 8/31 触发 detect_huigui_v5、qfq 口径不触发，故 9/1 计划 picks 不在 r6p 8/31 候选内。两条路径各自自洽（plan 用于盘中执行、候选表用于 preflight/回测）；**P1 事项：统一双轨口径或显式声明差异**。
## 9/1 01:05 修复完整性快照
- 8 个修改文件 mtime 全部符合昨晚修改时间（preflight 23:43 / trader_daily 22:06 / qfq_store 22:25 / run_trading_task 22:14 / fetch_daily_incremental 22:54 / collect_daily_acceptance 00:07 / r6p_candidates_build 00:10 / check_morning 00:03），无外部覆盖。
- 6 处修复标记（P0-2/P0-3/P0-5/P0-6/_maxd/norm_date/fetch_rebuilt）全部在位。
- **凌晨施工阶段正式收尾**：剩余轮次耗尽不影响验证——9/1 09:40 晨检自动落盘 `outputs/validation/morning_check_2026-09-01.json`，之后任何会话/用户可读取结果完成跨日验证闭环。
## 9/1 01:10 rebuild 防回退加固
- fetch_daily_minute_rebuild.py 写入前增加回归校验：新聚合 max date < 旧文件 max date 时跳过（保留旧数据），防止 TDX 数据滞后/未就绪时全量重写导致 daily_rebuilt 数据倒退（否则次日 preflight 账本检查会因持仓数据缺失 FAIL）。语法验证通过；正常路径行为不变。
## 9/1 00:45 时间表重构（用户评审）
**评审意见**：① 系统检验必须在 09:00 前完成（09:15 集合竞价、09:30 开盘）——09:40 晨检在开盘后才跑，发现问题已无法处置；② 盘后链 4 个时间碎片化，应合并。

**新时间表**：
| 时间 | 任务 | 说明 |
|---|---|---|
| 08:45 | Preflight | 基础设施检验 |
| 08:50 | Premarket | 盘前快照 |
| 08:55 | PlanGate | 计划验收（post_plan 门禁） |
| **08:58** | **MorningCheck** | **开盘前晨检（09:00 前完成）**：检查 08:45-08:55 链 + preflight 报告 + 数据就绪 |
| 09:15/09:30 | Auction/Scan/Tick/Monitor | 交易动作（非检验） |
| **15:10** | ClosePipeline | 收盘流水线（原 15:40 提前） |
| **16:30** | **PostCloseChain** | **盘后链单任务**：r5p→r6p→daily_rebuilt→next_plan→acceptance（取代 DataRefresh 16:45/Rebuild 17:00/Acceptance 19:10 三任务） |

**实施**：
- check_morning.py：CHAIN 拆为开盘前 3 项（盘中连续性由 acceptance 覆盖）；MorningCheck 任务 09:40→08:58。
- run_trading_task.ps1 新增 'post-close' 模式（链逻辑独立为 scripts/post_close_chain.ps1，case 单行调用——PowerShell 5.1 switch 多行块解析 bug 规避）；每步失败不中止（尽力而为），acceptance 汇总，飞书通知整体结果。
- 注册 YaobanPostCloseChain（16:30，PT3H）；禁用 YaobanDataRefresh/DailyRebuild/DailyAcceptance（XML 保留可回滚）；preflight EXPECTED 更新为 PostCloseChain。
- ClosePipeline 15:40→15:10；preflight 验证 PASS（任务Action bad=[]，unproven=[PostCloseChain] 首跑前预期）。
- **post-close 链真实演练进行中**（00:45 启动，含 r5p/r6p/rebuild/next_plan/acceptance 全步骤）。
## 9/1 01:50 时间表重构完成（含 4 轮演练）
- **post-close 链实现细节**：链逻辑独立为 scripts/post_close_chain.ps1（param 必须为脚本第一条语句——PowerShell 语法）；run_trading_task.ps1 case 以**独立进程**调用（powershell.exe -File）并 `exit $LASTEXITCODE`（修复 `&` 嵌套调用中 exit 码不传播问题）。
- **4 轮演练**：①switch 多行块解析 bug（改独立脚本）→ ②param 位置错误（2 秒失败）→ ③exit 传播修复（独立进程）→ ④**完整 36 分钟跑通**：r5p 160 行/r6p 30876 条/rebuild skip 83s/next_plan 生成/acceptance 执行，链 exit_code=1 正确反映凌晨 acceptance fail（16:30 真实运行早晨链已跑 → pass → exit 0）。
- **最终时间表**（用户评审后）：08:45 Preflight → 08:50 Premarket → 08:55 PlanGate → **08:58 MorningCheck**（09:00 前完成检验）→ 09:15-11:30 交易时段 → **15:10 ClosePipeline** → **16:30 PostCloseChain**（单任务盘后链）。
- 待办：09:00 前确认 MorningCheck 08:58 首次自动运行结果（morning_check_2026-09-01.json 由 08:58 任务覆盖更新）。

## 9/1 上午 P0-7 修复：TDX 服务器清单 + check_morning 误报（含一次运维事故复盘）
### TDX 08:55 全服务器连接失败根因（用户反馈 mootdx "4/4 可达"）
- **mootdx bestip 仅做 TCP socket 探测（0.7s 超时），不验证行情数据**；实测 47 个候选节点：18 个 TCP 可达，但仅 2 个（115.238.56.198 / 115.238.90.165）能拉到真实 K 线。119.97.185.59 TCP 47ms 可达但 get_security_bars 全部类别返回空 → **"TCP 可达" ≠ "行情可用"**。
- 08:55 时 preflight 内置 10 节点全部失败（8 connect_false + 2 empty）：08:45 尚正常的 115.238.56.198 在 08:55-09:30 窗口内也连接失败，09:35 恢复 → 服务器端瞬时故障窗口。P0-3 开盘前降级 WARN 逻辑正确兜底（PlanGate 仍 PASS）。
- **preflight.py 改动**：`tdx_health` 增加 TCP 预筛（1s/节点，全挂时从 ~2min 降至 ~10s）；实测可用节点优先。
- **10 个脚本 SERVERS 备份节点更新**：123.125.108.14（实测行情空）→ 115.238.90.165（实测行情可用）：close_pipeline / collect_tick_daily / fetch_daily_minute_rebuild / fill_daily_all_0827 / fill_daily_history / monitor_intraday / pull_intraday / scan_and_confirm / tick_monitor / stress_tdx_tick / fetch_stock_names。
### check_morning.py 两处误报修复
- **schtasks 中文键解析**：zh-CN 系统输出"上次运行时间/上次结果"等中文键，原脚本仅解析英文键 → chain 恒判失败（假阴性）。现中英文键并存解析（_KEY_ALIASES + result_zero 兼容 0x0）。
- **delivery 失败推送按当日时间过滤**：仅统计当日 08:00 之后（cutoff），凌晨演练/历史遗留的 failure 推送不再污染晨检。
- 验证：模拟 zh-CN 输出单测通过；重跑 check_morning --date 2026-09-01 → chain_ok=true、preflight_ok=true（修复前 chain 全空）。
### monitor_intraday.py 开盘窗口误报修复
- 根因：当日 5m K 线 09:35 起逐根生成，凑齐 5 根需到 09:55；原豁免窗口仅到 09:35 → 09:35-09:55 每轮误报 unavailable → scan companion_health 判 "monitor stale >15m" → 禁止新仓连锁误伤。
- 修复：豁免窗口 09:35 → 09:55。验证：09:45 手动运行 monitor exit=0。
### 运维事故复盘（重要）
- 09:30-09:45 盘中 scan/tick/monitor 连续失败（SyntaxError: Non-UTF-8）根因：09:30 前对 10 个脚本执行批量 `Get-Content/Set-Content -Encoding UTF8` 修改 SERVERS 行时，PS5.1 默认 ANSI(GB2312) 读 + UTF-8 写造成中文乱码（GBK↔UTF-8 双重编码，且 .NET GBK 往返对部分字节对有损不可逆）。
- 恢复方法：monitor_intraday（纯 GBK 字节无损转回）；5 个仅 SERVERS 改动的文件 git checkout HEAD + 重放；5 个含合法未提交改动的文件（close_pipeline / fetch_daily_minute_rebuild / scan_and_confirm / tick_monitor）以 **`__pycache__/*.cpython-313.pyc`（08:57 破坏前编译缓存）为金标准**重建——字符串常量集合 + 字节码逐指令比对全部一致（117/171/81/40 字符串 0 缺失），并修复 pyc 反汇编暴露的 2 处 HEAD-repair 误插行。
- **教训**：① 修改含中文的 Python 文件禁止用 PowerShell `Get-Content/Set-Content`（编码陷阱），一律用 UTF-8 感知工具；② 脚本修改后立即 `py_compile` 验证；③ 定时任务环境与交互环境编码假设不同（zh-CN ANSI vs UTF-8）。
- 现状：13 个脚本全部 py_compile 通过、UTF-8 有效；preflight 11 PASS / 0 FAIL；09:50 起盘中任务恢复（monitor 豁免窗口修复后 companion_health 恢复 → scan 新仓能力恢复）。
## 9/1 调度注册收敛：08:58 晨检 + Vibe 时间统一
- 新增权威注册入口 `yaoban-system/scripts/register_p0_schedule.ps1`：幂等注册并校验 `YaobanMorningCheck` 工作日 08:58，以及 `VibeResearchLiveTickValidation` 工作日 09:35/13:05。
- `run_trading_task.ps1` 新增 `morning-check` 模式，晨检经统一 `launch.ps1` 记录任务日志并保留退出码。
- Vibe 校验触发器与脚本交易窗口统一为 09:35-11:30 / 13:05-15:00；失败后每分钟重试，最多 3 次。
- 会覆盖 P0 生产时间表的旧注册器已 fail-fast 禁用（exit 64）；`register_board_refresh.ps1` 配置与现行时间表一致，继续保留。

## 9/3 P0 观察日审查结论（用户裁定，2026-09-04 00:11 传达）
**评级：严重异常——盘中风控链路未达标；盘后数据链最终恢复，但验收仍失败。P0 观察日不计为正常日。**

| 链路 | 评定 |
|---|---|
| 盘前链 | 通过 |
| 盘中行情/扫描 | 部分通过 |
| 实时 tick 风控 | 失败 |
| 收盘结算 | 通过 |
| 盘后研究链 | 重试后通过 |
| 日终平台验收 | 失败 |

- **P0-1** tick daemon 09:30 启动、11:16 死于 WinError5（pos_live 写入撞锁）→ 持仓盲区 2h25m；13:52 看门狗上线后多轮重启无效（13:59/14:01 两次耗尽额度），14:11 schtasks_spawner 手动拉起恢复；验收 live_tick=false（数据源停 11:15:57，陈旧 6559s ≫ 90s 阈值）。
- **P0-2** 看门狗"能告警不能恢复"：重启上限耗尽后无升级处置、无隔离状态；15:06-15:08 收盘后又把 daemon 正常自退误判为 missing，再耗尽 5 次额度。
- **P1** 603538 计划外买入（10:35, 1500 股, +9.2%, offplan-盘中捕捉）；收盘灰度审计卖出"仅审计未执行"但账本仍持仓 1500 股，日报胜率/平均亏损口径与审计动作混淆（"卖出触发:无" vs 止损卖出记录并存造成误读）。
- **P1** 盘后链 16:30 首跑 exit=1（已定位修复：Invoke-ChainStage stdout 污染 5e48f6a + UTF-8 BOM GBK 吞行 ada7f25）；22:23/22:39 重试成功；22:48 全量重跑验收 exit=4；最终验收 fail（live_tick / tasks / VibeResearchLiveTickValidation）。
- **P2** 08:55 TDX 全服务器连接失败（非 critical 放行，P0-3 降级逻辑按设计兜底）；13:43 全市场行情覆盖率 91.5%。
- 关键判断：**"故障被发现并留下记录" ≠ "风控链路运行正常"**；盘后数据生成成功不能视为平台日运行成功。

## 9/4 凌晨 P0 加固施工（针对 9/3 裁定三项最优先处置）
### 1. 看门狗 v2（`scripts/_tick_watch.py` 全量重写）
- **收盘窗口修复（P0-2 直接根因）**：daemon 自退时刻 >15:05 而 v1 守到 >15:10 → 15:05-15:10 把正常自退当 missing 5 连假重启。v2：分钟 ≥903（15:03）起 missing/stale 一律不再重启，视为正常收盘。
- **启动宽限 BOOT_GRACE=150s**：daemon 首写 pos_live 最坏 ~25s（TDX 连接+首轮），v1 首查 20s 可先于首写误判；每次 spawn 后宽限期内不判 stale。
- **午休感知（v1 潜伏缺陷，全天守护必炸）**：daemon 午休 11:30-13:00 按设计停写 → v1 mtime 判据会把整个午休当挂死反复重启。v2：午休冻结 stale 判据 + 跨午休 age 扣除 90min（effective_age）。
- **耗尽升级（P0-2 处置）**：watch_limit → `tick_guard_state.json`（state=restart_exhausted 隔离状态）+ 飞书告警（每日一条，f85cb8ae）+ degraded 观测模式（不再烧额度，人工复活 daemon 记 watch_recovered），退出码 6（对齐 scan 的 exit=6 语义）。
- **进程存活 ≠ 数据更新**：唯一健康判据 = pos_live mtime；进程列表仅用于 missing 检测与 kill。
- **状态机**：armed → ok/restart_exhausted → closed_ok；文件锁单实例 + beat 接管逻辑保留。
- 验证：内置 `--selftest`（stub daemon + 快时钟，双场景）**12/12 PASS**——午休扣除单测、正常路径 exit 0 / closed_ok / 零重启、宽限保持（首重启 10.0s ≥ 8s 宽限）、挂死 2 次重启即耗尽、隔离状态落盘、degraded 复活观测、耗尽后零重启、收盘窗口自退不重启。
### 2. 调度链切换（P0-1 根因处置）
- `run_trading_task.ps1` 'tick' 模式：裸 `tick_monitor.py --daemon` → **`_tick_watch.py` 前台守护**（内部拉 daemon+监护）。v1 裸 daemon 一死即裸奔是 9/3 盲区 2h25m 的直接根因；YaobanTickDaemon 09:30 计划任务无需改动。
- `tick_monitor.py`：清除 9/3 遗留 DBG 打点（每轮 4 条 stderr）。
- `_restart_tick_daemon.py`：杀 watcher 后清理残留锁（消除新 watcher 120s beat 接管盲区；kill 失败时保留锁防双守）。
### 3. 验收硬性项（`collect_daily_acceptance.py`，9/3 裁定第二项处置）
- `tick_snapshot` 升级为**收盘新鲜度**：`pos_live.time >= 14:55`（v1 只查文件存在+日期，daemon 死 3 小时的陈旧快照样 pass——"进程存在≠数据更新"的验收层漏洞）。
- 新增 `tick_watchdog`：当日 risk_events 无 watch_limit / data_failure halt。
- 新增 `offplan_fills`：当日买入全部计划内（plan_match.in_plan / plan_ref offplan 前缀 / 兜底 sym∈picks），计划外成交即 fail。
- 报告附 `tick_watchdog`（restart_events/fail_events）与 `offplan_fills_today` 明细；inputs 增 risk_events。
- 验证：**9/3 回放 probe**——failed checks = live_tick、tick_watchdog（23 restarts/3 fail_events）、offplan_fills（603538）、tasks；tick_snapshot 15:05:56 达标 pass（盘中故障由 tick_watchdog 层捕获，分层正确）；整体 fail/exit 2 与裁定一致。
### 4. 日报口径统一（`trader_daily.py`，9/3 裁定第三项处置）
- 读 `close_decision_{date}.json`，灰度审计买卖单列**"未执行，不计入交易统计"**区块（9/3：卖出建议 603538 止损 1500股——账本仍持仓；买入建议 300670）。
- 胜率/盈亏标注**累计闭环**（仅计实际成交闭环）+ 新增当日实际成交/当日闭环计数；流水表计划外买入标 `[计划外]`；口径脚注。
- 验证：9/3 重放——实际成交 1 笔/当日闭环 0 笔/累计闭环 1 笔，offplan_buys=[603538]，audit_only_actions 与交易统计彻底分离。
### 施工事故与教训（工具层，跨项目）
- **并行 Edit 同文件互相覆盖**：同一消息里对同一文件发出多个 Edit 调用时，后写者基于旧内容读-改-写，会吃掉先写者的改动（本夜 3 个脚本各丢 1-2 处编辑，靠 selftest/回放抓回）。规矩：同文件多处修改必须串行单条 Edit 或整文件 Write，改完立即 grep 验证。
### 待办（P2 与观察项）
- TDX 行情源不稳定 + 覆盖率不足（91.5%）：暂维持 P0-3 降级逻辑；若与盘中监控故障叠加需评估 critical 升级。
- 9/4（今日）09:30 起 YaobanTickDaemon 以 watcher 模式首跑：重点观察 watch_start→首写时序、午休 11:30-13:00 无假重启、15:05 正常自退零 watch_limit、任务 LastResult=0。
- 603538 持仓 1500 股（offplan）：按止损纪律次日处置（止损价由 close_pipeline 审计已给出 stop_px 路径）。

