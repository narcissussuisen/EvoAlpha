# EvoAlpha 旧入口清理预案

清理仅在"新旧入口并行验证完成"后执行。当前阶段不删除任何旧入口，本文件是执行清单。

## 验证前置条件（全部满足才清理）

- [x] EvoAlpha CLI 覆盖全部 13 个命令（含 compat）且冒烟通过（2026-08-31 compat-check 退出码 0）
- [x] 旧模块路径 5/5、Vibe-Research 服务端口 3/3、旧入口 verify_env 在运行解释器下 6/6 通过（2026-08-31）
- [x] 团队决策产物在 EvoAlpha/outputs/team_decisions 正常落盘（含 .tmp 检查）
- [x] 任务引用盘点：现行任务均指向 yaoban_tasks\launch.ps1（脚本存在），旧 cmd 型任务已 Disabled（2026-08-31）
- [ ] yaoban-system 计划任务在 EvoAlpha 新入口下连续运行 1 个完整周期（跨交易日）

## 清理清单（验证后执行）

| 项目 | 动作 | 风险 |
|---|---|---|
| yaoban-system/README.md 旧定位文案 | 保留为 EvoAlpha 子模块说明 | 低 |
| 已 Disabled 的旧 cmd 型任务（YaobanDailySignal/MonthlyOptimize/LoopEngine/TickCollect/Candidates/OCR） | 已被 yaoban_tasks\launch.ps1 编排取代；确认无引用后按用户确认移除任务定义 | 低-中 |
| 根目录重复入口 README | 合并到 EvoAlpha/README.md 后移除 | 低 |
| 重复/过期的历史输出副本 | 按 MANIFEST 核对后删除归档外冗余副本 | 中 |
| EvoAlpha/docs/INTEGRATION_PLAN.md 历史阶段 | 归档到 docs/archive 后移除 | 低 |
| 不再被引用的临时脚本 | 移入 EvoAlpha/archive/legacy_scripts | 中 |

## 明确不清理

- 数据库、Parquet、.local、虚拟环境和缓存
- 任务计划注册（仅更新其工作目录指向，不删除任务）
- Vibe-Research 第三方源码与许可证
- 选手学习资料原始视频/图片（学习入口永久保留）
