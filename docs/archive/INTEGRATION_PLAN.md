# EvoAlpha 整合计划

## 第一阶段：控制平面

- [x] 总 README、系统地图、学习入口、团队角色协议、迁移台账和运行手册

## 第二阶段：统一运行入口

- [~] EvoAlpha CLI：已提供 status、learning、health、research、scan、paper-trade、review、walkforward；research/health 依赖 Vibe-Research 本地运行环境
- [ ] 统一路径和环境变量
- [~] 输出目录与运行 ID 规范：团队决策已落盘 EvoAlpha/outputs/team_decisions/，全局产物迁移待完成
- [x] CLI status/learning/help/team 冒烟验证；旧模块仍保持原路径兼容

## 第三阶段：团队决策闭环

- [x] 角色输入输出 JSON schema：agents/artifact-contract.v1.json
- [x] 多角色编排与基础风控门禁：agents/coordinator.py；CLI team
- [x] 决策记录基础字段与风险阻断记录
- [~] 团队决策持久化：原子写入 EvoAlpha/outputs/team_decisions/
- [~] 接入真实 Vibe Research Agent 角色运行：adapt_vibe_run.py / adapt_yaoban_report.py / adapt_paper_trade.py 已覆盖 researcher / strategy_researcher / trader / portfolio_manager / reviewer 五类角色 artifact，team 已接入多角色完整性门禁；真实冲突编排待接入
- [~] 模拟成交与绩效归因接入：trader artifact 订单已进入团队决策 orders；portfolio_manager artifact 含绩效事实与窗口

## 第四阶段：物理迁移与清理

- [~] 迁移有效学习和研究文档：学习笔记、战法画像、因子纪要、walk-forward 已进入 EvoAlpha/learning/library 和 research/validated；原文件保留
- [~] 归档历史输出、缓存和日志：已建立 ARCHIVE_INDEX 与 EvoAlpha/archive（含 MANIFEST + 首批研究报告归档）；大体量私有产物保持原位
- [~] 更新任务计划与路径引用：已盘点全部任务（现行 launch.ps1 编排脚本 10/10 存在；旧 cmd 任务已 Disabled；Vibe 服务脚本存在）
- [~] 新旧入口并行验证：compat_check 全绿（旧路径/新入口/服务 4 端口/CLI），验证报告 outputs/validation/VALIDATION_SUMMARY.md；计划任务完整周期验证待跨交易日
- [ ] 清理重复旧入口（预案见 docs/LEGACY_CLEANUP.md，前置条件满足后执行）
