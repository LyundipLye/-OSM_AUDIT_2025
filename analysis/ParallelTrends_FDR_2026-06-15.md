# 平行趋势检验 + 多重比较 FDR 控制

**日期**：2026-06-15
**脚本**：`analysis/ParallelTrends_FDR_2026-06-15.py`（所有 p 值由脚本在归档 CSV 上实跑，非转写）
**图**：`visualisations/ParallelTrends_eventstudy_2026-06-15.png`
**方法约定**：delta = Impact − Control；split = 2021-06-01；HAC 带宽 maxlags = ceil(n^(1/3))（Andrews 1991），与脚本 05/07/07b/11 一致。
**ROI→文件映射**（命名与角色相反，见 README）：NDVI=ee-chart_ndvi.csv；LST 全多边形=ee-chart_lst_sensitivity.csv（脚本 07，主）；LST 停车核=ee-chart_lst.csv（脚本 07b，敏感）；ET=ee-chart_et.csv。

---

## 结论先行

1. **平行趋势：四条管线的 pre 期 DiD 斜率全部不显著（HAC p≥0.11），即四条都通过平行趋势前检验。** 最弱的是 LST 全多边形（pre 斜率 −0.129/yr，p=0.109）——未触线但是四者中最接近，按 Roth (2022) 低功效告诫应标注为"通过但留观"。NDVI（p=0.457）、停车核（p=0.868）、ET（p=0.161）清楚通过。ET 的 pre 斜率为负主要由 2019 干旱年凹陷驱动，与实现 1 互证。
2. **FDR：主结论在 BH 校正后仍 surviving。** 完整 14 检验族里 6 个存活；只保留"每个 ROI×窗口一个主检验（HAC OLS DiD / Seasonal MK）"的 7 检验主族里 4 个存活。**NDVI（HAC、MK）与停车核 LST（全年、暖季 HAC）在 FDR 后稳稳显著；全多边形 LST 与 ET 在 FDR 后不显著**——与备忘 §4.4 的预判一致。值得注意：全多边形的非参 MW（raw p=0.041，曾被当作"非参显著"）在 BH 校正后 q=0.073，**不再 surviving**，这是如实呈现整张矩阵带来的最重要的一处收紧。

---

## (a) 平行趋势 / pre-trend 检验

对每条管线，仅取 pre 期（<2021-06-01），跑 `delta ~ const + 时间(年)`（HAC SE）。H0：pre 斜率=0（Impact 与 Control 在干预前平行）。真实输出：

```
NDVI (core)            n_pre=179 span=3.4yr | slope=-0.0204/yr | HAC p=0.4573 (n.s.) | 95% CI [-0.0742,+0.0334] -> PASS
LST full polygon (07)  n_pre=152 span=6.3yr | slope=-0.1289/yr | HAC p=0.1094 (n.s.) | 95% CI [-0.2867,+0.0289] -> PASS
LST parking core (07b) n_pre=140 span=6.3yr | slope=-0.0148/yr | HAC p=0.8680 (n.s.) | 95% CI [-0.1892,+0.1596] -> PASS
ET (11)                n_pre=295 span=6.4yr | slope=-0.0694/yr | HAC p=0.1609 (n.s.) | 95% CI [-0.1665,+0.0276] -> PASS
```

| 指标 | pre 斜率 (/yr) | HAC p | 判定 | 备注 |
|:--|:--|:--|:--|:--|
| NDVI（核） | −0.0204 | 0.4573 | **通过** | 平坦，平行假设干净成立 |
| LST 全多边形 | −0.1289 | 0.1094 | **通过（留观）** | 四者中最弱；存在未达显著的轻微负 pre-trend；按 Roth (2022) 低功效 pre-test 不能完全免责，结合该 ROI 本就边际显著，应标注 |
| LST 停车核 | −0.0148 | 0.8680 | **通过** | 最干净 |
| ET | −0.0694 | 0.1609 | **通过** | 负斜率主要来自 2019 凹陷；event-study 图能看到 2019 那一期的负尖峰（与实现 1 互证） |

event-study 年度分解图（`visualisations/ParallelTrends_eventstudy_2026-06-15.png`）：四面板各画各年 ΔX 均值±95%CI、pre-trend 拟合线与 2021 分割线。NDVI post 期断崖式下落、停车核 post 期抬升、ET 在 2019 出现孤立负尖峰随后 post 期持续微负——可视化地支持平行趋势检验的数值结论。

**诚实边界**：pre-trend 检验本身功效有限（Roth 2022），"未检出趋势偏离"不等于"一定平行"。全多边形的 −0.13/yr 虽 n.s. 但非零，宜作为该 ROI 仅边际显著的额外理由，而非用平行趋势"洗白"它。

## (b) 完整 p 值矩阵 + Benjamini-Hochberg FDR（α=0.05）

下表为工程报告过的全部显著性检验，p 值由脚本实跑（与 README/脚本 05/07/07b/07c/11 输出一致）。BH-q(all) 是对全部 14 个检验做 BH 校正后的 q 值；surv(all) 标记 FDR 后是否仍显著。

| metric | ROI | window | test | p | BH-q(all) | surv |
|:--|:--|:--|:--|--:|--:|:--:|
| NDVI | core | full | HAC OLS DiD | 2.91e-40 | 4.08e-39 | **YES** |
| NDVI | core | full | Seasonal Mann-Kendall | 3.78e-08 | 2.65e-07 | **YES** |
| LST | full polygon | full-year | HAC OLS DiD | 6.05e-02 | 9.12e-02 | no |
| LST | full polygon | full-year | Mann-Whitney U | 4.10e-02 | 7.33e-02 | no |
| LST | full polygon | summer JJA | HAC OLS DiD | 6.70e-02 | 9.12e-02 | no |
| LST | full polygon | summer JJA | Mann-Whitney U | 4.19e-02 | 7.33e-02 | no |
| LST | full polygon | annual JJA composite | Welch t | 1.87e-01 | 2.18e-01 | no |
| LST | parking core | full-year | HAC OLS DiD | 3.37e-03 | 7.86e-03 | **YES** |
| LST | parking core | full-year | Mann-Whitney U | 1.20e-04 | 4.20e-04 | **YES** |
| LST | parking core | warm Apr-Sep | HAC OLS DiD | 1.82e-03 | 5.10e-03 | **YES** |
| LST | parking core | warm Apr-Sep | Mann-Whitney U | 6.19e-05 | 2.89e-04 | **YES** |
| LST | parking core | annual JJA composite | Welch t | 7.16e-02 | 9.12e-02 | no |
| ET | 500m | full | HAC OLS DiD | 4.45e-01 | 4.79e-01 | no |
| ET | 500m | full | Mann-Whitney U | 5.69e-01 | 5.69e-01 | no |

**完整族：14 个里 6 个 FDR 后存活。**

### 主检验族（去掉同一效应上的 MW/Welch 伴随检验）

把 HAC OLS DiD 和 NDVI 的 Seasonal MK 作为每个 ROI×窗口唯一的主检验（避免对同一假设重复计数膨胀检验族），再做一次 BH：

```
metric ROI           window                p          BH-q(prim)  surv
NDVI  core          full           2.91e-40    2.04e-39   YES
NDVI  core          full(MK)       3.78e-08    1.32e-07   YES
LST   full polygon  full-year      6.05e-02    7.81e-02    no
LST   full polygon  summer JJA     6.70e-02    7.81e-02    no
LST   parking core  full-year      3.37e-03    5.90e-03   YES
LST   parking core  warm Apr-Sep   1.82e-03    4.25e-03   YES
ET    500m          full           4.45e-01    4.45e-01    no
```

**主族：7 个里 4 个 FDR 后存活**（NDVI HAC、NDVI MK、停车核全年、停车核暖季）。

### 解读

- **NDVI**：p=2.9e-40 / MK p=3.8e-8，FDR 后 q 仍 ≪0.001。最强结论，校正不影响。
- **停车核 LST**：全年 HAC p=0.0034、暖季 HAC p=0.0018，FDR 后 q=0.0079 / 0.0051，稳稳存活。这是"局地人为热信号"主张的统计承重柱，FDR 后依然成立。
- **全多边形 LST**：HAC p≈0.06（全年/夏季）本就边际；其非参 MW raw p≈0.041 单看显著，但 **BH 后 q≈0.073，不再显著**。这正面坐实 README 已有的收紧表述——全多边形只是"power 上限下的保守存在性证据",不承担"超过区域基线/独立显著"的举证责任。
- **ET**：baseline HAC p=0.45 / MW p=0.57，FDR 后自然不显著。实现 1 的 spec(c) 把 ET 推到 raw p=0.049（剔除 2019），但即使把它并入任一多检验族，0.049 也几乎必然被 BH 拉到 0.05 以上——故 ET 在多重比较框架下仍不能算显著，与实现 1 的"边际、条件依赖"判断一致。[此为基于矩阵的推断，未把 spec(c) 正式并入上表]

**反 p-hacking 意义**：如实列出全部 14 个检验（含不显著的全多边形与 ET）、并报告哪些撑过 FDR，本身就是对 R4 型"选择性报告"指控最直接的反驳——主结论（NDVI、停车核）不是从一堆检验里挑出来的幸存者,而是在 BH 校正后依然显著的少数。
