# parameters.toml 消费者地图（唯一真相源治理）

> status: active
> verified_at: 2026-09-15

> 生成工具：`yaoban-system/tools/param_consumer_map.py`（**可重跑**，输出 `yaoban-system/persona/_param_consumer_map.report.txt`）
> 首次生成：2026-09-13 ｜ 背景：R5.0「所有阶段都需要唯一真相源」治理

## 一、为什么要这张图

系统里同一个「止盈」有**三处不同的值**：

| 位置 | 值 | 谁在读 |
|---|---|---|
| `parameters.toml [sell.intraday]` | `profit_take_pct=10.0` / `frac=1/3` | **生产** `src/core/sell.py:76` |
| `BacktestConfig`（代码硬编码） | `0.15` / `0.40` | **回测** `src/core/backtest.py:45-58` |
| `parameters.toml [sell]`（顶层） | `[10, 20]` / `[0.33, 0.5]` | **无人读**（SOP 的 `eng=` 却引用它） |

⇒ 等于「一个大脑里装了三套标准」。**在口径分裂被消除之前，任何回测结论与覆盖率数字都不具备解释力**——
它们测量的对象本身是分裂的。

⚠️ **规则：任何"删参数 / 改参数 / 收敛单一源"的动作，都必须先跑本工具确认消费者，禁止凭印象删除。**

## 二、消费者地图（2026-09-13 实测）

| 段 | 键数 | 消费者 | 真实使用情况 |
|---|---|---|---|
| `[env]` | 9 | `src/core/env_score.py:22` | ✅ `ENV` 使用 12 次 |
| `[strategy]` | 4 | **旁路**：`src/config.py:35` `strategy(name)` + `rules.rule_params()` | ✅ 多脚本消费 |
| `[risk]` | 8 | `src/core/env_score.py:23` ｜ `src/core/backtest.py:24` | ⚠️ env_score 用 1 次；**backtest 的 `RISK` 是死变量** |
| `[sell]` | 10 | `src/core/sell.py:76`（**只读 `intraday`**）｜ `src/core/backtest.py:25` | ⚠️ **backtest 的 `SELL` 是死变量** |
| `[data]` | 8 | `backfill_data.py:24` · `src/data/fetchers.py:17` · `src/data/store.py:297` | ✅ 各用 4 次 |

### 三个关键结论

1. **顶层 `[sell]` 的 9 个非 `intraday` 键确实没有消费者**（`sell.py` 不读、`backtest.py` 的 `SELL` 是死变量）。
2. **回测既没读顶层、也没读 `intraday`**——它的 toml 变量是死的，用的是 `BacktestConfig` 硬编码值。
   所以三套里**只有硬编码那套在回测中真正生效**。
3. **`[strategy.*]` 走旁路而非 `section()`**：`src/config.py:35` 的 `strategy(name)` + `src/iteration/rules.py:425` 的 `rule_params()`。
   所以它**有消费者，不是孤儿**。

## 三、由地图得出的施工顺序（含依赖）

删顶层键**会让 SOP 的 `eng=` 引用解析失败**（生成器有引用校验，`GEN-HOLD-05/06/07` 正引用 `[sell].ten_oclock_rule` / `[sell].profit_take_pct`），
所以顺序**不能**是"先删"：

| 步 | 动作 | 依赖 / 风险 |
|---|---|---|
| **1** | 改 SOP 的 `eng=` → 指向 `[sell.intraday].*`（真实生效那套） | 安全、独立；改完须重跑生成器确认 `err=0` |
| **2** | 改 `BacktestConfig` → 从 `sell.DEFAULT_PARAMS` 派生（回测与生产同源） | 会让 4 个研究脚本的历史回测结果全部变化（**期望的**）；须跑 `test_backtest.py` |
| **3** | 删顶层 `[sell]` 的 9 个死键 | 会触发 **v0 frozen 漂移**（属实现基线变更，按「拆三层」不算人格变更） |
| **4** | 全量测试锁基线 + 查 10 点纪律证据定开关 | 见下 |

⚠️ **第 3 步的顺序依赖**：若"拆三层"（人格身份 / 知识修订号 / 实现版本）尚未完成，删键会再次制造
「这是不是人格变更」的争议。**建议先完成拆三层，再执行删除。**

## 四、待决事项

| # | 事项 | 状态 |
|---|---|---|
| 1 | **「10 点纪律」开关矛盾**：SOP `ten_oclock_rule=True` vs 生产 `intraday.ten_oclock=False` | **查选手证据再定**（不由代码或文档单方面获胜） |
| 2 | `[sell].ma60_break_action`（"无条件撤退"）在 `[sell.intraday]` 中**无对应键** ⇒ MA60 规则**无生产实现** | 改 `eng=` 时须**如实留空**并注明，不得指向死键 |
| 3 | `[strategy.*]` 的子键消费者需结合 `rule_params()` 人工确认 | 待补 |

## 五、局限（如实标注）

- 本工具是**静态分析**，抓不到动态取键（如 `section(s)[k]`）、`importlib` 或字符串拼接式读取；
- 「定义后未使用」只统计了模块内引用，跨模块以模块变量形式导出后再使用的情况需人工复核。
