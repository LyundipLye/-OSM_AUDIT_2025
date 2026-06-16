# ET BACI/DiD：2019 干旱年敏感性分析

**日期**：2026-06-15
**数据**：`data/raw_telemetry/ee-chart_et.csv`（NASA MODIS MOD16A2GF，8-day，2015-01 至 2025-12，n=506 有效观测）
**脚本**：`analysis/ET_2019_sensitivity_2026-06-15.py`（复用脚本 11 的 mean-shift OLS + Newey-West HAC 方法；split=2021-06-01；HAC 带宽 maxlags=ceil(n^(1/3))=8；delta = Sprawl_ET − Control_ET）
**图**：`visualisations/ET_2019_sensitivity_2026-06-15.png`

---

## 结论先行

控制或剔除 2019 干旱年后，ET 的 DiD 点估计从 baseline 的 **−0.081（n.s.）翻倍到 −0.205，HAC p≈0.049（边际显著 \*）**。但这个"翻回显著"**有三个不能省略的限定**：

1. **它依赖剔除/控制一个气候异常年（2019 英格兰东南干旱）。** 这是设计选择，不是数据修正；必须在正文里写明，否则等于换一种 p-hacking。
2. **它只到边际显著，且对 HAC 带宽敏感。** maxlags 从 4 到 16，HAC p 在 0.050↔0.025 之间滑动；在预登记带宽 maxlags=8 上正好 p=0.0491，差一点就过不了 0.05。
3. **非参 Mann-Whitney 不支持。** 剔除 2019 后 pre vs post 的 MW p=0.197，仍 n.s.。参数模型翻回显著、非参没有，说明信号主要来自均值，分布层面不稳。

因此 **ET 不应被重新当作 well-powered 支柱**。诚实表述为：ET 方向为负、量级小；剔除 2019 干旱年后参数 DiD 达边际显著，但该显著性条件依赖于异常年处理、对带宽敏感、且未被非参检验证实。post 期 2021–2025 逐年皆负这一事实，比 p 值本身更能支撑"建设后存在 ET 抑制"的定性主张。

---

## 三个 spec 的真实脚本输出

直接粘贴 `python3 analysis/ET_2019_sensitivity_2026-06-15.py` 的 stdout：

```
=== ET 2019 drought sensitivity | split=2021-06-01 | delta=Impact-Control ===
Total valid 8-day obs n=506 | 2019 obs=46 (all in pre)

(a) baseline  delta ~ const + Post
    Post beta = -0.0815 mm/8-day | HAC p=0.4448 (n.s.) | 95% CI [-0.290,+0.127] | MW p=0.5688 | n=506 (pre 295/post 211)

(b) control   delta ~ const + Post + Drought2019
    Post beta = -0.2054 mm/8-day | HAC p=0.0491 (*) | 95% CI [-0.410,-0.001] | MW p=0.1967 (pre(excl 2019) vs post(all)) | n=506
    Drought2019 beta = -0.7948 | HAC p=0.0000 (***)

(c) drop 2019 delta ~ const + Post  (calendar 2019 removed)
    Post beta = -0.2054 mm/8-day | HAC p=0.0491 (*) | 95% CI [-0.410,-0.001] | MW p=0.1967 | n=460 (pre 249/post 211)
```

### 逐 spec 解读

| spec | DiD Post 点估计 | HAC p | MW p | n | 判定 |
|:--|:--|:--|:--|:--|:--|
| (a) baseline | −0.0815 | 0.4448 | 0.5688 | 506 (295/211) | n.s. |
| (b) +Drought2019 协变量 | **−0.2054** | **0.0491 \*** | 0.1967 | 506 | 边际显著（参数），非参不支持 |
| (c) 剔除 2019 整年 | **−0.2054** | **0.0491 \*** | 0.1967 | 460 (249/211) | 边际显著（参数），非参不支持 |

**为什么 (b) 与 (c) 给出完全相同的 Post 系数（−0.2054）？** 因为 `Drought2019` 哑变量与"日历 2019"完全共线，且 2019 的 46 个观测全部落在 pre 期。由 Frisch-Waugh-Lovell 定理，在回归里用哑变量吸收 2019 与把 2019 整段剔除，对 Post 系数的估计是代数等价的。两条路径互为印证，不是巧合。

**2019 本身的量级。** spec (b) 里 `Drought2019` 系数 = −0.7948，HAC p<1e-4（\*\*\*），与脚本 11 年度分解的 2019 ΔET=−0.80 吻合。这坐实了备忘 §1 的机制判断：baseline 的 n.s. 很大程度上是单一干旱年被分到 pre 基线一侧、把 pre 均值从约 −0.05 拉到 −0.13，从而压缩了 regime shift 的量。

## HAC 带宽稳健性（诚实标注边际性）

`spec(c)` 的 Post=−0.2054 在不同 HAC 带宽下的 p（真实输出）：

```
maxlags= 4 -> HAC p=0.0504
maxlags= 6 -> HAC p=0.0550
maxlags= 8 -> HAC p=0.0491   <- 预登记带宽 ceil(460^(1/3))
maxlags=10 -> HAC p=0.0411
maxlags=12 -> HAC p=0.0344
maxlags=16 -> HAC p=0.0253
plain OLS  -> p=0.0054   (不校正自相关，不可作主结论)
HC1 robust -> p=0.0036   (仅异方差，不校正自相关)
```

p 在 0.05 两侧滑动，maxlags=4/6 时 ≥0.05。**这正是"边际"的定义**：结论的显著与否取决于一个本可辩护但非唯一的带宽选择。plain OLS / HC1 的 p≈0.005 看起来强，但它们不校正 8-day ET 序列的时间自相关，按工程一贯方法不能用作主结论，仅列作上界参照。

## 为什么 ET 在归档数据上（baseline）不显著 —— 讲死

1. **机制：单一异常年落 pre 期。** 2019 是英格兰东南公认干旱年，两区同时变干，ΔET（Impact−Control）在该年达 −0.80，而其余 pre 年份 ΔET 在 ±0.07 内。这把 pre 均值压低，缩小了 pre→post 的落差，于是 baseline 的 Post 系数被稀释到 −0.081。这是真实气候信号，不是数据错误。
2. **方向一致但量级小。** post 期 2021–2025 每年 ΔET 皆为负（−0.06 至 −0.33），方向与"建设抑制蒸散"一致；但 MODIS MOD16A2GF 的 500 m 像元相对停车核/转换面积偏粗，单位信号本就小。
3. **非参不支持分布层面差异。** 即便剔除 2019，MW p=0.197；说明 pre/post 的 ΔET 分布重叠仍大，差异集中在均值而非整体分布。

## 对 ET 表述的处置建议

- **不要**把 spec (b)/(c) 的 −0.205 / p=0.049 当作新的主结果替换 baseline。
- **应当**在 README/AUDIT/v3 导读的 ET 段，把现有定性表述补成：baseline n.s.（−0.081）为主报口径；并列报告"控制/剔除 2019 干旱年后参数 DiD 升至 −0.205、HAC p≈0.049（边际、带宽敏感、非参 MW 仍 n.s.）"，明确标注该显著性**条件依赖于对一个气候异常年的处理**。
- ET 的定位维持为**定性佐证**（方向为负、post 逐年皆负），不升级为 well-powered 支柱。

## 边界

- 本分析纯本地，未重跑 GEE，未换 ET 产品。备忘 §1 提到的 reference-ET（FAO-56 Penman-Monteith ET₀）归一化、PML_V2/MOD16 稳健性、合成控制，均需本地没有的气象驱动或新 GEE 提取，未做。
- split=2021-06-01 沿用脚本 11；该分割点本身的一手源锚定见 `documentation/construction_timeline_sources.md`（实现 3）。若分割点移动，2019 落 pre 还是 post 会变，本结论需重估。[此依赖为真实未决项]
