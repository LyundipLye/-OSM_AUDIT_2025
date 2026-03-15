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
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(100);

// 4. 敏感性分析点：围绕 sprawl zone 不同方位取样
var sensitivity = {
  'Sprawl_Core':  ee.Geometry.Point([-0.469366, 51.410315]).buffer(100),
  'Sprawl_North': ee.Geometry.Point([-0.469366, 51.411500]).buffer(100),
  'Sprawl_South': ee.Geometry.Point([-0.469366, 51.409100]).buffer(100),
  'Sprawl_East':  ee.Geometry.Point([-0.467000, 51.410315]).buffer(100),
  'Sprawl_West':  ee.Geometry.Point([-0.472000, 51.410315]).buffer(100),
  'Control':      ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(100)
};

// Sentinel-2
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(analysisBuffer)
  .filterDate(START_DATE, END_DATE)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

var maskS2clouds = function(image) {
  // 1. 基本的 QA60 去云掩膜
  var qa = image.select('QA60');
  var maskQA = qa.bitwiseAnd(1 << 10).eq(0).and(qa.bitwiseAnd(1 << 11).eq(0));
  
  // 2. 增强型 SCL (Scene Classification Layer) 场景分类去云
  // 剔除：3(云影), 8(中概率云), 9(高概率云), 10(薄卷云), 11(雪/冰)
  var scl = image.select('SCL');
  var maskSCL = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  
  // 结合两层掩膜
  var combinedMask = maskQA.and(maskSCL);
  return image.updateMask(combinedMask).divide(10000);
};

var ndviCollection = sentinel2.map(function(img) {
  var masked = maskS2clouds(img);
  var ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return masked.addBands(ndvi).copyProperties(img, ['system:time_start', 'system:index']);
}).select(['NDVI']);

// ==============================================================================
// 统一输出合并图表 (用于一键 CSV 导出)
// ==============================================================================
// 既然需要做长期时序分析对比，最好的办法是把所有区域合并成一个FeatureCollection多序列输出
var roiCollection = ee.FeatureCollection([
  ee.Feature(sprawlZone, {label: 'Sprawl_Zone_Core'}),
  ee.Feature(controlZone, {label: 'Control_Zone'}),
  ee.Feature(sensitivity['Sprawl_North'], {label: 'Sprawl_North'}),
  ee.Feature(sensitivity['Sprawl_South'], {label: 'Sprawl_South'}),
  ee.Feature(sensitivity['Sprawl_East'], {label: 'Sprawl_East'}),
  ee.Feature(sensitivity['Sprawl_West'], {label: 'Sprawl_West'})
]);

var consolidatedChart = ui.Chart.image.seriesByRegion({
  imageCollection: ndviCollection,
  regions: roiCollection,
  reducer: ee.Reducer.mean(),
  band: 'NDVI',
  scale: 10,
  xProperty: 'system:time_start',
  seriesProperty: 'label'
}).setOptions({
  title: 'Consolidated NDVI Time Series (Sprawl vs Control & Cardinal Points)',
  vAxis: {title: 'NDVI', min: 0, max: 0.8},
  lineWidth: 1, 
  pointSize: 2,
  series: {
    0: {color: '#FF0000', lineWidth: 2, pointSize: 3}, // Sprawl_Core (Red bold)
    1: {color: '#00FF00', lineWidth: 2, pointSize: 3}, // Control (Green bold)
    2: {color: '#FFAAAA'}, // North (Light red)
    3: {color: '#FFAAAA'}, // South 
    4: {color: '#FFAAAA'}, // East
    5: {color: '#FFAAAA'}  // West
  }
});

print("【ACTION REQUIRED】 Click the pop-out arrow in the top right of this chart to download the single 'ee-chart.csv'");
print(consolidatedChart);

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