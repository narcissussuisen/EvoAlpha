# 2026-09-15 战法池 / 确认队列取样计划

> status: active
> verified_at: 2026-09-15

> 生成于 2026-09-14 盘后（EvoAlpha 盘后施工）。
> **唯一硬目标（用户 2026-09-14 裁定）**：先拿到**一天的实盘队列样本**，比继续盲调参数可靠。
> 因此本次施工的一切取舍都服从一条：**保证 2026-09-15 开盘能产出真实的 `confirm_queue` 样本**。

---

## 1. 次日战法池是否就位

| 字段 | 值 | 口径校验 |
|---|---|---|
| `day` | 2026-09-15 | 必须 = 目标交易日 |
| `asof` | 2026-09-14 | 必须**严格早于** `day`（T-1） |
| `lookback` | 4 | 与 `plan_daily.py` 的 `win_days` 同口径 |
| 池规模 | 见 §3「修后」 | 必须 > 0 |
| 产物路径 | `outputs/patterns/2026-09-15_pattern_pool.json` | scan 侧 `PATTERN_DIR` 只读此路径 |
| 落盘方式 | 由 `plan_daily.py::build_pattern_artifact` 与日计划**共用同一次全市场遍历**产出 | 见 §2 |

**为什么口径是硬约束**：`scan_and_confirm.py::load_pattern_pool(day)` 会校验
`doc['day'] == day` 且 `doc['asof'] < day`，任一不满足即返回 `None` ⇒
启用 `--pattern-gate` 时该轮 `rc=8`（**fail-closed，全天禁新仓**）。
这不是"少买一点"，是"当天拿不到任何队列样本"——与本次唯一硬目标直接冲突。

---

## 2. 本次施工做了什么（三条，按风险排序）

### 2.1 战法池并入 `plan_daily.py`：一次 IO 出两份产物

原先战法池由 `scripts/build_pattern_pool.py` 单独跑：它自己再做一次
`load_all_daily()`（实测日线载入 ~900 s + 形态计算 ~1200 s ≈ **35 分钟**），
而 `plan_daily.py` 盘后**已经为日计划付过同一笔全市场遍历**，读的还是同一份
`core.daily_src` + `build_daily_map`。分开跑纯属把 IO 付两遍。

收敛后：`plan_daily.py` 一次载入 → 两份产物
（`outputs/plans/<day>_plan.json` + `outputs/patterns/<day>_pattern_pool.json`）。
schema 由 `core/pattern_pool.py::write_pattern_pool` **单点保证**（唯一写入口），
scan 侧读取契约不变。

两个工程细节：
- **先落战法池、后算日计划**：战法池是 scan 侧 fail-closed 的硬依赖，先落盘可让
  "后续日计划步骤失败"不影响次日战法池的可用性。
- **原子替换**（tmp + `os.fsync` + `os.replace`）：scan 每 60 s 读一次，
  读到半截 JSON 会退化成 `None` ⇒ `rc=8`。
- **战法池失败不打死日计划**（`try/except` 只降级自身），但**不静默**：
  异常写 stderr，供盘后链 `log-error-digest` 捞取。

### 2.2 三项标定修复（用户指定）

| # | 问题 | 根因 | 修法 |
|---|---|---|---|
| ① | 池里含 ST / 退市风险标的 | 池层无名称过滤；实测 `000078 ST海王`、`000909 *ST数源`、`000004 *ST国华` 等 | 池层按名称表剔除 `*ST`/`ST`；**名称缺失只计数不排除**（`n_no_name`）——按"无名称即排除"会误伤名称表覆盖不全的正常票 |
| ② | `zt_huicai` 全池 **0 命中** | `config/parameters.toml [strategy.zt_huicai] volume_shrink_ratio = 0.0`，语义明写「**0 = 不启用缩量过滤器**」；但 `detect_zt_huicai` **无条件**套用 `vol_ratio[i] < shrink` ⇒ 判据退化为 `v < 0.0`，而 `v` 恒 ≥ 0 ⇒ **该检测器 100% 返回全 False** | 尊重配置语义：`shrink <= 0` 即关闭过滤器。**不是**"把阈值调大"——那是在给一个已被真实样本证伪的过滤器续命 |
| ③ | 池过宽（2308 只） | `qu_shi_fanbao`（反包）**单独命中**的票在选手实买样本里零覆盖 ⇒ 纯噪声扩容 | 剔除 `patterns == ['qu_shi_fanbao']`（**仅反包**）；与其它战法共振则保留。`--keep-fanbao-only` 保留消融对照入口 |

### 2.3 ⚠️ 两条**刻意不做**的硬过滤（已实证会筛掉真值）

| 候选过滤 | 实测后果 | 结论 |
|---|---|---|
| 「信号日必须在 `asof` 当日（T-1）」 | 选手 4 只**全部落选**（其信号日为 T-2/T-3） | **只能当排序权重**，不可下沉为门槛 |
| 「≥2 战法共振」 | 池仍有 292 只，但选手**只剩 1/4** | 同上 |

两条已写进 `core/pattern_pool.py::build_pattern_pool` 的 docstring，
并注明"将来若有人『优化』回来，请先看这两条实测"。

---

## 3. 「修前 / 修后」对照

### 3.1 修前（既有产物，未经本次修复）

产品：`outputs/patterns/2026-09-14_pattern_pool.json`（构建于 09-14 13:49，
`asof=2026-09-11`，`lookback=4`）。

| 指标 | 值 |
|---|---|
| 扫描标的 | 5644 |
| 日线不足跳过 | 41 |
| **池规模** | **2308** |
| `by_pattern` | `huigui` 1713 / `qu_shi_fanbao` 588 / `xianren` 7 / **`zt_huicai` 缺席（= 0）** |
| 共振数分布 | 1 战法 2016 / 2 战法 289 / 3 战法 3 |
| 仅反包命中 | 588 |
| 含 `ST` / `*ST` | **101** |
| 无名称 | 183 |

按新口径**事后分解**（同一 `asof`、同一标的全集，故为**受控对照**）：

```
2308  (修前池)
 −588  (剔除仅反包命中)
 =1720
  −87  (在余下 1720 里再剔 ST/*ST)
 =1633  → by_pattern = {huigui: 1626, xianren: 7}   (−29.2% vs 2308)
```

**选手 4 只存活检验**（这是"零损失"的判据，不是池规模好看）：

| 代码 | 名称 | 在池中 | `patterns` | 信号日 | 新鲜度 |
|---|---|---|---|---|---|
| 002436 | 兴森科技 | ✅ | `['huigui']` | 2026-09-09 | T-2 |
| 603936 | 博敏电子 | ✅ | `['huigui','qu_shi_fanbao']` | 2026-09-09 | T-2 |
| 605162 | 新中港 | ✅ | `['huigui']` | 2026-09-08 | T-3 |
| 600644 | 乐山电力 | ❌ | — | — | — |

⇒ 池中 **3/4**；**剔除仅反包后仍 3/4**（603936 因与 huigui 共振被保留，未被误伤）。

### 3.2 修后（本次修复后，`asof=2026-09-14`）

> 落盘后由 `plan_daily.py` 的盘后链 `next_plan` stage 产出；
> 本节数字在产物落盘后回填（`stats` 字段直接给出口径内计数）。

产物：`outputs/patterns/2026-09-15_pattern_pool.json`（**375,857 bytes**，
`built_at=2026-09-14 17:11:29`，由盘后链 `next_plan` stage 的 `plan_daily.py` 产出）。

| 指标 | 值 |
|---|---|
| `day` / `asof` / `lookback` | **2026-09-15 / 2026-09-14 / 4** ✅ |
| 扫描标的 | 5644 |
| 日线不足跳过 | 40 |
| **池规模** | **1546** |
| `by_pattern` | `huigui` 1444 / **`zt_huicai` 99** / `xianren` 3 |
| 共振数分布 | 1 战法 1153 / 2 战法 334 / 3 战法 59 |
| `bars_since_sig` 分布 | 0: 183 / 1: 143 / 2: 390 / 3: 830（**T-1 当日信号 183 只**） |
| `n_excluded_st` | 212（口径：**扫描集**里被判为 ST/*ST 的标的数，**不是**"池内 ST 数"） |
| `n_excluded_fanbao_only` | 479 |
| `n_no_name` | 420（扫描集口径；**池内**无名称 138 只，按设计**保留**） |

**池内自检（对产物直接统计，非推断）**：

| 检验项 | 结果 |
|---|---|
| 池内 ST/*ST 残留 | **0** ✅ |
| 池内「仅反包命中」残留 | **0** ✅ |
| 每条的字段数 | 7（`sym` / `pattern` / `pattern_cn` / `patterns` / `sig_date` / `bars_since_sig` / `close_asof`）；文档级 9 字段契约不变 |
| 生产读取链路 | `scan_and_confirm.load_pattern_pool('2026-09-15')` → **OK**（非 None ⇒ 不会 rc=8） |

### 3.2.1 ⭐ 意外收获：`zt_huicai` 的修复把选手样本召回由 3/4 提升到 **4/4**

| 代码 | 名称 | 修前（asof=09-11） | 修后（asof=09-14） |
|---|---|---|---|
| 002436 | 兴森科技 | IN `['huigui']` | IN `['huigui','zt_huicai']` |
| 603936 | 博敏电子 | IN `['huigui','qu_shi_fanbao']` | IN `['qu_shi_fanbao','zt_huicai']` |
| 605162 | 新中港 | IN `['huigui']` | IN `['huigui','zt_huicai']` |
| 600644 | 乐山电力 | **OUT** | **IN `['zt_huicai']`** ✅ |
| **合计** | | **3/4** | **4/4** |

⇒ `zt_huicai` 从「恒 0 命中」恢复后，不仅把 600644 乐山电力（选手实买样本之一）
从池外召回，还让另 3 只获得了共振。**这是"池层过滤器修对了"最直接的证据**。

⚠️ **但必须同时记下代价**：`zt_huicai` 现在的缩量确认是**关闭**状态，
单战法命中从 0 跳到 99 只（占池 6.4%）。这 99 只里有相当部分是「涨停回踩 + 站上
MA5/MA20」但**没有量能确认**的票——它在召回真值的同时也必然引入噪声。
**判断口径**：看 9/15 及后续队列里 `pattern=zt_huicai` 的票的**实际表现**，
而不是现在去调阈值。若其胜率显著低于 `huigui`，再单独给它加量能确认
（届时是**基于样本**的标定，不是基于直觉）。

### 3.3 关于两个 `asof` 不同的说明（口径坦白）

修前产物 `asof=2026-09-11`，修后产物 `asof=2026-09-14`——**两者窗口不同，
池规模不可逐只对齐**。原因：那份修前产物是本次修复前（09-14 13:49）跑的，
当时 09-14 的日线尚未定稿（`rebuild` 收盘后才落库），脚本取到的最新源日只有 09-11。

因此：
- **①②③ 三个修复的受控证据用 §3.1 的事后分解**（同 `asof`、同全集，精确）+ §4 的
  40 只真实数据集成测试；
- **§3.2 的修后全池数字**只用于说明"次日在用的池长什么样"，不与修前逐只对比。

### 3.4 `zt_huicai` 修复的最小可复现证据

修前"恒 0"是**可证的**、不是估计：判据 `vol_ratio[i] < 0.0`，而
`ind.vol_shrink_ratio(df, n=5)` 语义为 `v5/v5_prev`，**恒 ≥ 0** ⇒ 谓词恒假。

修后：在 40 只真实标的的集成测试上，`by_pattern` 由 `{}`（无 zt_huicai）
变为包含 `zt_huicai: 1`；全池计数见 §3.2。

---

## 4. 集成验证（真实数据，非 mock）

**40 只子集**（真实 `load_all_daily()` 数据，跑改后代码全链路）：

```
池 40 → 10 只
ST剔除 4 / 仅反包剔除 11 / 无名称 0
by_pattern = {huigui: 9, zt_huicai: 1}
schema 9 字段完整；asof == day 被正确拒绝（GUARD OK）
```

**单元测试**：新增 `tests/test_pattern_pool_filters.py`（13 项）与
`tests/test_tick_lunch_pos_live.py`（9 项）。前者钉住：`volume_shrink_ratio == 0.0`
前提自检、`shrink` 恒非负（根因锚）、`>0` 仍生效（消融回归要用）、
ST 与 `*ST` 剔除、**缺名只计数不排除**、仅反包剔除但共振保留、
`--keep-fanbao-only` 可恢复、9 字段 scan 契约、原子替换不留 `.tmp`、
两份产物共用写入口（源码断言）、`plan_daily` 侧 `asof` 守卫。

---

## 5. 明日（2026-09-15）观察清单

### 5.1 开盘前（08:20–09:30）

| # | 动作 | 判据 |
|---|---|---|
| 1 | 确认 `outputs/patterns/2026-09-15_pattern_pool.json` 存在 | `day=='2026-09-15'`、`asof=='2026-09-14'`、`len(pool)>0` |
| 2 | 确认 `outputs/plans/2026-09-15_plan.json` 存在 | `scan_and_confirm.py::_load_day_plan` 对计划缺失是 fail-closed |
| 3 | `python -X utf8 tools/t0_readiness.py` | 要求 **0 FAIL** |
| 4 | **确认 `YaobanTickDaemon` 在 09:30 真的起来了** | 见 §5.1.1 —— 这是本次取样**最脆的一环** |

#### 5.1.1 ⚠️ 最脆的一环：daemon 上午停摆会让「样本」直接归零

2026-09-14 当天实盘暴露：**daemon 在 ~09:46 停摆**，随后
`scan rc=6「伴随监控失效，禁止新仓: tick stale >2m」` **连报 8 次（09:40–13:00）**，
并推送告警 `monitor-gap:2026-09-14:tick:0935`。
⇒ 这段时间 scan **根本不产出候选队列**，等于上午的样本全部丢失。

**这与「午休 pos_live 陈旧」（今日已修的 rc=6 成因）是两个不同成因**：后者是窗口跳过、13:01 自愈；
前者是**进程真的死了**。今日只影响上午（当日买入额度 1/1 已用尽，无实际损失），
但 9/15 是**取样日**，停摆＝样本残缺。

**逐条核验（09:30 起，每 15 分钟一次）**：

| 检查点 | 命令/文件 | 通过判据 |
|---|---|---|
| 进程在 | `tasklist` 里有 `pythonw.exe` 且持有 `outputs/intraday/_tick_daemon.lock` | 锁内 pid == 存活进程 |
| 心跳在 | `outputs/intraday/_tick_daemon.beat` | mtime age ≤ 60s（daemon 每 5s 刷） |
| 数据新鲜 | `outputs/intraday/pos_live.json` | `date=='2026-09-15'` 且 `time` 与当前相差 ≤ 120s |
| scan 未被闸 | `outputs/task_logs/2026-09-15/*_scan.json` | `exit_code==0`；**rc=6 必须同时看 stderr** |

> ⚠️ **排查纪律**：`rc≠0` 的原因（如 `tick stale >2m`）写在 **stderr**，stdout 可能为空
> —— 只看 stdout 会误判成「静默禁仓」（2026-09-14 已踩过一次）。

> ℹ️ 明日启动链**已在盘后验证过无阻塞**：我 15:5x 重启的 daemon 因
> `tick_monitor.py:362`「已过盘后窗口(AFTER_HOURS_END=15:30)，退出」**立即返回 0**，
> 且该早退分支**不清锁**，遗留 `_tick_daemon.lock`（pid=27036，**实测已死**，锁 mtime 超龄 5743s）。
> 明早走 `_acquire_daemon_lock`（`tick_monitor.py:339-348`）的**双判据回收**：
> pid 已死 → `unlink` → 重试 `O_EXCL` 获锁。`YaobanTickDaemon` 实测
> `State=Ready / NextRun=2026-09-15 09:30:30`。

### 5.2 盘中（每轮 scan 的漏斗五档）

scan 每轮会打印，并落痕到 `outputs/intraday/confirm_<YYYYMMDD>_<HHMM>.json → pattern_meta.funnel`，
**这五档就是"样本"的原始素材**：

> **⚠️ 为什么没法在盘中之前就"预估"这五档**：`--pattern-gate` 关闭时，scan 落痕里
> `pattern_meta` 只有 `{asof: null, enabled: false}`，**中间三档根本不存在**；
> 而落痕里只有 `movers`（涨幅前 20）与 `candidates_snapshot`，**不落全市场活跃集
> （`allq`）**，`board_momentum.json` 也只有板块级（12 个热点 L2）而非标的级。
> ⇒ 「池 ∩ 今日活跃」的交集大小**只能在盘中第一次读到**。
> 这正是"9/15 是取样而不是验收"的原因——不要为了让它"看起来对"而先去调参。

| 字段 | 含义 | 预期 |
|---|---|---|
| `n_pool` | 战法池规模（全日不变） | 与 §3.2 一致 |
| `n_pat_active` | 形态合格 ∩ 今日活跃（过 `rough_screen` 且可交易） | 数十量级 |
| `n_dropped_cold_l2` | 因板块不热被挡（既非当日热点前 12、也非 T-1 强主线） | 主要收窄档 |
| `n_hot_active` | 剔冷门后的候选数（**封顶前**） | — |
| `n_queue_capped` | 最终队列长度（上限 `PATTERN_QUEUE_MAX=15`） | **这是要拿的样本** |

> ⚠️ 若 `n_queue_capped` 长期为 0，**先看 `n_pat_active` 是否为 0**：
> - `n_pat_active == 0` ⇒ 战法池与今日活跃**没有交集**（池口径问题，查 `asof`）；
> - `n_pat_active > 0` 而 `n_hot_active == 0` ⇒ 是**板块层**（`HOT_L2_TOP=12` + T-1 强主线）
>   把票全挡了，与形态层无关。**别把这两种情况混成一个结论。**

### 5.3 收盘后与选手候选池对照

需要与选手 9/15 候选池逐只对照的字段（`confirm_queue` 每条已带齐）：

| 字段 | 用途 |
|---|---|
| `sym` / `name` | 交集计数（**主判据**：`|候选池 ∩ 选手池|`） |
| `pattern` / `pattern_cn` / `patterns` | 战法是否对得上（`huigui` = 上升回档是选手主战法） |
| `sig_date` / `bars_since_sig` | 信号新鲜度是否落在选手可接受的 T-2/T-3 |
| `l2` / `l2_rank` / `l2_name` | 板块是否对得上（选手"只选热点板块，冷门概念不玩"） |
| `in_hot` / `strong_mainline_only` | 该票是被**当日热度**收进来的，还是被 **T-1 强主线豁免**收进来的 |
| `in_plan` | 是否在日计划内（排序权重①） |
| `chg` | 防追高检验（进场另受 e4 的 ≤3% 上界约束） |

### 5.4 一个必须现在就说明的期望管理

`--pattern-gate` 启用后，**候选池构造方式发生了实质变化**：
`confirm_queue = 战法池 ∩ 今日活跃`，不再是"全市场涨幅前 8"。

⇒ **9/15 的队列规模与 9/14 不可比**。9/14 的"候选池交集 0/4"是**旧选股层**的
结果（涨幅榜 vs 回踩低吸，构造互斥）；9/15 才是新选股层的第一个样本。
**不要用 9/14 的数字当基线去判 9/15 是"变好"还是"变坏"。**

---

## 6. 风险与回退

| 风险 | 触发条件 | 处置 |
|---|---|---|
| **次日 `rc=8` 全天禁新仓**（红线） | `2026-09-15_pattern_pool.json` 缺失或 `asof/day` 口径违规，**且** scan 行已加 `--pattern-gate` | 接线前必须通过 §5.1 第 1 项的硬验收；**验收不过则不接线**（保持默认关，旧行为 + 显式告警），宁可少一层筛选也不拿"零样本"换 |
| 战法池生成失败但日计划成功 | `plan_daily.py` 内 `build_pattern_artifact` 抛异常 | 战法池缺失 ⇒ 同上，**不接线**；异常已写 stderr 供复盘捞取 |
| 池层收窄过度 | 新口径把选手实买样本筛掉 | §3.1 的"选手 4 只存活检验"是对照锚：修后必须仍 ≥3/4，低于此即回滚 ①②③ |

---

## 7. 附：本次施工的代码落点

| 文件 | 改动 |
|---|---|
| `scripts/plan_daily.py` | 新增 `build_pattern_artifact()`；`main()` 内共用 `load_all_daily()` 出两份产物 |
| `src/core/pattern_pool.py` | 新增 `load_stock_names()` / `write_pattern_pool()`（唯一写入口，原子替换）；池层 ST 剔除 + 仅反包剔除 |
| `src/core/strategies.py` | `detect_zt_huicai` 尊重 `volume_shrink_ratio <= 0` = 关闭过滤器 |
| `scripts/build_pattern_pool.py` | 新增 `--keep-fanbao-only`；改用共享写入口；打印各剔除计数 |
| `scripts/tick_monitor.py` | daemon 在**上午收盘之后**的窗口外结转写 `pos_live`（修 13:00 首轮 `rc=6`） |
| `tests/test_pattern_pool_filters.py` | 新增 13 项（池层过滤 + 写入口契约） |
| `tests/test_tick_lunch_pos_live.py` | 新增 9 项（AST 防回退 + 端到端 daemon replay） |
