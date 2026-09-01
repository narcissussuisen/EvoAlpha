# EvoAlpha 并行验证报告（2026-08-31）

> 由 EvoAlpha/agents/compat_check.py 与旧入口冒烟测试生成；机器报告见 outputs/validation/compat-check-2026-08-31.json。

## 1. 兼容性检查（compat_check）

| 检查项 | 结果 |
|---|---|
| 旧模块路径（yaoban-system / 因子研究 / Vibe-Research / 选手学习资料 / 妖板选手方法论拆解） | 5/5 存在 |
| EvoAlpha 控制平面入口（README / cli / docs / agents / learning / research / trading / evolution） | 15/15 存在 |
| 本地服务端口（8766 API / 5930 UI / 8765 应急看板 / 3080 DSH Web） | 4/4 监听 |
| CLI 子命令装配（12 个命令在 --help 可见） | 通过 |
| 退出码 | 0 |

## 2. 旧入口冒烟

- yaoban-system verify_env.py 在运行解释器（.workbuddy python 3.13.14 + ..\py_libs）下：6/6 全部通过，退出码 0。
- 注意：系统 Python 3.14 缺少 numpy/akshare，旧入口须按 README 使用指定解释器与 PYTHONPATH —— 这是既有运行约定，不是本次重构引入的回归。

## 3. 新入口管道验证

- team 多角色装配：五类角色 artifact 全 complete → paper_execute（含订单）；混入 incomplete researcher → blocked（订单清空）。
- adapt-run / adapt-report / adapt-paper：真实 Vibe 运行与 yaoban 报告均可转 artifact，状态与证据引用保留。
- 决策落盘：outputs/team_decisions/ 原子写入，无 .tmp 残留。

## 4. 计划任务与路径引用盘点（2026-08-31）

- 现行任务（Ready/Running）均通过 C:\Users\YZP\WorkBuddy\yaoban_tasks\launch.ps1 -Mode <premarket|scan|monitor|tick|close|notify|acceptance|rebuild|next-plan|plan-gate|infra> 编排，引用脚本 10/10 存在。
- VibeResearchDashboardServices / VibeResearchLiveTickValidation 引用 Vibe-Research/scripts/*.ps1，均存在。
- 旧 cmd 型任务（YaobanDailySignal / YaobanMonthlyOptimize / YaobanLoopEngine / YaobanTickCollect / YaobanDailyCandidates / YaobanOCR）已全部 Disabled，已被 launch.ps1 编排取代 —— 无需为它们执行破坏性清理。
- tpoint_loop_engine 引用 Claw\tpoint 工作区（独立遗留系统），本次不涉及。

## 5. 生产闭环当日证据（2026-08-31）

- 当日任务日志完整：infra(08:45) → premarket(08:50, exit_code=0) → plan-gate(08:55) → auction/notify(09:15+) 全部落盘 task_logs/2026-08-31/。
- 盘中实况 pos_live.json 存在；Vibe 服务端口与 DSH Web 监听正常。

## 6. 仍待验证（跨交易日）

- YaobanDailySignal / YaobanMonthlyOptimize / 盘中守护任务在新入口下完整周期运行。
- 旧入口清理需在本报告全部前置条件满足后执行（见 docs/LEGACY_CLEANUP.md）。
