# 规则角色分流清单（eye / brain）

> status: active
> verified_at: 2026-09-15

> 依据：2026-09-13 用户确立的架构 —— **「LLM 就是作为选手人格，机械侧是选出标的以及位置，LLM 是盘中决定买入卖出的」**
> 来源数据：`persona/sop_v0.toml`（160 条）；本清单先覆盖「决定买卖」的三段：①环境闸门 19 · ④找低吸 22 · ⑤稳持仓 45 = **86 条**
> 生成辅助脚本：`_scratch/role_split_src.py`（可重跑）

## 一、判据（怎么分）

| role | 含义 | 判断依据 |
|---|---|---|
| **eye** | **眼睛**：代码能算出的**事实 / 位置 / 数值**，无需判断 | 输出是「是否成立」或「一个数/一个位」 |
| **brain** | **大脑 = 选手人格**：需要**判断 / 取舍**的决定 | 输出是「动作」，且含**非数值的选择**（走不走、减半还是全走、算不算洗盘） |
| **na** | 认知 / 心法，**不进决策流程** | 是态度，不是判据 |

⚠️ **重要**：一条规则常常**同时含 eye 输入与 brain 输出**（如 `GEN-HOLD-05`：判「10:00 是否涨停」是 eye，判「走不走」是 brain）。
本表**按规则的输出定 role**；它需要的 eye 输入单列在「所需事实」栏 —— 这正是 prompt 该喂什么、代码该算什么。

## 二、eye 事实清单（**代码要实现的计算**，全部来自规则的实际引用）

| 组 | 事实项 |
|---|---|
| **环境（①）** | `limit_up_count` · `limit_down_count` · `max_consec_limit_up` · `count(pct_chg < -0.07)` · `amt_ma5 / amt_ma20 / shrink_days` · `eq_weight_index_ret` vs `weighted_index_ret` · `gap_open_pct` · `overnight_us_tech_up` · `index_low` / `prior_low_cluster(20)` · `rebound_days` · `box_high / box_low` · `sentiment_temp / median_chg / lianban_rate / zhaban_rate / prev_zt_perf` · **`first_board_premium`（首板次日溢价）** |
| **板块（②③）** | `sector_strength`（三层） · `sector_retreat_signal` · `sector_leader_broken` · `mainline_rank` |
| **个股位置** | `MA5 / MA10 / MA20 / MA60` · `close vs MA_n` · `bias5 = (close-MA5)/MA5` · `KDJ(9,3,3)` · `support / resist_band` · `prior_high`（前高） · `pattern_bar_high / pattern_bar_low` |
| **分时** | `vwap` · `px_above_vwap` · `pullback_hold_vwap` · `fall_from_peak` · `fall_from_limit` · `no_new_high_in(30min)` · `intraday_high_pct` · `intraday_ramp_pct` · `vol_expand / vol_shrink / vol_prior_rise` · `up_down_vol_ratio` |
| **持仓/账务** | `holding_days` · `entry_ts - candidate_ts` · `entry_px` · `structure_broken(MA, vol)` · `arm / trail`（冲高回落） |

⇒ **这张表就是「代码该写什么」的完整清单**（约 45 项）。用户已确认 LLM 延迟可接受，因此 eye 只需**算准**，不必追求秒级。

## 三、逐条分流（86 条）

| id | role | 所需 eye 事实 |
|---|---|---|
| GEN-GATE-01 | eye | limit_up_count |
| GEN-GATE-02 | eye | limit_up_count / limit_down_count / up_count |
| GEN-GATE-03 | eye | max_consec_limit_up |
| GEN-GATE-04 | eye | amt_ma5 / amt_ma20 / shrink_days |
| GEN-GATE-05 | eye | eq_weight_index_ret / weighted_index_ret |
| GEN-GATE-06 | **brain** | gap_open_pct / overnight_us_tech_up |
| GEN-GATE-07 | eye | vol_expand / high_tech_down / eq_weight_stable |
| GEN-GATE-08 | eye | bz50_excess_ret_pulse / mainline_high_no_new_high |
| GEN-GATE-09 | eye | index_low / prior_low_cluster(20) |
| GEN-GATE-10 | **brain** | regime / support 状态 |
| GEN-GATE-11 | **brain** | rebound_days |
| GEN-GATE-12 | **brain** | box_high / box_low / px |
| GEN-GATE-13 | **brain** | 8 个见顶信号计数 |
| GEN-GATE-14 | eye | turnover_pct / 封板状态 / 梯队状态 |
| GEN-GATE-15 | eye | sentiment_temp 等 7 项 |
| GEN-GATE-16 | **brain** | break_key_level / vol_expand |
| GEN-GATE-17 | eye | limit_down_count / count(pct_chg<-0.07) |
| GEN-GATE-18 | **brain** | first_board_premium |
| GEN-GATE-19 | eye | 外盘 / 竞价 / 前日收盘（三级数据获取顺序） |
| GEN-ENTRY-01 | eye | pct_change_today |
| GEN-ENTRY-02 | eye | px / vwap / vol_expand |
| GEN-ENTRY-03 | eye | px_above_vwap / 量能结构 |
| GEN-ENTRY-04 | eye | px vs vwap |
| GEN-ENTRY-05 | eye | entry_bar_index / pattern_bar_index |
| GEN-ENTRY-06 | **brain** | D6 五项特征 |
| GEN-ENTRY-07 | eye | 四类过滤器定义 |
| GEN-ENTRY-08 | eye | 时点表 |
| GEN-ENTRY-09 | eye | entry_ts - candidate_ts |
| GEN-ENTRY-10 | **brain** | 持仓 vs 未建仓 状态 |
| GEN-ENTRY-11 | eye | intraday_ramp_pct |
| GEN-ENTRY-12 | **brain** | 低开幅度 / 量能 / 午后走势 |
| GEN-ENTRY-13 | **brain** | 板块强弱对比 |
| GEN-ENTRY-14 | eye | hm（11:00）+ pullback_hold_vwap |
| GEN-ENTRY-15 | **brain** | 四类支撑压力位识别 |
| GEN-ENTRY-16 | **brain** | 止跌/滞涨信号形态 |
| P1-ENTRY-01 | eye | close vs pullback_swing_high / vol |
| P1-ENTRY-02 | eye | min(low) vs MA_n / stabilize_bar |
| P1-ENTRY-03 | **brain** | 大盘/板块/个股综合 |
| P2-ENTRY-01 | eye | low_today vs low_yesterday / px vs vwap |
| P3-ENTRY-01 | eye | bar_offset / C vs pattern_bar_high / vol |
| P3-ENTRY-02 | **brain** | 拉升角度 / 回落形态 / 尾盘勾头 |
| GEN-HOLD-01 | **brain** | close vs MA5 / MA10 / 情绪强弱 |
| GEN-HOLD-02 | eye | close vs MA_n / next_close |
| GEN-HOLD-03 | eye | close vs MA_n / next_close |
| GEN-HOLD-04 | eye | MA5 / MA10 |
| GEN-HOLD-05 | **brain** | hm / limit_up 状态 / px vs vwap |
| GEN-HOLD-06 | **brain** | 次日是否涨停 / 开盘半小时封板状态 |
| GEN-HOLD-07 | **brain** | gain（浮盈） |
| GEN-HOLD-08 | **brain** | touched_limit_up / fall_from_limit |
| GEN-HOLD-09 | **brain** | fall_from_peak / no_new_high_in(30min) |
| GEN-HOLD-10 | **brain** | new_high / vol vs vol_prior_rise |
| GEN-HOLD-11 | **brain** | downtrend / rebound / vol_shrink |
| GEN-HOLD-12 | **brain** | 买入逻辑 id（来自 provenance） |
| GEN-HOLD-13 | **brain** | 买入逻辑 id + 结构是否仍成立 |
| GEN-HOLD-14 | **brain** | open vs prev_close / early_fade / up_without_volume |
| GEN-HOLD-15 | **brain** | intraday_high_pct / 封板状态 |
| GEN-HOLD-16 | eye | holding_days |
| GEN-HOLD-17 | **brain** | 资金调度意图（跨标的） |
| GEN-HOLD-18 | **brain** | 阻力位 vs px |
| GEN-HOLD-19 | **brain** | 支撑位状态 |
| GEN-HOLD-20 | **brain** | sector_leader_broken |
| GEN-HOLD-21 | **brain** | regime |
| GEN-HOLD-22 | **brain** | structure_broken(MA, vol) |
| GEN-HOLD-23 | **brain** | 结构破坏程度 |
| GEN-HOLD-24 | **brain** | gap_up / fade |
| GEN-HOLD-25 | **na** | — |
| GEN-HOLD-26 | **brain** | bias5（阈值待标定） |
| GEN-HOLD-27 | eye | KDJ(9,3,3) |
| GEN-HOLD-28 | eye | close / entry_px / 低开幅度 |
| GEN-HOLD-29 | **brain** | 封单变化（盘口语义） |
| GEN-HOLD-30 | **brain** | sector_retreat_signal |
| GEN-HOLD-31 | **brain** | 指数阻力位 / 做T可行性 |
| GEN-HOLD-32 | eye | arm / trail / peak |
| GEN-HOLD-33 | **brain** | 龙头/跟风炸板状态 |
| GEN-HOLD-34 | **na** | — |
| GEN-HOLD-35 | **brain** | 减仓后时间 / MA10 位置 |
| GEN-HOLD-36 | **brain** | 价格台阶 / 时间台阶 |
| GEN-HOLD-37 | **brain** | prior_high 距离 / 大阴线+爆量 |
| GEN-HOLD-38 | **brain** | prior_high 冲击是否被证伪 |
| GEN-HOLD-39 | eye | 六条均线定义 |
| GEN-HOLD-40 | **brain** | close vs MA10 / MA20 |
| P1-HOLD-01 | eye | close vs MA20 / below_MA10 days |
| P1-HOLD-02 | **brain** | support_hold / support_broken |
| P1-HOLD-03 | **brain** | 历史支撑位复用 |

## 四、统计

| role | 条数 | 占比 |
|---|---|---|
| **eye**（代码算） | 30 | 34.9% |
| **brain**（LLM 判） | 54 | 62.8% |
| **na** | 2 | 2.3% |

⇒ **brain 占近三分之二** —— 这从数据上印证了用户判断：**SOP 的主体是"判断"，不是"数值"**。
⇒ 也说明此前「把 46 条 `mech=full` 当欠账去机械化」的方向**部分偏了**：其中相当一部分本质是 brain。

## 五、实施顺序

1. **先补 eye 事实层**（本清单 §二）—— brain 的判断质量取决于喂进去的事实是否齐全准确；
2. **再接 brain**：先 `GEN-HOLD-05/06`（10 点纪律 + 减半/全走，两段式决策 = 最佳验证样本）；
3. 然后按段铺开（HOLD → ENTRY → GATE）；
4. **最后做一次真实闭环模拟**（用户指定的下一步目标）。

⚠️ 本清单的 role 归属含**判断成分**，可逐条复议；争议项建议以「这条的输出是不是一个可算的事实」为准绳。
