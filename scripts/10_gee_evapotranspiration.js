// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT - PHASE V
// Evapotranspiration (ET) Collapse: The Metabolic Rift Physical Proxy
// Demonstrates that the UHI is driven by the total loss of latent heat flux
// Data: MODIS/061/MOD16A2GF (8-Day, 500m)
// ==============================================================================

var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';

// 1. Impact Zone — 对于 MODIS 的 500m 分辨率，我们必须使用 1km² 的 VP 开发多边形
// 才能捕获足够多（约 4 个）有效像元。单单停车场太小了。
var sprawlZone = ee.Geometry.Polygon([[
  [-0.4758927487043363, 51.41217153384681],
  [-0.47417613493480504, 51.409200313379166],
  [-0.4710862301496488, 51.40735324117383],
  [-0.47027083860912144, 51.405479323562865],
  [-0.4644343517927152, 51.40454233596011],
  [-0.45975657927074254, 51.40778155441695],
  [-0.4637047909406644, 51.40791540148267],
  [-0.4710862301496488, 51.412225067579875],
  [-0.4758927487043363, 51.41217153384681]
]]);

// 2. 对照区（未开发公园）
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(500);

// ==============================================================================
// 提取 MODIS ET 数据
// ==============================================================================
var modisET = ee.ImageCollection('MODIS/061/MOD16A2GF')
  .filterDate(START_DATE, END_DATE)
  .select('ET');

// scale factor 0.1 -> kg/m^2/8day (or mm/8day)
function prepET(image) {
  var et = image.select('ET').multiply(0.1).rename('ET_mm_8day');
  return et.copyProperties(image, ['system:time_start']);
}

var etCollection = modisET.map(prepET);

// ==============================================================================
// 转换为时间序列 CSV 的提取函数
// ==============================================================================
var extractStats = function(image) {
  var spMean = image.reduceRegion({
    reducer: ee.Reducer.mean(), geometry: sprawlZone, scale: 500, bestEffort: true
  });
  var ctMean = image.reduceRegion({
    reducer: ee.Reducer.mean(), geometry: controlZone, scale: 500, bestEffort: true
  });
  
  return ee.Feature(null, {
    'Sprawl_ET_mean': spMean.get('ET_mm_8day'),
    'Control_ET_mean': ctMean.get('ET_mm_8day')
  }).set('system:time_start', image.get('system:time_start'));
};

var timeSeriesData = etCollection.map(extractStats);

var etChart = ui.Chart.feature.byFeature({
  features: timeSeriesData,
  xProperty: 'system:time_start',
  yProperties: ['Sprawl_ET_mean', 'Control_ET_mean']
})
.setChartType('LineChart')
.setOptions({
  title: 'MODIS Actual Evapotranspiration (Latent Heat Flux Proxy)',
  vAxis: {title: 'ET (mm / 8-day)'},
  lineWidth: 1,
  pointSize: 2,
  colors: ['#FF8C00', '#33CC33'] // Orange for Sprawl, Green for Control
});

print("【ACTION REQUIRED】");
print("1. MODIS 8-Day Evapotranspiration Time Series.");
print("2. Click the pop-out arrow -> Download CSV.");
print("3. MUST Save as: data/raw_telemetry/ee-chart_et.csv");
print(etChart);

// ==============================================================================
// 可视化
// ==============================================================================
Map.centerObject(sprawlZone, 13);
Map.setOptions('SATELLITE');
Map.addLayer(sprawlZone, {color: 'orange'}, 'Impact Zone (VP Full)');
Map.addLayer(controlZone, {color: 'green'}, 'Control Zone');
