# EvoAlpha

> **最终目标（2026-09-12 用户裁定，本项目保留范围的唯一判据）**
> **EvoAlpha = 妖板选手决策过程的可执行复刻体，在一套可审计的账本上自主跑 A 股短线，用它自己的前向净值证明有效。**
>
> 命名沿革：同一项目三次命名——逐妖交易团队（2026-08-29 用户命名，10 万模拟盘团队代号）→ 妖板系统（yaoban-system，策略内核）→ EvoAlpha（2026-08-31 重构确立的进化体）。2026-09-09 起生产脚本与推送署名统一为 EvoAlpha。
>
> **重构权威文档**：`docs/EVOALPHA_V2_RESTRUCTURE_PLAN.md`（v2.0 全系统重构计划，取代蓝图 v1.0 的学习范式与晋级门禁）。
> **归档区**：同级 `../evoalpha_all/`（冗余资料外迁区，见 `../evoalpha_all/MANIFEST.md`）。

EvoAlpha 以模拟盘为实验环境，自主完成环境判断、主线选择、个股形态筛选、分时买点、持仓卖出与仓位管理，并用自身前向净值（对照市场基准臂）判定是否有效。

## 入口

- 选手学习入口：EvoAlpha/learning/README.md；原始资料保留在 选手学习资料/。
- 系统地图：EvoAlpha/docs/SYSTEM_MAP.md。
- 团队协议：EvoAlpha/agents/README.md。
- 运行手册：EvoAlpha/docs/RUNBOOK.md。
- 人类监控看板与 Agent 运行时：Vibe-Research/。

## 仓库结构（两个 git 仓库 —— 提交前先看清自己在哪个仓库里）

本目录下并存**两个独立 git 仓库**，`.gitignore` 让外层不跟踪内层（避免嵌套仓库），
因此**改动的提交目标不同**：

| 仓库 | 远端 | 管什么 | 明确不管 |
|---|---|---|---|
| **`EvoAlpha/`**（本目录） | `git@github.com:narcussuisen/EvoAlpha.git` | 文档主目录 `docs/`、`learning/`、`agents/`、`选手学习资料/` | `yaoban-system/`、`Vibe-Research/`、`py_libs/`、`data/`、`因子研究/`、`_scratch/`、`docs/dashboard/` |
| **`EvoAlpha/yaoban-system/`** | `git@github.com:narcussuisen/yaoban-system.git` | 策略内核、脚本、账本 `portfolio/ledger.json`、计划任务注册源 `scripts/register_schedule.ps1` | — |

**⭐ 两处的 `docs/` 不是同一个目录**（本项目最易搞混的一点）：

- `EvoAlpha/docs/` = **文档主目录**（规范 / 契约 / 计划 / 画像）→ 索引 `docs/_INDEX.md`；
- `EvoAlpha/yaoban-system/docs/` = **代码仓文档**（`reviews/`、`loops/`、时间线还原）→ 索引见其 `_INDEX.md`。
- 判断某条 `docs/XXX.md` 引用指向哪边：**看该工具的 `ROOT` 定义**
  （例：`build_roadmap_dashboard.py` 用 `PROJ_ROOT = REPO.parent`，即本目录）。

**归档区**：`../evoalpha_all/`（**项目外，不入 git**）。历史产物一律外迁到那里，
EvoAlpha 自身只保留"当前有效"的内容 —— 防止误读与依赖错误。索引见 `../evoalpha_all/MANIFEST.md`。

## 闭环（v2.0 决策环）

选手实盘决策标签 → 规则层（37 条规则算子）→ 裁量层（LLM 按 SOP 分级）→ 容差层（均线支撑 ≤2%、执行偏差 3 日）→ 组合层（不追单条正 alpha，以组合决策为单位）→ 盘中实时自主交易 → 单一主账本净值 → 对照市场基准臂判定 → 版本分段归因与回滚

> ⚠️ 架构级分离（必须守住）：**行为复刻 ≠ 收益来源**。9/11 已证伪「分时跌破均价线」命中选手行为 94.4% 但全市场反事实显著反向（p=0.00014）。
> 命中率只作**诊断轨**，净值才是**晋级闸门**。

## 模块归属（2026-09-12 瘦身后）

> EvoAlpha 收敛为 yao 本体：30 GB → **2.71 GB**。冗余资料外迁至同级 `evoalpha_all/`
> （`因子研究` 17.8 GB、`妖板选手方法论拆解` 2.99 GB、`选手学习资料/妖板选手视频拆解/_work` 4.6 GB、`_vr_rollback_20260911` 930 MB）。
> 搬迁为同盘改名，**不释放磁盘空间**；完整记录与恢复方法见 `../evoalpha_all/MANIFEST.md`。

- 选手学习资料：知识输入与方法论学习入口。**保留** 战法画像、全库总纲、卖点/风控总纲、60+ 逐日 record、逐日文字资料、精选证据帧（E0 级证据，人格标签库基础）。
- yaoban-system：成熟的 A 股短线策略、信号、组合模拟、交易日志和计划任务内核。它是 EvoAlpha 的执行内核，过渡期暂不改名（2026-09-09：原「逐妖交易团队」的生产代码与推送署名已统一改为 EvoAlpha，目录名保留）。
- Vibe-Research：**核心设施** —— 与妖板选手的交互观察窗口 + 选手所需数据的获取源；同时提供人类监控看板与 Agent 运行时。
- EvoAlpha 控制平面：统一入口、架构、角色协议、入口和迁移台账（`docs/`、`learning/`、`agents/`）。
- ⬛ 已外迁（不在本项目范围）：`因子研究`（本次路线为行为克隆，不使用因子挖掘）、`妖板选手方法论拆解`（已被新版 82/82 拆解取代）。

## 原则（2026-09-12 修订）

1. 模拟盘优先，所有自主投资决策先进入模拟组合；**不接真实资金**。
2. 证据优先：行情、交割、持仓、绩效必须可追溯到原件（证据等级 E0-E6）。
3. **行为复刻与收益验证分离**：命中率是诊断轨，自身前向净值（对照市场基准臂）是唯一晋级闸门。
4. **不信任未控变量的回测**：回测退为辅助工具；判据以真实前向成交流水为准。
5. 失败可见：数据缺口、过期快照、策略失效和门禁失败不得静默掩盖。

当前采用统一入口、兼容旧路径、逐步迁移的方式。详见 EvoAlpha/docs/MIGRATION.md。
