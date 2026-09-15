# EvoAlpha 文档索引（项目根 docs/）

> status: active
> verified_at: 2026-09-15
> 本文件是 `EvoAlpha/docs/` 的**唯一权威索引**。新增文档必须先在此登记。

---

## 0. 两个 docs 目录的分工（**先看这一段，能省一半找文件的时间**）

项目里有**两个** `docs/`，此前没有文档说明这一点，是"资料很多但很杂乱"的最大来源：

| 位置 | 定位 | 内容 |
|---|---|---|
| **`EvoAlpha/docs/`**（本目录，项目根） | ⭐ **文档主目录** —— 日常查阅的就是这里 | 规范 / 契约 / 计划 / 画像 / 历史归档 / 看板数据（30 个 md + 1 html + `dashboard/` + `source_material/` + `archive/`） |
| `EvoAlpha/yaoban-system/docs/`（代码仓内） | **代码仓文档** | 时间线还原、评审记录（`reviews/`）、循环工程（`loops/`）、以及 2026-09-15 新建的 `archive/` 与 `_INDEX.md` |

代码里的 `docs/XXX.md` 引用**多数指向本目录**（如 `src/decision_chain/*.py` 引 `EVOALPHA_V2_RESTRUCTURE_PLAN.md`）；
少数指向仓内（如 `src/core/pattern_pool.py` 引 `TRADER_ROADMAP_v2.md`）。**判断方式：看该工具的 `ROOT` 定义**
（`build_roadmap_dashboard.py` 用 `PROJ_ROOT = REPO.parent`，即本目录）。

⚠️ **本目录不在 git 仓库内**（仓库是 `yaoban-system/`）⇒ 这里的文件**没有版本保护**，改动前必须手工备份。

---

## 1. 三态标签约定

```markdown
> status: active | historical | superseded
> verified_at: YYYY-MM-DD        # 仅 active：最后一次确认与代码/账本一致
> superseded_by: <路径或说明>     # 仅 superseded
```

**判据：读者拿它做决策会不会做错？会 ⇒ 不是 active。** 历史文档只增不改。

---

## 2. 当前生效（active · 20 篇）

### 2.1 运行权威（与生产强耦合，改动需评估影响面）

| 文档 | 用途 |
|---|---|
| `DAY_TIMELINE.md` | ⭐ **交易日时间链权威表述**（机器权威 = `yaoban-system/scripts/register_schedule.ps1:: $Schedule`） |
| `DAY_TIMELINE_AND_PUSH.html` | 时间链 × 飞书推送映射（含 9/14 实测推送清单） |
| `HUMAN_MACHINE_INTERFACE.md` | 人机交互协议（三层边界 / 触发词 / 资料格式） |
| `RUNBOOK.md` | 运维手册 |
| `SYSTEM_MAP.md` | 系统地图 |
| `ROADMAP_STATUS.md` | 路线图当前状态 |
| `ARCHIVE_INDEX.md` | 历史产物外迁记录（2026-09-12 大清理，判据 = 是否服务于 EvoAlpha 定位） |

### 2.2 架构 / 规格 / 契约

| 文档 | 用途 |
|---|---|
| `EVOALPHA_V2_RESTRUCTURE_PLAN.md` | ⭐ v2 重构总计划（被 `decision_chain/*` 大量引用为「权威」） |
| `RULE_ROLE_SPLIT.md` | 规则角色分流表（eye=事实 / brain=判断，86 条） |
| `DECISION_DIGEST_CONTRACT.md` | 决策 digest 契约（由 `tools/build_decision_digest_schema.py` 生成） |
| `PARAM_CONSUMER_MAP.md` | 参数消费图 |
| `EVOALPHA_VISION_ALIGNMENT.md` | 愿景对齐 |
| `LLM_COST_AND_LATENCY.md` | LLM 成本与时延口径 |

### 2.3 当前计划 / 切片

| 文档 | 用途 |
|---|---|
| `SELECTION_LAYER_GO_LIVE_20260915.md` | 选股层上线（Layer A/B/C，召回 32/32） |
| `PATTERN_QUEUE_SAMPLE_PLAN_20260915.md` | 形态队列采样计划 |
| `PLAN_AUCTION_EMOTION_WIRING_20260915.md` | 竞价情绪接线方案 |
| `R4_MINIMAL_VETO_SLICE.md` | R4 盘中否决最小切片 |
| `PLAYER_MATERIAL_AUDIT.md` | 选手资料审计 |

### 2.4 画像产物（由 `tools/build_persona_*.py` 生成，**改内容要改生成器**）

`PERSONA_SOP_v0.md`（规则二维表）· `PERSONA_MEMORY_v0.md` · `PERSONA_DISCRETION_v0.md` · `PERSONA_VERSIONING_v0.md`

---

## 3. 历史（historical · 9 篇，只增不改）

`P0_CHANGELOG.md`（P0 基线变更日志，60KB）· `ITERATION_2026-09-11.md` · `V4_MATERIALS_DIGEST.md` ·
`R2_DATA_LAYER.md` · `AUTOMATION_RESULT_VERIFY_20260914.md` · `DECISIONS_PENDING_20260914.md` ·
`YAOBAN_AGENT_BASELINE_AND_PHASE1_BLUEPRINT.md`（改名前的阶段蓝图）

已移入 `archive/`：`DASHBOARD.md` · `INTEGRATION_PLAN.md` · `LEGACY_CLEANUP.md`
（三者经全仓扫描确认**零引用**；备份在 `_scratch/projdocs_backup_20260915_113655/`）

## 4. 已取代（superseded · 1 篇）

`ROADMAP.md` → 现行状态看 `ROADMAP_STATUS.md`，v5 路线图见 `yaoban-system/docs/ROADMAP_v5*.md`。

---

## 5. 运行时数据（**当数据看，别当文档改**）

| 路径 | 性质 | 消费方 |
|---|---|---|
| `dashboard/status.json` | ⭐ **看板 / roadmap 的单一真相源** | `tools/build_roadmap_dashboard.py`、`tools/roadmap_server.py` |
| `dashboard/roadmap.html` | 自包含产物（数据内嵌） | 浏览器 / roadmap 服务 |
| `dashboard/status.json.bak_midday_20260914` | 9/14 午盘备份 | — |
| `dashboard/test_baseline.json` | 测试基线 | — |
| `source_material/session-*.jsonl` | 会话原始素材（7.1 MB） | 追溯用 |

⚠️ 改 `status.json` 前先备份；它是看板的输入，不是普通文档。

---

## 6. SSOT 登记（唯一真相源，他处只引用、禁复制数值）

| 事实 | 唯一来源 |
|---|---|
| 本金 | `yaoban-system/portfolio/ledger.json::start_cash` |
| 风控阈值 | `yaoban-system/portfolio/ledger.json::policy` |
| 交易时间链（机器权威） | `yaoban-system/scripts/register_schedule.ps1:: $Schedule` |
| 看板叙事状态 | 本目录 `dashboard/status.json` |
| 非交易日判定 | `yaoban-system/scripts/trading_calendar.py` |
| 飞书 webhook | `C:\Users\YZP\WorkBuddy\yaoban_tasks\feishu_webhook.txt` |

---

## 7. 放置规则

1. **面向当下操作**（规范 / 契约 / 手册 / 计划）→ 本目录顶层，`status: active` + `verified_at`。
2. **带日期的产物**（单日复盘 / 单次扫描 / 阶段报告）→ 顶层标 `historical`，或移入 `archive/`。
3. **被代码读写** → 保留原路径（移动会断引用），并在 §5 登记。
4. **看板数据** → `dashboard/`，不进顶层。
5. 新增 `active` 文档**必须**同时登记到本索引 §2。
