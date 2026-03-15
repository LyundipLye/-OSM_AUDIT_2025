// ==============================================================================
// OSM_AUDIT_2025: NDVI SPATIAL AUDIT
// Sentinel-2 NDVI 时序 + 对照区 + 敏感性分析
// ==============================================================================

// ⚠️ Update END_DATE before each run
var START_DATE = '2018-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 1. 审计区坐标
var shepperton = ee.Geometry.Point([-0.4640, 51.4065]); 
var analysisBuffer = shepperton.buffer(1000);

// 2. Sprawl Zone（新建停车场区域，对应 EIA 规划图 Zone C 中心）
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(100);

// 3. 对照区：Sunbury 方向未开发的稳定绿地（距 Shepperton ~2km，无大型开发）
var controlZone = ee.Geometry.Point([-0.4180, 51.4110]).buffer(100);

// 4. 敏感性分析点：围绕 sprawl zone 不同方位取样
var sensitivity = {
  'Sprawl_Core':  ee.Geometry.Point([-0.469366, 51.410315]).buffer(100),
  'Sprawl_North': ee.Geometry.Point([-0.469366, 51.411500]).buffer(100),
  'Sprawl_South': ee.Geometry.Point([-0.469366, 51.409100]).buffer(100),
  'Sprawl_East':  ee.Geometry.Point([-0.467000, 51.410315]).buffer(100),
  'Control':      ee.Geometry.Point([-0.4180,   51.4110  ]).buffer(100)
};

// Sentinel-2
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(analysisBuffer)
  .filterDate(START_DATE, END_DATE)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

function maskS2clouds(image) {
  var qa = image.select('QA60');
  var mask = qa.bitwiseAnd(1 << 10).eq(0).and(qa.bitwiseAnd(1 << 11).eq(0));
  return image.updateMask(mask).divide(10000);
}

var ndviCollection = sentinel2.map(function(img) {
  var masked = maskS2clouds(img);
  var ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return masked.addBands(ndvi).copyProperties(img, ['system:time_start', 'system:index']);
}).select('NDVI');

// ==============================================================================
// 图表 1: Sprawl Zone vs Control Zone 对比
// ==============================================================================
var chartSprawl = ui.Chart.image.series(ndviCollection, sprawlZone, ee.Reducer.mean(), 10)
  .setOptions({title: 'Sprawl Zone NDVI', vAxis: {min: 0, max: 0.8}, lineWidth: 2, pointSize: 3, colors: ['#FF3333']});
var chartControl = ui.Chart.image.series(ndviCollection, controlZone, ee.Reducer.mean(), 10)
  .setOptions({title: 'Control Zone NDVI (Undeveloped Reference)', vAxis: {min: 0, max: 0.8}, lineWidth: 2, pointSize: 3, colors: ['#33CC33']});
print(chartSprawl);
print(chartControl);

// ==============================================================================
// 图表 2: 敏感性分析 — 多点同时展示
// ==============================================================================
var sensKeys = Object.keys(sensitivity);
for (var i = 0; i < sensKeys.length; i++) {
  var key = sensKeys[i];
  var color = key === 'Control' ? '#33CC33' : '#FF3333';
  var chart = ui.Chart.image.series(ndviCollection, sensitivity[key], ee.Reducer.mean(), 10)
    .setOptions({title: 'Sensitivity: ' + key, vAxis: {min: 0, max: 0.8}, lineWidth: 1, pointSize: 2, colors: [color]});
  print(chart);
}

// ==============================================================================
// 损失图（2018基线 vs 近期）
// ==============================================================================
var baseline2018 = ndviCollection.filterDate('2018-01-01', '2019-01-01').mean();
var recent2026 = ndviCollection.filterDate('2025-09-01', END_DATE).mean();
var loss = baseline2018.subtract(recent2026).rename('NDVI_Loss');

Map.centerObject(shepperton, 15);
Map.addLayer(loss.clip(analysisBuffer), 
  {min:-0.3, max:0.3, palette:['darkgreen','green','white','red','darkred']}, 
  'NDVI Loss (Red=Decline)');
Map.addLayer(sprawlZone, {color: 'red'}, 'Sprawl Zone', true);
Map.addLayer(controlZone, {color: 'green'}, 'Control Zone', true);