# decision_digest 契约 v1

> status: active
> verified_at: 2026-09-15

> **自动生成**，请勿手改。生成器 `yaoban-system/tools/build_decision_digest_schema.py`；
> 契约的**单一事实源**是 `yaoban-system/src/core/decision_digest.py`（常量 `FIELDS` / `IMPLEMENTATION_HASH_FIELDS` / `EXECUTION_CONTEXT_FIELDS` / `LAYER_RULES`）；
> 机器可读：`persona/decision_digest_schema_v1.toml`；样例：`persona/_decision_digest_sample_v1.json`。

## 一、它解决什么问题

R5.0 要求把「**实现层**」与「**有效性层**」分开判：

| 层 | 问题 | 判据 | 需要净值吗 |
|---|---|---|---|
| **实现层** | 代码有没有按 SOP 规格执行？ | 6 条**机械**规则（见 §三） | **不需要** |
| **有效性层** | 赚钱了吗？ | 只能由 R5.1 净值判定器（vs 双基准臂，60 日） | 需要 |

⭐ **核心洞察**：两者的分界可以**机械判定** ——

> **`replay_hash` 不变 = 纯实现层改动（refactor 不改行为）→ 可直接晋级；**
> **`replay_hash` 变化 = 行为改动 → 必须进 60 日有效性队列。**

这把「这次改动到底是不是只动了实现」从主观判断变成了一次哈希比对。

## 二、digest 覆盖的链条

```
inputs_snapshot → rules_fired → discretions → risk_gate → order_intent → fill | not_executed
```

### 字段契约（三层分类）

| 字段 | 类型 | 层 | 必填 | 说明 |
|---|---|---|---|---|
| `digest_id` | str | **identity** | ✅ | 本 digest 的稳定标识；seq 为当日序号，hash8 = replay_hash 前 8 位 |
| `digest_revision` | str | **identity** | ✅ | schema 版本；跨版本比对必须显式声明 |
| `decision_id` | str | **identity** | ✅ | **必须与 ledger 的 decision_id 一致**（R0.4）；ledger 侧空值即拒单 |
| `day` | date | **identity** | ✅ | 交易日（YYYY-MM-DD）；同一 digest 的 day 必须与 timing.decision_ts 的日期一致 |
| `sym` | str | **identity** | ✅ | 标的代码（6 位数字）；与 ledger fill 的 sym 必须完全一致 |
| `side` | enum(buy,sell,hold,skip) | **identity** | ✅ | hold/skip 也必须有 digest —— 否则「没做什么」不可审计 |
| `timing.signal_ts` | datetime | **implementation** | ✅ | 信号产生时刻；格式 'YYYY-MM-DD HH:MM:SS'。时序契约链的第 1 环 |
| `timing.decision_ts` | datetime | **implementation** | ✅ | 作出决策的时刻。必须 ≥ signal_ts —— 否则是回溯成交（R0.3 禁止） |
| `timing.recorded_at` | datetime | **implementation** | ✅ | 落账时刻。必须 ≥ decision_ts —— 否则时序倒挂 |
| `timing.freshness_sec` | number | **implementation** | ✅ | decision_ts − signal_ts；>120s 一律拒单（tick 卖出豁免，见 SELL_EXECUTION_CONTRACT §2） |
| `timing.tick_executor` | bool | **implementation** | ✅ | 是否由 tick 执行器产生的决策（决定是否适用 120s 新鲜度门） |
| `inputs.candidate_snapshot_id` | str | **implementation** | ✅ | 候选池快照 id（R0.4 蓝图要求）；无候选池的卖出决策可写空串 |
| `inputs.market_snapshot_hash` | str | **implementation** | ✅ | 决策所依据的行情数据 canonical hash（涉及标的的 bar 序列）—— 重放的基准 |
| `inputs.sop_version_id` | str | **implementation** | ✅ | 人格版本 id，如 v0；取自 persona/versions/registry.json |
| `inputs.params_hash` | str | **implementation** | ✅ | config/parameters.toml 的 sha256（R1.5 frozen 组） |
| `decision.rules_fired` | list[str] | **implementation** | ✅ | ⭐ 必须是 R1.1 SOP 表里的规则 id（如 GEN-HOLD-01）；无规则触发时为空数组 |
| `decision.discretions` | list[table] | **implementation** | ✅ | ⭐ 每项 point_id 必须是 R1.2 的 D1–D10；output 必须落在该点的枚举内。model/prompt_sha256/cli_version 是可重放性的前提（计划 §4.2） |
| `decision.risk_gate` | table | **implementation** | ✅ | 风控 veto 不可被裁量绕过；checks 列出实际执行的门禁项 |
| `decision.narrative_refs` | list[str] | **implementation** | — | 本轮引用的 R1.4 记忆 id（MEM-*）或自述字段路径 |
| `action.order_intent` | table | **implementation** | ✅ | 打算做什么。`reason` 应是 rules_fired 或裁量点的可读映射，不是自由文本下单理由 |
| `action.executed` | bool | **implementation** | ✅ | **是否真成交**。审计重建必须为 false（SELL_EXECUTION_CONTRACT §4） |
| `action.kind` | enum(fill,audit_counterfactual,shadow) | **implementation** | ✅ | 与 SELL_EXECUTION_CONTRACT §4 对齐；audit_counterfactual 是被 return 5 守卫永久禁执行的重建流水线产物 |
| `action.authority` | str | **implementation** | ✅ | 执行权威来源；真成交固定为 `account.fills`（防双重计算的机器可读标记） |
| `action.fill_ref` | str | **implementation** | — | executed=true 时指向 account.fills 的定位键（sym+ts+qty+px） |
| `outcome.pnl_attributable` | number | **effectiveness** | — | 本 digest 关联的已实现盈亏。**仅供 R5.1 归因，不用于实现层判定** |
| `outcome.effectiveness_basis` | str | **effectiveness** | — | 该盈亏属于哪段净值（R5.2 版本分段）；禁止跨段拼接 |
| `replay_hash` | str | **identity** | ✅ | ⭐ 对**决策内容**（IMPLEMENTATION_HASH_FIELDS）的 canonical sha256。重放一致性的唯一判据：hash 相同即同决策 |

## 三、分层判定规则（R5.0 的机械分判据）

| 规则 | 层 | 判据 | 含义 | 结论 |
|---|---|---|---|---|
| **R-IMPL-1** | implementation | `replay_hash 不变` | 该改动属**实现层**（refactor / 性能优化 / 日志调整等不改变决策内容） | 可直接晋级（无需净值） |
| **R-IMPL-2** | implementation | `provenance_complete` | 必填字段齐备 + decision_id 已在 ledger 登记（R0.4） | 失败即实现层不达标，禁止晋级 |
| **R-IMPL-3** | implementation | `timing_ok` | signal_ts ≤ decision_ts ≤ recorded_at；tick 执行器豁免 120s 新鲜度门，其余 >120s 拒单 | 失败即实现层不达标 |
| **R-IMPL-4** | implementation | `sop_conformant` | rules_fired ⊆ SOP 规则 id；discretions[].point_id ⊆ D1–D10 且 output ∈ 枚举 | 失败即实现层不达标（出现表外理由 = 绕过 SOP） |
| **R-IMPL-5** | implementation | `authority_not_double_counted` | kind=audit_counterfactual ⇒ executed=false；executed=true ⇒ authority='account.fills' | 失败即实现层不达标（会导致审计重建被误当成交、双重计算收益） |
| **R-EFF-1** | effectiveness | `replay_hash 变化` | 属**行为改动**（决策内容变了） | **必须**进 60 日有效性队列，不得仅凭实现层判据晋级 |
| **R-EFF-2** | effectiveness | `有效性只能由 R5.1 判定` | 净值 / 回撤 / 收益÷回撤 vs 双基准臂 / 纪律合规率 | digest 只提供 pnl_attributable 与版本分段依据，**不自行判定有效性** |

## 四、⭐ 哈希的敏感性边界（本契约最关键的裁定）

`replay_hash` 对决策内容取 canonical sha256。**三分法**：

| 类别 | 字段 | 进哈希？ | 理由 |
|---|---|---|---|
| **决策内容** | `day/sym/side` · `inputs.*` · `decision.*` · `action.order_intent` | ✅ | 「决定了什么」 |
| **执行环境** | `timing.*` · `action.executed/kind/authority/fill_ref` | ❌ | 「何时、走哪条渠道执行」—— 不是决策本身 |
| **结果** | `outcome.*` | ❌ | 「赚了多少」—— 绝不能反过来定义「决策是什么」 |

**为什么 `kind`/`authority` 也要排除**（容易被误改，测试已钉住）：

它们描述「这条 digest 代表真实成交 / 审计重建 / 影子」，即**执行渠道**。
若纳入哈希，则 **R3 影子盘 → R4 实盘的同一个决策**会得到两个不同 fingerprint，
R5.0 会把这次「渠道切换」误判为**行为改动**、对每一天都触发 60 日评审 → **判据失效**。

> 身份用 `digest_id`（含当日 seq），内容比对用 `replay_hash` —— 两者职责分离。

**进哈希的字段**（12 个）：

- `day`
- `sym`
- `side`
- `inputs.candidate_snapshot_id`
- `inputs.market_snapshot_hash`
- `inputs.sop_version_id`
- `inputs.params_hash`
- `decision.rules_fired`
- `decision.discretions`
- `decision.risk_gate`
- `decision.narrative_refs`
- `action.order_intent`

**明确不进哈希的执行环境字段**（9 个）：

- `timing.signal_ts`
- `timing.decision_ts`
- `timing.recorded_at`
- `timing.freshness_sec`
- `timing.tick_executor`
- `action.executed`
- `action.kind`
- `action.authority`
- `action.fill_ref`

## 五、与既有契约的关系（不重复造轮子）

| 本契约的字段 | 沿用自 |
|---|---|
| `timing.signal_ts/decision_ts/recorded_at` + 120s 新鲜度 | R0.3 `portfolio/timing_contract.py` |
| `decision_id` 命名（`dec-tick-{day}-{sym}` / `dec-auto-{ts}-{hash}`）与登记 | R0.4 `portfolio/ledger.py` |
| `action.kind/executed/authority` | `docs/SELL_EXECUTION_CONTRACT.md §4`（防审计重建被误当成交、防双重计算） |
| `inputs.sop_version_id` / `inputs.params_hash` | R1.5 `persona/versions/<v>.toml`（frozen 组） |
| `decision.rules_fired` | R1.1 `persona/sop_v0.toml`（150 条规则 id） |
| `decision.discretions[].point_id/output` | R1.2 `persona/discretion_v0.toml`（D1–D10 + 输出枚举） |
| `decision.narrative_refs` | R1.4 `persona/memory/memory_v0.toml`（MEM-* id） |
| `decision.risk_gate` | 风控 veto（不可被裁量绕过） |

## 六、样例 digest

```json
{
 "digest_revision": "decision-digest/v1",
 "decision_id": "dec-tick-20260911-300468",
 "day": "2026-09-11",
 "sym": "300468",
 "side": "sell",
 "timing": {
  "signal_ts": "2026-09-11 09:41:08",
  "decision_ts": "2026-09-11 09:41:08",
  "recorded_at": "2026-09-11 09:41:09",
  "freshness_sec": 0.0,
  "tick_executor": true
 },
 "inputs": {
  "candidate_snapshot_id": "",
  "market_snapshot_hash": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "sop_version_id": "v0",
  "params_hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
 },
 "decision": {
  "rules_fired": [
   "GEN-HOLD-22",
   "P1-HOLD-01",
   "GEN-HOLD-03"
  ],
  "discretions": [
   {
    "point_id": "D7",
    "output": "logic_invalidated",
    "rationale": "有效跌破 20 日线（收盘破 + 次日未收回）→ 买入逻辑消失",
    "model": "deepseek-v4-flash",
    "prompt_sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
    "cli_version": "n/a"
   }
  ],
  "risk_gate": {
   "passed": true,
   "veto_reason": "",
   "checks": [
    "single_stock_pct",
    "portfolio_floor",
    "stop_px"
   ]
  },
  "narrative_refs": [
   "MEM-005",
   "MEM-002"
  ]
 },
 "action": {
  "order_intent": {
   "side": "sell",
   "qty": 1800,
   "px_limit": 23.3,
   "reason": "stop_loss(px<=stop_px) → GEN-HOLD-22",
   "plan_ref": "plan-20260911"
  },
  "executed": true,
  "kind": "fill",
  "authority": "account.fills",
  "fill_ref": "300468|2026-09-11T09:41:09|1800|23.31"
 },
 "outcome": {
  "pnl_attributable": -1930.52,
  "effectiveness_basis": "v0-seg-1（start_date=2026-09-14 之前无，留空）"
 },
 "replay_hash": "a4dfa01a43465d5234d7f54385fe4663146d0a3c33b017a67c9537359f03e9a8",
 "digest_id": "dd-2026-09-11-2-a4dfa01a"
}
```

## 七、零生产写入说明

`src/core/decision_digest.py` **尚未被任何生产脚本 import** —— 本步只定义契约并提供可测的参考实现。
接线属 **R3.1**（六段决策环引擎）与 **R4.1**（盘中决策服务）。

测试：`tests/test_decision_digest.py`（28 项，覆盖哈希敏感性边界的正反两面）。
