// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT - PHASE IV
// Spatial Transect Decay (LST Distance Gradient)
// Proves Spatial Advection / Spillover Effect of the Urban Heat Island
// ==============================================================================

// ⚠️ Update END_DATE before each run if needed, though this uses fixed summer composites
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';

// 1. Impact Zone — 精确的停车场多边形 (The "Point Source" of heat)
var sprawlZone = ee.Geometry.Polygon([[
  [-0.4676848515978538,51.40882742185046],
  [-0.4669123754015647,51.409429716784295],
  [-0.46926006378714025,51.41065315692719],
  [-0.4703222185570377,51.40986350085904],
  [-0.4676848515978538,51.40882742185046]
]]);

var maxDistance = 800; // 设定最远分析距离 (meters)
var stepSize = 50;     // 每圈 50 米带宽

var macroRegion = sprawlZone.buffer(maxDistance + 200);

// 包围整个研究区域的矩形，用于影像裁剪过滤
var combinedBounds = ee.Geometry.Rectangle([-0.49, 51.39, -0.45, 51.43]);

// ==============================================================================
// 影像融合：Landsat 7 + 8 + 9 (无 NDBI 掩膜，保留真实辐射)
// ==============================================================================
function prepL7(image) {
  var qa = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var lstCelsius = image.select('ST_B6').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST_Celsius');
  return image.addBands(lstCelsius).updateMask(mask).copyProperties(image, ['system:time_start']);
}
var landsat7 = ee.ImageCollection('LANDSAT/LE07/C02/T1_L2').filterBounds(combinedBounds).filterDate(START_DATE, END_DATE);

function prepL89(image) {
  var qa = image.select('QA_PIXEL');
  var mask = qa.bitwiseAnd(1 << 1).eq(0).and(qa.bitwiseAnd(1 << 3).eq(0)).and(qa.bitwiseAnd(1 << 4).eq(0)).and(qa.bitwiseAnd(1 << 5).eq(0));
  var lstCelsius = image.select('ST_B10').multiply(0.00341802).add(149.0).subtract(273.15).rename('LST_Celsius');
  return image.addBands(lstCelsius).updateMask(mask).copyProperties(image, ['system:time_start']);
}
var landsat8 = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2').filterBounds(combinedBounds).filterDate(START_DATE, END_DATE);
var landsat9 = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2').filterBounds(combinedBounds).filterDate(START_DATE, END_DATE);

var lstCollection = landsat7.map(prepL7)
  .merge(landsat8.map(prepL89))
  .merge(landsat9.map(prepL89))
  .select(['LST_Celsius']);

// ==============================================================================
// 提取 夏季 (JJA) 复合均值 (消除单日气候异常)
// ==============================================================================
var summerPre = lstCollection
  .filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2016-01-01', '2019-01-01')
  .mean();

var summerPost = lstCollection
  .filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2023-01-01', '2026-01-01')
  .mean();

// 计算复合图像，合并为一个 Image 以便提取
var lstComposite = ee.Image([
  summerPre.rename('Pre_LST_mean'),
  summerPost.rename('Post_LST_mean')
]);

// ==============================================================================
// 构建同心圆环 (Concentric Buffers)
// ==============================================================================
var distances = ee.List.sequence(0, maxDistance - stepSize, stepSize);

// Distance 0 = 核心区本身 (Impact Zone)
var coreFeature = ee.Feature(sprawlZone, {
  'Distance_m': 0,
});

// 生成外部环形缓冲区
var ringsList = distances.map(function(d) {
  var dNum = ee.Number(d);
  var inner = sprawlZone.buffer(dNum.max(0.1));
  var outer = sprawlZone.buffer(dNum.add(stepSize));
  var ring = outer.difference(inner); // 切出面包圈形状
  
  // 对于 0-50m 这层环，我们标注其代表距离为25m
  return ee.Feature(ring, {
    'Distance_m': dNum.add(stepSize / 2)
  });
});

// 合并核心区与环形区
var transectZones = ee.FeatureCollection(ee.List([coreFeature]).cat(ringsList));

// ==============================================================================
// 提取每个圆环的平均 LST
// ==============================================================================
var extractDecay = function(feature) {
  var stats = lstComposite.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: feature.geometry(),
    scale: 30,  // 使用 30m 提取，GEE 会自动用最近邻或双线性重采样 100m 原生 LST
    bestEffort: true
  });
  
  return feature.set({
    'Pre_LST_mean': stats.get('Pre_LST_mean'),
    'Post_LST_mean': stats.get('Post_LST_mean')
  });
};

var decayData = transectZones.map(extractDecay);

// ==============================================================================
// 绘制 UI 图表并输出
// ==============================================================================
var decayChart = ui.Chart.feature.byFeature({
  features: decayData,
  xProperty: 'Distance_m',
  yProperties: ['Pre_LST_mean', 'Post_LST_mean']
})
.setChartType('LineChart')
.setOptions({
  title: 'Spatial Transect (0-800m): Summer LST Decay Margin',
  vAxis: {title: 'LST Celsius (°C)'},
  hAxis: {title: 'Distance from Impact Zone Boundary (meters)'},
  lineWidth: 2,
  pointSize: 5,
  colors: ['#33CC33', '#FF4500'] // Pre = Green, Post = Red
});

print("【ACTION REQUIRED】");
print("1. Summer composite (JJA) spatial advection decay curve.");
print("2. Click the pop-out arrow -> Download CSV.");
print("3. MUST Save as: data/raw_telemetry/ee-chart_decay.csv");
print(decayChart);

// ==============================================================================
// 可视化渲染 (用于截屏放PPT)
// ==============================================================================
Map.centerObject(sprawlZone, 15);
Map.setOptions('SATELLITE');

// 将环形区域用空心白线画出以示示意图
var empty = ee.Image().byte();
var outline = empty.paint({
  featureCollection: transectZones,
  color: 1,
  width: 1
});
Map.addLayer(outline, {palette: ['FFFFFF']}, 'Transect Rings');

var anomalyVis = {
  min: 25, max: 35, // 绝对温度范围
  palette: ['#313695','#4575b4','#74add1','#abd9e9','#e0f3f8','#ffffbf','#fee090','#fdae61','#f46d43','#d73027','#a50026']
};
Map.addLayer(summerPre.clip(macroRegion), anomalyVis, 'Summer Pre (2016-2018)', false);
Map.addLayer(summerPost.clip(macroRegion), anomalyVis, 'Summer Post (2023-2025)', true);
