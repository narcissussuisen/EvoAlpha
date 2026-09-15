# Automation 结果复核 · 2026-09-14 22:2x

> status: historical
> note: 记录当时口径与决策，只增不改（数字停留在当时）

> **起因**：用户问「现在你拿到他的结果了吧。结果如何？」
> **先答事实**：automation 的输出**不会自动投递到主会话** —— 我这条会话没有「收到」任何推送。
> 下面是**我去落盘把它的汇报读出来 + 逐项独立复核**的结果，不是转述。

---

## 0. 「他」是谁：今日 automation 清点（实测）

| automation | 触发 | 结束 | 结果位置 |
|---|---|---|---|
| tpoint 反馈闭环驱动（`automation-1786457553495`） | 15:45 | 15:49 | 非本项目（tpoint） |
| **D11 卖出裁量日报**（`ff4227d8`） | 15:50 | 15:52 | `projects\f-WorkBuddyItem-automation-2026-09-13-20-09-38\543daf87…jsonl` |
| **盘后施工**（原 `b92b3ad0`，20:2x 已判过期删除） | 15:45 | 17:41 | `projects\f-WorkBuddyItem-automation-2026-09-14-13-02-40\57992e9b…jsonl` |

**尚未触发**：9/15 08:45「战法池就位校验」、9/15 15:20「采集首个真实队列样本」。

---

## 1. 盘后施工 automation 的汇报（7 点）+ 我的复核判定

| # | 它的结论 | 我的复核 | 判定 |
|---|---|---|---|
| 1 | 9/15 战法池就位：`day=2026-09-15 / asof=2026-09-14 / lookback=4 / n_pool=1546`，`huigui 1444 / zt_huicai 99 / xianren 3` | 直读产物：**逐字段一致**（375,857 B，17:11:29）；`n_syms_scanned 5644 / n_excluded_st 212 / n_excluded_fanbao_only 479 / n_no_name 420` 全部对上 | ✅ 成立 |
| 1b | 9/15 日计划就位：picks n=4 | 直读：`002815 崇达 / 002913 奥士康 / **000565 渝三峡Ａ** / 000690 宝新` （上午那份里的 300335 已被 000565 替换） | ✅ 成立 |
| 2 | `--pattern-gate` 已接入生产 scan 行；BOM 正确；开关恰好 1 处 | grep：`run_trading_task.ps1` 命中 **1 次**；BOM = `[239,187,191]` ✅（`scan_and_confirm.py` 侧 6 次为实现） | ✅ 成立 |
| 3 | daemon/启动链：`closed_ok / daemon_alive=true / restarts_window=0` | 直读 `outputs/intraday/tick_guard_state.json`（15:55:52）：**完全一致** | ✅ 成立 |
| 4 | 全量测试 **546 passed / 0 failed** | **未复核**（未重跑；按纪律不与 rebuild 并行） | ⚠️ 采信自述 |
| 5 | 4 个 commit：yaoban `e559190`；文档 `dfe45e0 → 716f283 → 58f2485` | 两仓 git：yaoban HEAD=`87b54d6`、`e559190` 在链上；**3 个文档 hash 全在 EvoAlpha 仓**（17:36/17:38/17:40）；两仓 `origin/main..HEAD = 0` | ✅ 成立 |
| 6 | 盘后链 11/11 stage，15:35:05→17:39:04 = 2h04m，余约 56min | 间接印证：`data/yaoban.db` 17:37:14、`minute/1m/*.parquet` 17:37 批量写 ⇒ 时点自洽 | ✅ 成立 |
| 7 | 唯一非 0 为 `acceptance exit=2`（offplan_fills / tasks / YaobanTickDaemon），属既有长期失败 | **未复核** | ⚠️ 采信自述 |

**它主动提示的一件事（有效，非甩锅）**：`tick_monitor.py` 的午休 `pos_live` 修复「**只在工作区、HEAD 里是 inert 的**」（函数体在、调用点无），因该调用与 320 行**非本次**未提交重构同在 1 个 hunk，无法按 hunk 分离 ⇒ 未提交，已立待裁定。我复核 `git status`：确有大面积未提交改动，与「工作区 ≠ HEAD」自洽。**⇒ 运行态不受影响（生产走工作区），但 HEAD 不可复现该行为。**

---

## 2. D11 卖出裁量日报的汇报 + 复核

- 三项判据全 PASS，但属**空集口径**：当日 **D11 脑 0 次介入**（`brain_2026-09-14.jsonl` 未生成），原因是**无卖点触发**，不是开关失效。
- 交叉验证：`llm/2026-09-14/` 仅 D6×15、D11×0（对照 09-11：D11×11 / D6×265）；开关 ON（见 `MIDDAY_REVIEW_2026-09-14.md`）。
- **与我的独立复核一致**：`trader_daily_2026-09-14.json` → 当日实际成交 **1 笔**、卖出触发 **无**。

---

## 3. ⭐ 按你新准绳（实盘买卖贴合 = 基准），我发现两处口径要改

### 3.1 取样计划文档里有「主判据」与新基准冲突

`docs/PATTERN_QUEUE_SAMPLE_PLAN_20260915.md` 第 §5.3 节把
`|候选池 ∩ 选手池|` 写成**主判据**；§3.1 / §3.2.1 又把「选手 4 只」既称**候选池**、又称「**选手实买样本**」。
⇒ **两者在你今天的裁定下是不同东西**：候选池 = 诊断参考；实买 = 真值。**此文档口径须改。**

### 3.2 但 §6 的「≥3/4 否则回滚」应当**保留**

它不是保真度评分，而是**过滤器防误伤的必要条件闸门**（选手真买的票不许被筛掉）。
⇒ 降级的只是「把它当 KPI」，不是「不能拿它当护栏」。**这两件事不要一起砍。**

---

## 4. 9/14 实盘动作（新基准下的第一个数据点，全部取自账本/日报）

| 项 | 事实 | 来源 |
|---|---|---|
| 实盘成交 | **1 笔**：`001896` 买 11,600 @12.91（10:00，`reason=e4_support`，**计划外**） | `portfolio/ledger.json` |
| 追高幅度 | `off_plan_reason.detail = engine=e4_support; chg=**+9.3%**; pool_rank=1` ⇒ 违反 rule#8 ≤3% 上界（P0，当日 12:0x 已修） | 同上 |
| 计划内 4 只 | **实盘 0 成交**（002815 / 002913 / 000690 / 300335） | `trader_daily_2026-09-14.json` |
| 卖出 | **实盘 0 笔**；收盘 counterfactual 给 1 条止损建议（001896 @12.99，`executed=false`，且当日 T+1 锁定不可卖） | `close_decision_2026-09-14.json` |
| 符合度审计 | `001896: 偏离（计划外标的（盘中捕捉））` | `trader_daily_2026-09-14.md` |

**⇒ 用你的新基准打分：9/14「该买的没买（计划内 4 只零成交）+ 买的那只是计划外追高」。**
这个缺口比「候选池交集 0/4」更接近本质，**且换成新基准后依然成立**。

**卡点（必须先解决）**：新基准要「选手实盘买卖明细」当尺子，但**目前落盘里只有「选手候选池引用集」**（那 4 只），**没有选手实盘成交明细**。
⇒ 建议立一项：给选手实盘买卖建**有落文件的基准数据源**，否则新 KPI 无尺可量。

---

## 5. 现在压在你手上的待裁定项（合计 4）

| # | 事项 | 出处 |
|---|---|---|
| 1 | `tick_monitor.py`：① 单独提交（连带 320 行重构 + 清单）② 原作者确认后一并交 ③ 暂不提交 | `status.json` blockers[16] |
| 2 | 午休 `pos_live` 修复未进 HEAD（与 1 同源，但影响 HEAD 可复现性） | 同上 |
| 3 | `yaoban_tick_manual` 计划任务（今日被复用 2 次重启 daemon）是否注销 | D11 日报 |
| 4 | 「候选池交集」口径降级落地：改 §5.3 主判据 + 拆开 §3.1 的「候选池 / 实买」混用 | 本报告 §3 |

---

## 6. 9/15 取样日的关键前置（取自 automation，已复核其中第 1/2 项）

1. 09:30 前确认 `patterns/2026-09-15_pattern_pool.json`（`day/asof/n_pool`）+ `plans/2026-09-15_plan.json` 存在 ⇒ 否则 `rc=8` 全天禁新仓（红线）。
2. `t0_readiness.py` 要 0 FAIL。
3. **最脆一环：daemon 上午停摆**（9/14 实测 ~09:46 死过一次 ⇒ `scan rc=6` 连报 8 次、上午样本全丢）。09:30–10:00 三查：进程 / `_tick_daemon.beat` age≤60s / `pos_live.json` ≤120s。**`rc≠0` 必看 stderr**。
4. 盘中漏斗五档 `n_pool / n_pat_active / n_dropped_cold_l2 / n_hot_active / n_queue_capped` ← **这才是要拿的样本**。
5. 9/15 队列规模与 9/14 **不可比**（选股层已换），别拿 9/14 当基线。

---

## 7. 取证通道备忘（本机踩坑）

- **Bash 的 PATH 已整体损坏**（`dirname`/`tail`/`head` not found）⇒ 列目录/解析一律走 Python。
- **PowerShell 工具 stdout 不回显**（exit 0 但无输出）⇒ 「Python 写文件 + Read 回读」。
- automation 汇报的落盘位置：`~/.workbuddy/projects/<cwd-slug>/<session>.jsonl`（automation 工作区 slug = `f-WorkBuddyItem-automation-<创建时刻>`）；
  自动化自己写的高层摘要：`<automation cwd>\.workbuddy\automations\<automation-id>\memory.md`。
