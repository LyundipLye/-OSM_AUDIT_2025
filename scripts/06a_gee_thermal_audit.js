// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT
// Landsat 8 C2 T1 L2 (TIRS) — LST 时序 + 对照区 + 多年复合
// ==============================================================================

// ⚠️ Update END_DATE before each run
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 1. Sprawl Zone（新建停车场，EIA Zone C）
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(250); 
var macroRegion = sprawlZone.buffer(1500);

// 2. 对照区：Sunbury 方向稳定绿地
var controlZone = ee.Geometry.Point([-0.4180, 51.4110]).buffer(250);

// Landsat 8
var landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
  .filterBounds(macroRegion)
  .filterDate(START_DATE, END_DATE);

function prepLST(image) {
  var qa = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 4).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0));
  var lstCelsius = image.select('ST_B10').multiply(0.00341802).add(149.0)
    .subtract(273.15).rename('LST_Celsius');
  return image.addBands(lstCelsius).updateMask(mask)
    .copyProperties(image, ['system:time_start']);
}

var lstCollection = landsat8.map(prepLST).select('LST_Celsius');

// ==============================================================================
// 图表 1: Sprawl Zone LST 时序（带回归趋势线）
// ==============================================================================
var chartSprawl = ui.Chart.image.series({
  imageCollection: lstCollection, region: sprawlZone,
  reducer: ee.Reducer.mean(), scale: 30, xProperty: 'system:time_start'
}).setOptions({
  title: 'Sprawl Zone: LST Trend (2015-2026)',
  vAxis: {title: '°C'}, hAxis: {title: 'Date'},
  lineWidth: 0, pointSize: 4, colors: ['#FF4500'], 
  trendlines: {0: {color: 'red', lineWidth: 2, opacity: 0.8, showR2: true}}
});
print(chartSprawl);

// 图表 2: 对照区 LST 时序
var chartControl = ui.Chart.image.series({
  imageCollection: lstCollection, region: controlZone,
  reducer: ee.Reducer.mean(), scale: 30, xProperty: 'system:time_start'
}).setOptions({
  title: 'Control Zone: LST Trend (Undeveloped Reference)',
  vAxis: {title: '°C'}, hAxis: {title: 'Date'},
  lineWidth: 0, pointSize: 4, colors: ['#33CC33'], 
  trendlines: {0: {color: 'green', lineWidth: 2, opacity: 0.8, showR2: true}}
});
print(chartControl);

// ==============================================================================
// UHI Anomaly: 多年复合（3年均值 vs 3年均值）
// 消除单一年份气候异常的影响
// ==============================================================================
// 施工前 2016-2018 夏季复合
var lstPre = lstCollection.filterDate('2016-06-01', '2018-09-01')
  .filter(ee.Filter.calendarRange(6, 8, 'month')).mean();
// 施工后 2023-2025 夏季复合
var lstPost = lstCollection.filterDate('2023-06-01', '2025-09-01')
  .filter(ee.Filter.calendarRange(6, 8, 'month')).mean();

// 宏观背景均温（用于剥离气候趋势）
var meanPre  = ee.Number(lstPre.reduceRegion({reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30}).get('LST_Celsius'));
var meanPost = ee.Number(lstPost.reduceRegion({reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30}).get('LST_Celsius'));

// 相对异常值：像素温度 - 区域均温 = 局部热岛强度
var anomalyPre  = lstPre.subtract(meanPre).rename('UHI_Anomaly');
var anomalyPost = lstPost.subtract(meanPost).rename('UHI_Anomaly');

// 净热力疤痕 = 施工后异常 - 施工前异常
var thermodynamicScar = anomalyPost.subtract(anomalyPre);

// ==============================================================================
// 地图渲染
// ==============================================================================
var anomalyVis = {
  min: -2, max: 4,
  palette: ['#313695','#4575b4','#74add1','#abd9e9','#e0f3f8','#ffffbf','#fee090','#fdae61','#f46d43','#d73027','#a50026']
};
var scarVis = {
  min: 0, max: 3,
  palette: ['#000000','#5c0000','#FF0000','#FF4500','#FFFF00']
};

Map.centerObject(sprawlZone, 14);
Map.setOptions('SATELLITE');

Map.addLayer(anomalyPre.clip(macroRegion), anomalyVis, 'Pre-Construction UHI (2016-2018 Summer Composite)', false);
Map.addLayer(anomalyPost.clip(macroRegion), anomalyVis, 'Post-Construction UHI (2023-2025 Summer Composite)', false);
Map.addLayer(thermodynamicScar.clip(macroRegion), scarVis, 'Thermodynamic Scar (Net Heat Increase)');
Map.addLayer(sprawlZone, {color: 'red'}, 'Sprawl Zone', true);
Map.addLayer(controlZone, {color: 'green'}, 'Control Zone', true);
