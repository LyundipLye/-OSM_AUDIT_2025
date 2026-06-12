// ==============================================================================
// OSM_AUDIT_2025: NDVI SPATIAL AUDIT
// Sentinel-2 NDVI Time Series + Control Zone + Sensitivity Analysis
// ==============================================================================

// ⚠️ Update END_DATE before each run
var START_DATE = '2018-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 1. Audit zone coordinates
var shepperton = ee.Geometry.Point([-0.4640, 51.4065]); 
var analysisBuffer = shepperton.buffer(1000);

// 2. Sprawl Zone (newly-constructed parking area, corresponding to EIA Zone C centre)
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(100);

// 3. Control Zone: stable undeveloped greenbelt toward Sunbury (~2km from Shepperton, no major development)
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(100);

// Sentinel-2
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(analysisBuffer)
  .filterDate(START_DATE, END_DATE)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

var maskS2clouds = function(image) {
  // 1. Basic QA60 cloud mask
  var qa = image.select('QA60');
  var maskQA = qa.bitwiseAnd(1 << 10).eq(0).and(qa.bitwiseAnd(1 << 11).eq(0));
  
  // 2. Enhanced SCL (Scene Classification Layer) cloud filtering
  // Exclude: 3(cloud shadow), 8(medium-probability cloud), 9(high-probability cloud), 10(thin cirrus), 11(snow/ice)
  var scl = image.select('SCL');
  var maskSCL = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
  
  // Combine both mask layers
  var combinedMask = maskQA.and(maskSCL);
  return image.updateMask(combinedMask).divide(10000);
};

var ndviCollection = sentinel2.map(function(img) {
  var masked = maskS2clouds(img);
  var ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return masked.addBands(ndvi).copyProperties(img, ['system:time_start', 'system:index']);
}).select(['NDVI']);

// ==============================================================================
// Consolidated chart output (for one-click CSV export)
// ==============================================================================
// Merge all zones into a single FeatureCollection for multi-series time series output
var roiCollection = ee.FeatureCollection([
  ee.Feature(sprawlZone, {label: 'Sprawl_Zone_Core'}),
  ee.Feature(controlZone, {label: 'Control_Zone'})
]);

// Compute variance (stdDev) and export as Wide Format
var extractStats = function(image) {
  var stats = image.reduceRegions({
    collection: roiCollection,
    reducer: ee.Reducer.mean().combine({
      reducer2: ee.Reducer.stdDev(),
      sharedInputs: true
    }),
    scale: 10
  });
  
  // Safe extraction: use filter + first to avoid dynamic attribute type loss
  var sp = ee.Feature(stats.filter(ee.Filter.eq('label', 'Sprawl_Zone_Core')).first());
  var ct = ee.Feature(stats.filter(ee.Filter.eq('label', 'Control_Zone')).first());
  
  // Preserve system:time_start to prevent chart x-axis recognition errors
  return ee.Feature(null, {
    'Sprawl_Zone_Core_mean': sp.get('mean'),
    'Sprawl_Zone_Core_std': sp.get('stdDev'),
    'Control_Zone_mean': ct.get('mean'),
    'Control_Zone_std': ct.get('stdDev')
  }).set('system:time_start', ee.Number(image.get('system:time_start')));
};

// Wide-format FeatureCollection: one row per image, containing mean and stdDev for all zones
var timeSeriesData = ndviCollection.map(extractStats);

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
  title: 'NDVI Analytics Extraction Ready (with UQ StdDev Wide-Format)',
  vAxis: {title: 'NDVI'},
  pointSize: 2,
  dataOpacity: 0.5
});

print("[ACTION REQUIRED]");
print("1. We now explicitly export WIDE-FORMAT telemetry including Pixel StdDev.");
print("2. Click the pop-out arrow in the top right of this chart -> Download CSV.");
print("3. MUST Save as: data/raw_telemetry/ee-chart_ndvi.csv");
print(consolidatedChart);

// ==============================================================================
// Loss map (2018 baseline vs. recent)
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