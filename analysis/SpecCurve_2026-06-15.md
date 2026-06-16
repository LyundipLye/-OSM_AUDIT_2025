# Specification-curve / multiverse —— 实测结果

**脚本**：`analysis/SpecCurve_2026-06-15.py` ｜ **图**：`visualisations/SpecCurve_{NDVI_core,LST_parking_core,LST_full_polygon,ET_500m}_2026-06-15.png`
**日期**：2026-06-15 ｜ 全部数字实跑，无编造。
**方法**：对每条 headline DiD 遍历可本地变动的研究者自由度——分割日期月度网格 2021-02..2021-12（11）× 季节窗口（full-year / grow Mar–Oct / warm Apr–Sep / summer JJA，4）× HAC 带宽（Andrews n^1/3 / NW rule-of-thumb / 2×Andrews / fixed 6，4）= 每指标最多 176 个 specification。估计量 = HAC DiD Post 系数，`delta=Impact−Control`，双侧 α=0.05。

## 结论先行（每指标 176 specs）

| 指标 | 中位 β | 符号一致性 | 显著占比 (p<0.05) | 读法 |
|:--|:--|:--|:--|:--|
| **NDVI 核**（FDR 幸存）| **−0.342** | **100%** 负 | **100%** | 全多元宇宙稳健，无 spec 依赖 |
| **停车核 LST**（FDR 幸存）| **+1.225** | **100%** 正 | **89.8%** | 高度稳健；仅 summer JJA 窗（obs 最少）降至 59% |
| LST 全多边形（primary）| +0.653 | 100% 正 | 31.8% | 方向稳但显著性脆——印证边际地位 |
| ET（500m）| −0.179 | 100% 负 | 25.0% | 方向稳（恒负）但显著性**完全挂在窗口选择** |

## 细节（实测）

- **NDVI 核**：β 区间 [−0.39, −0.25]，全部窗口 100% 显著。任意分割点 × 任意窗口 × 任意带宽都给同号显著负。**最稳的一条。**
- **停车核 LST**：β 区间 [+0.84, +1.83]，全部正。full-year/grow/warm 三窗 100% 显著；summer JJA（obs 最少）59% 显著、中位 p=0.021。**收敛证据强。**
- **LST 全多边形**：恒正，但仅 31.8% 显著（full-year 36%、grow 52%、warm 39%、JJA 0%）。证明「全多边形 = power 上限下的保守存在性证据」，不承担超过区域基线的举证。
- **ET**：恒负，但仅 25% 显著——且这 25% **全部集中在 warm Apr–Sep 窗口（该窗 100% 显著、中位 p=0.019）**，其余三窗 0% 显著。这是 ET 显著性脆弱、窗口依赖的直接证据（warm 窗正是 ET 抑制物理上应最强处），也是为什么 ET 只能作定性方向佐证、且需 reference-ET 归一化（见 Tier-2 roadmap §3）才能原理性判定。

## 是否动摇主结论

**没有，反而硬化。** 两条 FDR 幸存结论在多元宇宙里符号 100% 一致、显著占比 100%/89.8%；全多边形与 ET 的「方向稳、显著性边际/窗口依赖」与 README 修正后的诚实头条完全吻合。**呈现整张 spec-curve 本身就是最强的反 p-hacking 证据。**
