# R4 最小切片 · 盘中 D6 否决权（设计冻结）

> status: active
> verified_at: 2026-09-15

> 冻结于 2026-09-13（周日）。目标：**9/14（周一）首个自主交易日，系统可自助下单且 LLM 真实行使否决权。**
> 对应路线图 R4 的前置最小集合；R4.2~R4.5 的完整放权不在本切片内。

## 一、问题：时序矛盾

R3.2 的 LLM 裁量层只挂在**盘后 15:35 决策链**上，而买入发生在**盘中 09:30–15:01**（`YaobanScanConfirm` 每分钟一轮）。
⇒ 盘后的裁量对当日买入**毫无作用**。否决权要生效，必须在买入之前可得。

## 二、六项冻结裁定（用户逐项确认）

| # | 裁定 | 理由 |
|---|---|---|
| 1 | **只接 D6 一条** | D6 是唯一有实测执行率证据的入场判据（5 个交易日与选手一致率 9/14）。D2/D3 板块阈值全是占位值（`calibrated=false`）、D4/D5 只有定性表述 → 接入等于用**未标定**判据否决买入 |
| 2 | **当日首次判一次并锁定至收盘** | 见 §四。不锁定 ⇒ 同一标的可被改判 ⇒ 否决权自我失效 + 成交记录无法解释 |
| 3 | **计划内 + 计划外全覆盖** | `scan_and_confirm` 两条路都会真买；计划外（`off_plan_reason`）正是历史 3 例「候选池 ≠ 完整交易集」的来源，最需要裁量把关 |
| 4 | **产完整 `decision_digest`**（R1.6 契约） | R4 验收要求「全链 provenance 完整」；轻量行不达标 |
| 5 | **降级 = 放行** | 见 §五。语义是「退回无否决权现状」，相对本次变更是**零新增风险** |
| 6 | 配套：`max_single_weight` 0.45 → **0.30** | 对齐 SOP「单票 ≤30%」；且 45%×5% 止损 ≈ 总资金 2.25% > 「单笔亏损 ≤2%」纪律。改 0.30 后 15 万×5% = 7500 = **1.5%**，两条纪律同时满足 |

## 三、数据流（盘中买入链）

```
候选池 → 买点触发（现状） → 【新增】LLM 判 D6 → 通过则买入（现状）
                                    │
                                    └─ C_reject ⇒ allowed=False ⇒ scan 侧 continue（跳过该标的）
```

- 插入点：`scripts/scan_and_confirm.py` 的 `for tg in triggered[:1]:` 循环首部，
  **早于** `record_autonomous_decision()` 与 `buy()`。
- 分钟序列复用：触发检测阶段已拉过 `df`，存进旁路字典 `_min_df`（**不能放进 `tg`** —— 它要进
  `candidates_snapshot` 的 JSON 序列化）；且必须在 `api.disconnect()` 之前填充。
- 只在 `triggered` 非空时调用（绝大多数分钟无触发 ⇒ 不调 LLM）。

## 四、当日锁定（本设计最易被改坏的地方）

`llm.consult` 缓存键 = `sha256(point | template_version | model | snapshot_hash)`。

⚠️ **盘后链**的 `snapshot_hash = _sha(dict(code, day, feats))` **含盘中特征** ⇒ 键随分钟变化
⇒ 5 分钟 TTL 形同虚设。若盘中直接复用，结果是：
- 每只标的**每 5 分钟重新真调一次**（不是「当日只调一次」）；
- 同一标的可能 10:05 判 `C_reject`（否决）、10:20 判 `A_optimum`（放行）⇒ **否决权自我失效**。

**盘中改用日级稳定哈希**：`intraday_snapshot_hash = sha256("intraday-d6-v1|day|code")`
（**故意不含任何盘中特征**），并把 TTL 拉到**当日 15:30**（`lock_ttl()`，下限 60s）。
两者合起来才构成锁定：
- 键稳定 ⇒ 同一标的当日命中同一缓存条目
- TTL 覆盖 ⇒ 该条目当日不过期

⚠️ **锁定的是结论，不是输入** —— 判定时喂给 LLM 的 `obs` 仍是当时的实时分时特征，并随 `_persist` 落盘留证。

⚠️ **盘后链的键未改动** ⇒ R3.2 的 `replay_hash` 基线不受影响（回归锚见 `test_snapshot_hash_differs_from_chain_key`）。

## 五、降级语义（⚠️ 最容易读反的一条）

D6 的保守档是 `B_medium`（可观察不优先），**不是** `C_reject`。因此：

| LLM 状态 | 处置 | 说明 |
|---|---|---|
| `ok` + `C_reject` | **否决** | 唯一否决路径 |
| `ok` + `A_optimum` / `B_medium` | 放行 | |
| `degraded` / `schema_failed` / `unreproducible` | 放行 | `veto_reason=degraded_pass` |
| 超时 / 网络异常 / 内部异常 | 放行 | `veto_reason=exception:*`，`status=error` |

**为什么「放行」是安全的**：降级时系统行为**等于本次变更之前的现状**（无否决权）。
相对于「引入否决权」这个变更，降级路径**没有引入任何新风险**。
⚠️ 这是「零新增风险」，**不是**「资金保守」—— 若有人把它改成「降级=拒买」，
等于用**已被 9/11 反事实证伪**的判据去阻止买入，且 LLM 一挂就全面停买。

⚠️ 必须能在 artifact 里区分 `degraded` 与真·`B_medium`（否则无法判断否决权是否长期空转）。

## 六、artifact 落点与契约

- 路径：`outputs/decision_chain/intraday/intraday_<day>.jsonl`（append，每判定一行）。
- **否决 / 放行 / 降级 / 异常四条路径都必须落 digest**。
  ⚠️ 首版把落盘写在 `try` 内 → LLM 抛异常时 `digest=None` ⇒「被放行的买入无痕」，
  由 `test_http_error_passes` 抓出后改为**统一出口**。
- digest 口径：`side = buy`（放行）/ `skip`（否决，R1.6 明文「没做什么也必须有 digest」）；
  `executed=False`、`authority="llm_veto"`（本模块只负责判定，成交由 ledger 另记，R-IMPL-5）。
- `rules_fired = HARD_RULES["ENTRY"]`、`discretions=[D6 记录（含 model/prompt_sha256/cli_version）]`、
  `sop_version_id` / `params_hash` 复用 engine 口径。
- 汇总：`intraday_veto.summarize(day)` 供状态卡与 `llm_health` 使用。

## 七、不改动范围（明确边界）

- ❌ 不改 `tick_monitor.py`（卖出侧）与 `_tick_watch.py` 看门狗。
- ❌ 不改盘后链现有 LLM 缓存键语义。
- ❌ 不改 `triggered[:1]` 的每轮单标的限流、不改 qty 计算逻辑。
- ❌ **不碰 `config/parameters.toml`** —— 它在 `persona/versions/v0.toml` 的 **frozen 组**，改动会触发人格版本纪律（须出 v1）。
- ✅ `ledger.py` / `scan_and_confirm.py` 属 `referenced` 组（漂移只溯源、不判失败）⇒ 本次改动**不需要出 v1 版本**；
  且 `max_single_weight` **不在** `[semantics]` 契约里（已核）。

## 八、已知缺口（诚实登记）

1. **`action.kind` 枚举没有为「真实盘中决策但被否决」预留值**
   （现只有 `["fill","audit_counterfactual","shadow"]`）。
   本切片用 `kind="shadow"` + `authority="llm_veto"` 组合过校验，靠 **authority** 与盘后影子链区分
   （authority 不进 `replay_hash`，符合哈希三分法）。建议 R5.0 扩展枚举（如 `live_veto`）时一并改。
2. **买入成交本身仍不产 digest** —— 走 ledger 既有 provenance（`decision_id` + `candidates_ref`）。
   把 ③④ 段整体搬进盘中属 **R4.2「下单权交决策环」**，不在本切片。
3. 本切片**不接入** ②③⑤⑥ 段 → 盘中买入路径仍非「六段决策环」驱动，仅叠了一层 D6 否决。

## 九、验收对照（R4）

| 验收项 | 本切片状态 |
|---|---|
| 全链 provenance 完整 | ✅ 否决与放行均产 digest + 账本 provenance 可经 `candidates_ref` 关联 |
| 无 off-plan fills | ⏸ 由 R0 既有 acceptance 检查覆盖（`offplan_fills`） |
| 风控 veto 无法绕过 | ✅ 否决在 `buy()` 之前；ledger `_validate_buy_policy` 独立生效 |
| 改循环体后必跑 `--selftest` | ⏸ 本切片未改 `_tick_watch.py`/`tick_monitor.py` |
| ⚠️ Python 进程不随文件修改更新 | ⚠️ **9/14 09:30 前必须确认 scan 任务拉起的是新码**（任务每次运行都是新进程 ⇒ 无需重启常驻；但 `_tick_watch` 常驻链不受影响） |

## 十、回归锚

`tests/test_intraday_veto.py`（**29 项**）四类不变量：
1. 否决语义（只有 `C_reject` 丢弃；`veto_choice` 单一事实源防枚举漂移）
2. **降级方向**（degraded/unreproducible/超时/异常一律放行）
3. **当日锁定**（日级键稳定 + 不含盘中特征 + 与盘后链键不同 + 同日二次命中不重调）
4. 绝不阻断 scan（畸形 df / None / 异常均不抛）+ digest 契约与落盘

## 十一、变更清单

| 文件 | 变更 |
|---|---|
| `src/decision_chain/intraday_veto.py` | **新增**（判定 + 日级锁定 + digest 落盘 + summarize） |
| `src/decision_chain/llm.py` | `consult()` 新增 `cache_ttl` 参数（默认 None ⇒ 盘后链行为不变） |
| `scripts/scan_and_confirm.py` | 引入模块；`_min_df` 旁路缓存；买入前插否决检查（含 try/except 兜底） |
| `portfolio/ledger.py` | `DEFAULT_POLICY.max_single_weight` 0.45→0.30 + 注释更正 |
| `portfolio/ledger.json` | **真正生效处**：policy 0.45→0.30（经 `ledger.transact()`，`_revision` 2→3；备份 `ledger_before_weight030_20260913_102120.json`） |
| `scripts/initialize_main_ledger.py` | 新建账本默认权重同步为 0.30 |
| `tests/test_scan_freshness.py` | mock policy 同步 0.30 |
| `tests/test_intraday_veto.py` | **新增 29 项** |
