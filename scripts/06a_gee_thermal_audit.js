// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT
// TARGET: Shepperton Studios Expansion (Sprawl Zone)
// SENSOR: Landsat 8 Collection 2 Tier 1 Level 2 (Thermal Infrared Sensor - TIRS)
// METRIC: Land Surface Temperature (LST) in Celsius
//
// ⚠️ IMPORTANT: This script runs in the Google Earth Engine Code Editor.
//    https://code.earthengine.google.com/
// ==============================================================================

// 1. 定位微观灾区 (Sprawl Zone) - 也就是你之前算沥青面积的地方
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(250); 
var macroRegion = sprawlZone.buffer(1500); // 1.5公里宏观背景区域

// ⚠️ IMPORTANT: Update END_DATE to the current date before each run.
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 2. 导入 Landsat 8 地表温度数据集
var landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
  .filterBounds(macroRegion)
  .filterDate(START_DATE, END_DATE);

// 3. 去云处理与开尔文到摄氏度的热力学转换函数
function prepLST(image) {
  var qa = image.select('QA_PIXEL');
  var cloudShadowBitMask = (1 << 4);
  var cloudsBitMask = (1 << 3);
  var mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0)
    .and(qa.bitwiseAnd(cloudsBitMask).eq(0));

  var lstKelvin = image.select('ST_B10').multiply(0.00341802).add(149.0);
  var lstCelsius = lstKelvin.subtract(273.15).rename('LST_Celsius');

  return image.addBands(lstCelsius)
              .updateMask(mask)
              .copyProperties(image, ['system:time_start']);
}

var lstCollection = landsat8.map(prepLST).select('LST_Celsius');

// ==============================================================================
// 模块 A: 结构性热力学升温折线图 (带线性回归趋势线)
// ==============================================================================
var tsChart = ui.Chart.image.series({
  imageCollection: lstCollection,
  region: sprawlZone,
  reducer: ee.Reducer.mean(),
  scale: 30,
  xProperty: 'system:time_start'
}).setOptions({
  title: 'Thermodynamic Audit: Absolute LST Trend (2015-2026)',
  vAxis: {title: 'Surface Temperature (°C)'},
  hAxis: {title: 'Date'},
  lineWidth: 0,
  pointSize: 4,
  colors: ['#FF4500'], 
  trendlines: { 0: {color: 'red', lineWidth: 2, opacity: 0.8, showR2: true} } 
});
print(tsChart);

// ==============================================================================
// 模块 B: 扩建前 vs 扩建后 【相对热岛异常 (UHI Anomaly)】重构
// 核心逻辑：剥离宏观气候波动，计算"局部额外发热量"
// ==============================================================================
// 提取 2017年(施工前)和 2024年(施工后)的夏季平均绝对温度
var lst2017 = lstCollection.filterDate('2017-06-01', '2017-09-01').mean();
var lst2024 = lstCollection.filterDate('2024-06-01', '2024-09-01').mean();

// 计算该年份、该区域的"平均背景气温"
var mean2017 = ee.Number(lst2017.reduceRegion({reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30}).get('LST_Celsius'));
var mean2024 = ee.Number(lst2024.reduceRegion({reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30}).get('LST_Celsius'));

// 【极其关键的一步】：像素绝对温度 - 当年背景平均温度 = 相对异常值 (Anomaly)
// 正值代表比周围热，负值代表比周围冷。彻底消除跨年份气温不同的影响。
var anomaly2017 = lst2017.subtract(mean2017).rename('UHI_Anomaly');
var anomaly2024 = lst2024.subtract(mean2024).rename('UHI_Anomaly');

// 提取真正的"物理疤痕"：2024年相比于2017年，该区域【额外恶化】了多少度
var thermodynamicScar = anomaly2024.subtract(anomaly2017);

// ==============================================================================
// 视觉渲染参数
// ==============================================================================
// 异常值配色：深蓝(冷异常) -> 浅黄(背景均温0度差) -> 深红(极端热异常)
var anomalyVis = {
  min: -2, max: 4,
  palette: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
};

// 疤痕配色：专门显示增温恶化的区域 (纯黑到刺眼的血红再到霓虹黄)
var scarVis = {
  min: 0, max: 3,
  palette: ['#000000', '#5c0000', '#FF0000', '#FF4500', '#FFFF00']
};

Map.centerObject(sprawlZone, 14);
Map.setOptions('SATELLITE'); // 设为黑色卫星底图增强对比

// 添加图层 (默认关闭前两个，展示最终的疤痕图层)
Map.addLayer(anomaly2017.clip(macroRegion), anomalyVis, '2017 Relative Thermal Anomaly (Pre)', false);
Map.addLayer(anomaly2024.clip(macroRegion), anomalyVis, '2024 Relative Thermal Anomaly (Post)', false);
Map.addLayer(thermodynamicScar.clip(macroRegion), scarVis, 'The Thermodynamic Scar (Net Heat Increase)');
