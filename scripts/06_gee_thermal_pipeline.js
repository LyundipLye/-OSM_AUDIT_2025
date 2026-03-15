// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT
// Landsat 8 C2 T1 L2 (TIRS) — LST 时序 + 对照区 + 多年复合
// ==============================================================================

// ⚠️ Update END_DATE before each run
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 1. Sprawl Zone（新建停车场，EIA Zone C）
// Buffer=150m：Landsat 8 TIRS 热红外原生分辨率 100m，150m 半径 ≈ 7 个原生像素，
// 兼顾统计稳定性和空间聚焦（250m 过大会稀释热信号）
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(150); 
var macroRegion = sprawlZone.buffer(1500);

// 2. 对照区（与 NDVI 管线完全一致的坐标）
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(150);

// 包围两个区域的矩形（避免 GEE union 误差问题）
var combinedBounds = ee.Geometry.Rectangle([-0.48, 51.40, -0.40, 51.42]);

// Landsat 8
var landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
  .filterBounds(combinedBounds)
  .filterDate(START_DATE, END_DATE);

function prepLST(image) {
  var qa = image.select('QA_PIXEL');
  
  // 增强型 Landsat 8 去云掩膜：包含扩张云(Bit 1)、云(Bit 3)、云影(Bit 4)、雪(Bit 5)
  var dilatedCloud = 1 << 1;
  var cloud = 1 << 3;
  var cloudShadow = 1 << 4;
  var snow = 1 << 5;
  
  var mask = qa.bitwiseAnd(dilatedCloud).eq(0)
    .and(qa.bitwiseAnd(cloud).eq(0))
    .and(qa.bitwiseAnd(cloudShadow).eq(0))
    .and(qa.bitwiseAnd(snow).eq(0));

  var lstCelsius = image.select('ST_B10').multiply(0.00341802).add(149.0)
    .subtract(273.15).rename('LST_Celsius');
  return image.addBands(lstCelsius).updateMask(mask)
    .copyProperties(image, ['system:time_start']);
}

var lstCollection = landsat8.map(prepLST).select('LST_Celsius');

// ==============================================================================
// 图表: 统一输出合并图表 (Sprawl vs Control)
// ==============================================================================
var roiCollection = ee.FeatureCollection([
  ee.Feature(sprawlZone, {label: 'Sprawl_Zone_Core'}),
  ee.Feature(controlZone, {label: 'Control_Zone'})
]);

// 为了计算方差 (stdDev) 并导出宽表 (Wide Format)
var extractStats = function(image) {
  var stats = image.reduceRegions({
    collection: roiCollection,
    reducer: ee.Reducer.mean().combine({
      reducer2: ee.Reducer.stdDev(),
      sharedInputs: true
    }),
    scale: 30
  });
  
  // 安全提取：使用 filter + first，避免动态生成导致的属性类型丢失
  var sp = ee.Feature(stats.filter(ee.Filter.eq('label', 'Sprawl_Zone_Core')).first());
  var ct = ee.Feature(stats.filter(ee.Filter.eq('label', 'Control_Zone')).first());
  
  // 原生保留 system:time_start 防止图表 x 轴识别报错
  return ee.Feature(null, {
    'Sprawl_Zone_Core_mean': sp.get('mean'),
    'Sprawl_Zone_Core_std': sp.get('stdDev'),
    'Control_Zone_mean': ct.get('mean'),
    'Control_Zone_std': ct.get('stdDev')
  }).set('system:time_start', image.get('system:time_start'));
};

// 获得宽表 FeatureCollection，每张影像对应1行
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
  title: 'LST Analytics Extraction Ready (with UQ StdDev Wide-Format)',
  vAxis: {title: 'LST Celsius'},
  pointSize: 4,
  dataOpacity: 0.6
});

print("【ACTION REQUIRED】");
print("1. We now explicitly export WIDE-FORMAT telemetry including Pixel StdDev.");
print("2. Click the pop-out arrow in the top right of this chart -> Download CSV.");
print("3. MUST Save as: data/raw_telemetry/ee-chart_lst.csv");
print(consolidatedChart);

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
