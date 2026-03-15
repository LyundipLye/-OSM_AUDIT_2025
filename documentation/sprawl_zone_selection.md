# Sprawl Zone 选点说明与面积口径说明

## Sprawl Zone 坐标选定依据

**坐标**: `[-0.469366, 51.410315]`

该坐标对应 Shepperton Studios 扩建区域南侧的新建大型停车场群（EIA 规划文案中对应 Zone C），位于 Studios Road 以南、Shepperton Studios 主厂区西南方向。

选定理由：
1. 该区域在 2018 年前为绿地/农田，2020-2023 年间被转换为不透水沥青面积
2. 与 EIA 规划文件 (18/01212/OUT) 中标注的新增 parking capacity (2,595 spaces) 直接对应
3. Sentinel-2 和 Landsat 8 影像目视确认该区域经历了最显著的土地覆盖变化

## 敏感性分析

审计结果不依赖于单一坐标的选取，在 sprawl zone 周围 4 个方位各偏移约 100-200m 取样：

| 点位 | 坐标 | 用途 |
|------|------|------|
| Sprawl_Core | [-0.469366, 51.410315] | 主审计点 |
| Sprawl_North | [-0.469366, 51.411500] | 北偏 ~130m |
| Sprawl_South | [-0.469366, 51.409100] | 南偏 ~130m |
| Sprawl_East | [-0.467000, 51.410315] | 东偏 ~160m |
| Control | [-0.4105, 51.4074] | 对照区（附近未开发绿地） |

## 对照区选定依据

**坐标**: `[-0.4105, 51.4074]`

- 位于 Shepperton 东北方向约 3km，Thames 河北岸的稳定绿地
- 无大型开发项目记录
- 纬度/海拔与 sprawl zone 相近，排除地形干扰
- 同在 Sentinel-2 / Landsat 8 扫描路径内，确保传感器条件一致

## 面积口径说明

本项目 `02_spatial_projection.py` 输出的 **13.2 ha** 仅统计 OSM 中标记为 `amenity=parking` 的多边形投影面积，**不等于** EIA 规划文件中的总开发面积。

| 指标 | 数值 | 来源 |
|------|------|------|
| 停车场面积 (parking polygons) | 13.2 ha | OSM 空间审计 |
| 新增建筑面积 (floorspace) | 16.4 ha (164,000 sqm) | EIA 18/01212/OUT |
| 绿带总损失 (Metropolitan Green Belt) | 39 ha | Spelthorne Borough Council |

停车场面积是 logistical sprawl 的指标（不透水面积扩张），不应与总开发面积混淆。
