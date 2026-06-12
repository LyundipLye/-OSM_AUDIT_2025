// ==============================================================================
// OSM_AUDIT_2025: THERMODYNAMIC SPATIAL AUDIT - PHASE IV
// Spatial Transect Decay (LST Distance Gradient)
// Proves Spatial Advection / Spillover Effect of the Urban Heat Island
// ==============================================================================

// ⚠️ Update END_DATE before each run if needed, though this uses fixed summer composites
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';

// 1. Impact Zone — precise parking lot polygon (the "point source" of heat)
var sprawlZone = ee.Geometry.Polygon([[
  [-0.4676848515978538,51.40882742185046],
  [-0.4669123754015647,51.409429716784295],
  [-0.46926006378714025,51.41065315692719],
  [-0.4703222185570377,51.40986350085904],
  [-0.4676848515978538,51.40882742185046]
]]);

var maxDistance = 800; // Maximum analysis distance (meters)
var stepSize = 50;     // Ring bandwidth: 50 metres per annulus

var macroRegion = sprawlZone.buffer(maxDistance + 200);

// Bounding rectangle for image filtering
var combinedBounds = ee.Geometry.Rectangle([-0.49, 51.39, -0.45, 51.43]);

// ==============================================================================
// Image fusion: Landsat 7 + 8 + 9 (no NDBI masking, preserves true radiance)
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
// Extract summer (JJA) composite mean (eliminates single-day weather anomalies)
// ==============================================================================
var summerPre = lstCollection
  .filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2016-01-01', '2019-01-01')
  .mean();

var summerPost = lstCollection
  .filter(ee.Filter.calendarRange(6, 8, 'month'))
  .filterDate('2023-01-01', '2026-01-01')
  .mean();

// Combine into a single Image for extraction
var lstComposite = ee.Image([
  summerPre.rename('Pre_LST_mean'),
  summerPost.rename('Post_LST_mean')
]);

// ==============================================================================
// Build concentric annular buffers
// ==============================================================================
var distances = ee.List.sequence(0, maxDistance - stepSize, stepSize);

// Distance 0 = the Impact Zone itself (core)
var coreFeature = ee.Feature(sprawlZone, {
  'Distance_m': 0,
});

// Generate outer annular buffer rings
var ringsList = distances.map(function(d) {
  var dNum = ee.Number(d);
  var inner = sprawlZone.buffer(dNum.max(0.1));
  var outer = sprawlZone.buffer(dNum.add(stepSize));
  var ring = outer.difference(inner); // Cut out the donut shape
  
  // For the 0-50m ring, label its representative distance as 25m
  return ee.Feature(ring, {
    'Distance_m': dNum.add(stepSize / 2)
  });
});

// Merge core and annular zones
var transectZones = ee.FeatureCollection(ee.List([coreFeature]).cat(ringsList));

// ==============================================================================
// Extract mean LST per annular ring
// ==============================================================================
var extractDecay = function(feature) {
  var stats = lstComposite.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: feature.geometry(),
    scale: 30,  // 30m extraction; GEE auto-resamples from 100m native LST
    bestEffort: true
  });
  
  return feature.set({
    'Pre_LST_mean': stats.get('Pre_LST_mean'),
    'Post_LST_mean': stats.get('Post_LST_mean')
  });
};

var decayData = transectZones.map(extractDecay);

// ==============================================================================
// Chart output
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

print("[ACTION REQUIRED]");
print("1. Summer composite (JJA) spatial advection decay curve.");
print("2. Click the pop-out arrow -> Download CSV.");
print("3. MUST Save as: data/raw_telemetry/ee-chart_decay.csv");
print(decayChart);

// ==============================================================================
// Map visualisation (for screenshots / presentations)
// ==============================================================================
Map.centerObject(sprawlZone, 15);
Map.setOptions('SATELLITE');

// Draw transect ring outlines in white
var empty = ee.Image().byte();
var outline = empty.paint({
  featureCollection: transectZones,
  color: 1,
  width: 1
});
Map.addLayer(outline, {palette: ['FFFFFF']}, 'Transect Rings');

var anomalyVis = {
  min: 25, max: 35, // Absolute temperature range
  palette: ['#313695','#4575b4','#74add1','#abd9e9','#e0f3f8','#ffffbf','#fee090','#fdae61','#f46d43','#d73027','#a50026']
};
Map.addLayer(summerPre.clip(macroRegion), anomalyVis, 'Summer Pre (2016-2018)', false);
Map.addLayer(summerPost.clip(macroRegion), anomalyVis, 'Summer Post (2023-2025)', true);
