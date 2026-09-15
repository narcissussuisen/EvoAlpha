# EvoAlpha 迁移台账

> status: historical
> note: 记录当时口径与决策，只增不改（数字停留在当时）

## 原则

先接入、再搬迁；先验证、再清理。旧路径在兼容期继续有效，任何任务计划引用的脚本在替换前不得移动。

## 物理迁移（2026-08-31 已执行）

- 全部系统模块已移入 EvoAlpha/：yaoban-system、Vibe-Research、因子研究、选手学习资料、妖板选手方法论拆解、py_libs。
- 无关内容（分析框架、研究报告、_review_tmp、.pip_tmp、杂项碎片）已移至 C:\Users\YZP\WorkBuddy\Claw\方法论与研究文档-非EvoAlpha。
- 计划任务适配：yaoban_tasks\root.txt 已指向 EvoAlpha\yaoban-system；VibeResearchDashboardServices / VibeResearchLiveTickValidation 任务动作路径已更新；desktop 前端 pnpm 依赖已重建（robocopy 破坏符号链接）。

| 现路径 | EvoAlpha 归属 | 当前动作 |
|---|---|---|
| 选手学习资料/ | learning / knowledge input | 保留原目录，新增统一学习入口 |
| yaoban-system/ | strategy engine / paper trading | 保留原目录，作为成熟核心 |
| 因子研究/ | research / factor and model lab | 保留原目录，先通过索引接入 |
| Vibe-Research/ | data platform / observability / agent runtime | 保留原目录，接入系统总览 |
| 妖板选手方法论拆解/ | learning source archive | 保留为原始知识档案 |
| 分析框架/ | research governance | 后续归档到 docs/governance |
| 研究报告/ | research outputs archive | 后续按来源归档到 outputs/archive |

## 暂不搬迁

虚拟环境、.local、raw/cache、SQLite/Parquet 数据库、大量历史日志和已注册任务依赖的脚本先不物理移动。

## 后续

1. 增加 EvoAlpha 统一 CLI。
2. 接入角色输入输出和决策记录。
3. 迁移有效文档，归档历史产物。
4. 更新任务计划和路径引用。
5. 新旧入口并行验证后清理重复旧入口。
