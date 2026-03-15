# 数据来源与可信度说明

## OpenStreetMap (OSM) 数据可信度

本项目使用的空间数据通过 Overpass API 从 OpenStreetMap 提取。OSM 是一个众包地理数据平台，其数据质量已被多项学术研究验证：

- **Haklay, M. (2010)** — "How good is volunteered geographical information? A comparative study of OpenStreetMap and Ordnance Survey datasets." _Environment and Planning B_, 37(4), 682-703.
  - 结论：英国城市区域 OSM 位置精度在 6m 以内，完整度约 80%

- **Barrington-Leigh, C. & Millard-Ball, A. (2017)** — "The world's user-generated road map is more than 80% complete." _PLOS ONE_, 12(8), e0180698.
  - 结论：全球 OSM 道路网络完整度超过 80%，发达国家高于 95%

- **Fan, H., Zipf, A., Fu, Q. & Neis, P. (2014)** — "Quality assessment for building footprints data on OpenStreetMap." _International Journal of Geographical Information Science_, 28(4), 700-719.
  - 结论：OSM 建筑轮廓在欧洲主要城市与官方数据集重叠率超过 85%

## Sentinel-2 遥感数据

- **数据集**: COPERNICUS/S2_SR_HARMONIZED (ESA)
- **空间分辨率**: 10m (B4, B8 用于 NDVI 计算)
- **云掩膜**: QA60 位元掩膜（去除云层和卷云）

## Landsat 8 热红外数据

- **数据集**: LANDSAT/LC08/C02/T1_L2 (USGS)
- **热红外分辨率**: 100m 原生 (重采样至 30m)
- **温度转换**: ST_B10 × 0.00341802 + 149.0 (DN -> Kelvin) -> -273.15 (-> Celsius)
- **云掩膜**: QA_PIXEL 位运算（去除云层和云影）
- **注意**: 100m 原生分辨率意味着 250m buffer zone 内约覆盖 6-8 个独立热像素

## 坐标参考系统

- **输入 CRS**: EPSG:4326 (WGS84, 经纬度)
- **投影 CRS**: EPSG:27700 (British National Grid, 米制)
- **投影精度**: 英国本土 < 0.1% 面积误差 (Ordnance Survey 标准)
