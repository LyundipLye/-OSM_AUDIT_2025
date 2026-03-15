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

// 2. 对照区
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(250);

// 包围两个区域的矩形（避免 GEE union 误差问题）
var combinedBounds = ee.Geometry.Rectangle([-0.48, 51.40, -0.40, 51.42]);

// Landsat 8
var landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
  .filterBounds(combinedBounds)
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
// 图表: Sprawl Zone vs Control Zone LST 时序
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
// UHI Anomaly: 多年夏季复合（消除单一年份气候异常）
// ==============================================================================
var summerPre  = lstCollection.filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2016-01-01', '2019-01-01').mean();
var summerPost = lstCollection.filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2023-01-01', '2026-01-01').mean();

// 宏观背景均温（用于剥离区域气候趋势）
var meanPre  = summerPre.reduceRegion({
  reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30, bestEffort: true
});
var meanPost = summerPost.reduceRegion({
  reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30, bestEffort: true
});

var anomalyPre  = summerPre.subtract(ee.Number(meanPre.get('LST_Celsius'))).rename('UHI');
var anomalyPost = summerPost.subtract(ee.Number(meanPost.get('LST_Celsius'))).rename('UHI');

// 净热力疤痕
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

Map.addLayer(anomalyPre.clip(macroRegion), anomalyVis, 'Pre-Construction UHI (2016-2018)', false);
Map.addLayer(anomalyPost.clip(macroRegion), anomalyVis, 'Post-Construction UHI (2023-2025)', false);
Map.addLayer(thermodynamicScar.clip(macroRegion), scarVis, 'Thermodynamic Scar (Net Heat Increase)');
Map.addLayer(sprawlZone, {color: 'red'}, 'Sprawl Zone', true);
Map.addLayer(controlZone, {color: 'green'}, 'Control Zone', true);
