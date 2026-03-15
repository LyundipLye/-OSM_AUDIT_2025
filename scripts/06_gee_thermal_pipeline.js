// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT (v3 — Triple-Satellite + NDBI Mask)
// Landsat 7 ETM+ (60m) + Landsat 8 C2 (100m) + Landsat 9 C2 (100m) — NDBI-filtered LST
// ==============================================================================

// ⚠️ Update END_DATE before each run
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 1. Sprawl Zone（新建停车场，EIA Zone C）
// Buffer=150m：兼顾统计稳定性和空间聚焦
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(150);
var macroRegion = sprawlZone.buffer(1500);

// 2. 对照区（与 NDVI 管线完全一致的坐标）
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(150);

// 包围两个区域的矩形
var combinedBounds = ee.Geometry.Rectangle([-0.48, 51.40, -0.40, 51.42]);

// ==============================================================================
// Landsat 7 ETM+ (60m 热红外，2003+ 有 SLC-off 但 reduceRegion 自动忽略条带)
// ==============================================================================
var landsat7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
  .filterBounds(combinedBounds)
  .filterDate(START_DATE, END_DATE);

function prepL7(image) {
  var qa = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 1).eq(0)  // dilated cloud
    .and(qa.bitwiseAnd(1 << 3).eq(0))     // cloud
    .and(qa.bitwiseAnd(1 << 4).eq(0))     // cloud shadow
    .and(qa.bitwiseAnd(1 << 5).eq(0));    // snow

  var lstCelsius = image.select('ST_B6').multiply(0.00341802).add(149.0)
    .subtract(273.15).rename('LST_Celsius');
  
  // NDBI = (SWIR1 - NIR) / (SWIR1 + NIR)  L7: SWIR1=SR_B5, NIR=SR_B4
  var swir = image.select('SR_B5').multiply(0.0000275).add(-0.2);
  var nir  = image.select('SR_B4').multiply(0.0000275).add(-0.2);
  var ndbi = swir.subtract(nir).divide(swir.add(nir)).rename('NDBI');
  
  return image.addBands(lstCelsius).addBands(ndbi).updateMask(mask)
    .copyProperties(image, ['system:time_start'])
    .set('satellite', 'L7');
}

// ==============================================================================
// Landsat 8 OLI/TIRS (100m 热红外)
// ==============================================================================
var landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
  .filterBounds(combinedBounds)
  .filterDate(START_DATE, END_DATE);

function prepL8(image) {
  var qa = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 1).eq(0)
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  var lstCelsius = image.select('ST_B10').multiply(0.00341802).add(149.0)
    .subtract(273.15).rename('LST_Celsius');
    
  // NDBI: L8 SWIR1=SR_B6, NIR=SR_B5
  var swir = image.select('SR_B6').multiply(0.0000275).add(-0.2);
  var nir  = image.select('SR_B5').multiply(0.0000275).add(-0.2);
  var ndbi = swir.subtract(nir).divide(swir.add(nir)).rename('NDBI');
  
  return image.addBands(lstCelsius).addBands(ndbi).updateMask(mask)
    .copyProperties(image, ['system:time_start'])
    .set('satellite', 'L8');
}

// ==============================================================================
// Landsat 9 OLI-2/TIRS-2 (100m 热红外，2022+)
// ==============================================================================
var landsat9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2')
  .filterBounds(combinedBounds)
  .filterDate(START_DATE, END_DATE);

function prepL9(image) {
  var qa = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 1).eq(0)
    .and(qa.bitwiseAnd(1 << 3).eq(0))
    .and(qa.bitwiseAnd(1 << 4).eq(0))
    .and(qa.bitwiseAnd(1 << 5).eq(0));

  var lstCelsius = image.select('ST_B10').multiply(0.00341802).add(149.0)
    .subtract(273.15).rename('LST_Celsius');
    
  // NDBI: L9 same as L8
  var swir = image.select('SR_B6').multiply(0.0000275).add(-0.2);
  var nir  = image.select('SR_B5').multiply(0.0000275).add(-0.2);
  var ndbi = swir.subtract(nir).divide(swir.add(nir)).rename('NDBI');
  
  return image.addBands(lstCelsius).addBands(ndbi).updateMask(mask)
    .copyProperties(image, ['system:time_start'])
    .set('satellite', 'L9');
}

// ==============================================================================
// 三星融合 (Triple-Satellite Merge)
// ==============================================================================
var lstCollection = landsat7.map(prepL7)
  .merge(landsat8.map(prepL8))
  .merge(landsat9.map(prepL9))
  .select(['LST_Celsius', 'NDBI'])
  .sort('system:time_start');

print('Total scenes (L7+L8+L9):', lstCollection.size());

// ==============================================================================
// 时序提取 — NDBI 掩膜：只提取不透水面 (NDBI > 0) 的温度
// ==============================================================================
var roiCollection = ee.FeatureCollection([
  ee.Feature(sprawlZone, {label: 'Sprawl_Zone_Core'}),
  ee.Feature(controlZone, {label: 'Control_Zone'})
]);

var extractStats = function(image) {
  // 对 Sprawl Zone：只取 NDBI > 0 的像素（不透水面/建筑物）
  var imperviousMask = image.select('NDBI').gt(0);
  var lstImpervious = image.select('LST_Celsius').updateMask(imperviousMask);
  
  // 对 Control Zone：不加 NDBI 掩膜（公园本来就是绿地，NDBI < 0 是正常的）
  var lstRaw = image.select('LST_Celsius');
  
  // 安全默认值：NDBI 掩膜可能滤掉全部像素（施工前该区域还是绿地）
  var defaults = ee.Dictionary({mean: null, stdDev: null});
  
  // Sprawl Zone: 只有不透水面的温度（空结果回退为 null）
  var spStats = defaults.combine(lstImpervious.reduceRegion({
    reducer: ee.Reducer.mean().combine({reducer2: ee.Reducer.stdDev(), sharedInputs: true}),
    geometry: sprawlZone,
    scale: 30,
    bestEffort: true
  }));
  
  // Control Zone: 全区域温度
  var ctStats = defaults.combine(lstRaw.reduceRegion({
    reducer: ee.Reducer.mean().combine({reducer2: ee.Reducer.stdDev(), sharedInputs: true}),
    geometry: controlZone,
    scale: 30,
    bestEffort: true
  }));
  
  return ee.Feature(null, {
    'Sprawl_Zone_Core_mean': spStats.get('mean'),
    'Sprawl_Zone_Core_std': spStats.get('stdDev'),
    'Control_Zone_mean': ctStats.get('mean'),
    'Control_Zone_std': ctStats.get('stdDev')
  }).set('system:time_start', image.get('system:time_start'));
};

var timeSeriesData = lstCollection.map(extractStats);

var consolidatedChart = ui.Chart.feature.byFeature({
  features: timeSeriesData,
  xProperty: 'system:time_start',
  yProperties: [
    'Sprawl_Zone_Core_mean', 'Sprawl_Zone_Core_std', 
    'Control_Zone_mean', 'Control_Zone_std'
  ]
})
.setChartType('ScatterChart')
.setOptions({
  title: 'LST Analytics: Triple-Satellite (L7+L8+L9) + NDBI Impervious Mask',
  vAxis: {title: 'LST Celsius'},
  pointSize: 3,
  dataOpacity: 0.6
});

print("【ACTION REQUIRED】");
print("1. Triple-satellite fusion (L7+L8+L9) with NDBI impervious surface mask.");
print("2. Sprawl Zone: ONLY impervious pixels (NDBI > 0). Control Zone: full greenland.");
print("3. Click the pop-out arrow -> Download CSV.");
print("4. MUST Save as: data/raw_telemetry/ee-chart_lst.csv");
print(consolidatedChart);

// ==============================================================================
// UHI Anomaly: 多年夏季复合（使用三星融合数据）
// ==============================================================================
var summerPre  = lstCollection.select('LST_Celsius')
  .filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2016-01-01', '2019-01-01').mean();
var summerPost = lstCollection.select('LST_Celsius')
  .filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2023-01-01', '2026-01-01').mean();

var meanPre  = summerPre.reduceRegion({
  reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30, bestEffort: true
});
var meanPost = summerPost.reduceRegion({
  reducer: ee.Reducer.mean(), geometry: macroRegion, scale: 30, bestEffort: true
});

var anomalyPre  = summerPre.subtract(ee.Number(meanPre.get('LST_Celsius'))).rename('UHI');
var anomalyPost = summerPost.subtract(ee.Number(meanPost.get('LST_Celsius'))).rename('UHI');

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
