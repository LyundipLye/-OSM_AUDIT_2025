# Wild-cluster bootstrap —— 实测结果

**脚本**：`analysis/WildBootstrap_2026-06-15.py`
**日期**：2026-06-15 ｜ 全部数字实跑，seed=20260615 可复现，无编造。
**方法**：对小样本年度合成（~3–6 pre vs ~5 post）的 DiD 用 **restricted wild bootstrap-t（WCR）**：Rademacher(±1) 权重、B=9999、HC1 SE、有限样本校正 p=(count+1)/(B+1)（MacKinnon 2015；Cameron-Gelbach-Miller 2008；MacKinnon-Webb 2017）。年度合成 = 窗口内逐年均值 → 每年一个观测，年聚合已消除年内自相关，故观测级 wild bootstrap 即 wild-cluster bootstrap。split year=2021，`delta=Impact−Control`。同时报朴素 Welch t 作对照。

## 结论先行（实测）

| 指标 | 窗口 | n pre/post | β | t_obs | Welch p | **wild p** | 判定 |
|:--|:--|:--|:--|:--|:--|:--|:--|
| **NDVI 核** | full-year | 3/6 | −0.385 | −19.2 | 0.000 | **0.0040** | `**` |
| 停车核 LST | summer JJA | 6/5 | +2.031 | +2.17 | 0.072 | **0.0701** | n.s. |
| **停车核 LST** | warm Apr–Sep | 6/5 | +1.685 | +2.87 | 0.024 | **0.0316** | `*` |
| LST 全多边形 | summer JJA | 6/5 | +1.275 | +1.50 | 0.187 | 0.1720 | n.s. |
| ET 500m | summer JJA | 6/5 | −0.087 | −0.29 | 0.779 | 0.7811 | n.s. |
| ET 500m | warm Apr–Sep | 6/5 | −0.422 | −1.93 | 0.098 | 0.0919 | n.s. |

## 读法

- **NDVI 核**：即便在最保守的 wild bootstrap 下仍 **p=0.0040 (**)**。注意 pre 仅 3 年（Sentinel-2 NDVI 自 2018 起），合成 p 有下限；但配合 per-overpass HAC（p=2.9e-40）与 spec-curve（100% 显著），结论极稳。[3 pre 年是真实限制，已标]
- **停车核 LST**：JJA 年度合成 **wild p=0.070，n.s.**——与 README 现述「+2.03 °C，Welch p=0.071，n.s.」**完全一致**，wild bootstrap 确认该合成确属欠功效，不是 Welch 的人为。但**更宽的 warm Apr–Sep 窗合成 wild p=0.0316 (*)，即便在 wild bootstrap 下仍显著**——这是停车核结论的新增支撑。
- **LST 全多边形 / ET**：wild p 均 n.s.，确认其欠功效/边际地位。ET warm 窗 wild p=0.092 接近但未达显著，与 spec-curve「warm 窗下 per-overpass 显著、年度合成欠功效」一致。

## 是否动摇主结论

**没有。** wild bootstrap 把所有结论拉回小样本诚实参照后：NDVI 核仍 `**`、停车核 warm 合成仍 `*`、停车核 JJA 合成如 README 所述 n.s.、ET 仍 n.s.。**~11 个年度点无法被任何 bootstrap 变出功效**——wild bootstrap 只修正参照分布，不制造 power。结论与现有头条无冲突。
