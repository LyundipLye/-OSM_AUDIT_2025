// ==============================================================================
// OSM_AUDIT_2025: LST ANALYSIS (v4 — Triple-Satellite Paired BACI)
// Landsat 7 ETM+ (60m) + Landsat 8 C2 (100m) + Landsat 9 C2 (100m)
// No NDBI masking — pure Paired Before-After-Control-Impact design
// ==============================================================================

// Update END_DATE before each run
var START_DATE = '2015-01-01';
var END_DATE   = '2026-03-15';  // <-- UPDATE ME

// 1. Impact Zone — precise polygon for the newly-constructed parking lot (5 vertices)
// No NDBI masking: directly measure the full temperature transition greenfield -> asphalt
// This is a standard Paired BACI design, eliminating MAUP (Modifiable Areal Unit) issues
var sprawlZone = ee.Geometry.Polygon([[
  [-0.4676848515978538, 51.40882742185046],
  [-0.4669123754015647, 51.409429716784295],
  [-0.46926006378714025, 51.41065315692719],
  [-0.4703222185570377, 51.40986350085904],
  [-0.4676848515978538, 51.40882742185046]
]]);
var macroRegion = sprawlZone.buffer(1500);

// 2. Control Zone (identical coordinates to NDVI pipeline)
var controlZone = ee.Geometry.Point([-0.4104592619093905, 51.40739479750269]).buffer(150);

// Bounding rectangle encompassing both zones
var combinedBounds = ee.Geometry.Rectangle([-0.48, 51.40, -0.40, 51.42]);

// ==============================================================================
// Landsat 7 ETM+ (60m thermal, 2003+ has SLC-off but reduceRegion handles gaps)
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
// Landsat 8 OLI/TIRS (100m thermal infrared)
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
// Landsat 9 OLI-2/TIRS-2 (100m thermal infrared, 2022+)
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
// Triple-Satellite Merge
// ==============================================================================
var lstCollection = landsat7.map(prepL7)
  .merge(landsat8.map(prepL8))
  .merge(landsat9.map(prepL9))
  .select(['LST_Celsius'])
  .sort('system:time_start');

print('Total scenes (L7+L8+L9):', lstCollection.size());

// ==============================================================================
// Time series extraction — Paired BACI (no NDBI mask, full-pixel temperature)
// ==============================================================================
var roiCollection = ee.FeatureCollection([
  ee.Feature(sprawlZone, {label: 'Sprawl_Zone_Core'}),
  ee.Feature(controlZone, {label: 'Control_Zone'})
]);

var extractStats = function(image) {
  // Paired BACI: no NDBI masking, direct full-pixel temperature measurement
  // Pre-construction = greenfield temperature, post = asphalt, difference = causal effect
  var lst = image.select('LST_Celsius');
  
  var spMean = lst.reduceRegion({
    reducer: ee.Reducer.mean(), geometry: sprawlZone, scale: 30, bestEffort: true
  });
  var spStd = lst.reduceRegion({
    reducer: ee.Reducer.stdDev(), geometry: sprawlZone, scale: 30, bestEffort: true
  });
  var ctMean = lst.reduceRegion({
    reducer: ee.Reducer.mean(), geometry: controlZone, scale: 30, bestEffort: true
  });
  var ctStd = lst.reduceRegion({
    reducer: ee.Reducer.stdDev(), geometry: controlZone, scale: 30, bestEffort: true
  });
  
  return ee.Feature(null, {
    'Sprawl_Zone_Core_mean': spMean.get('LST_Celsius'),
    'Sprawl_Zone_Core_std':  spStd.get('LST_Celsius'),
    'Control_Zone_mean':     ctMean.get('LST_Celsius'),
    'Control_Zone_std':      ctStd.get('LST_Celsius')
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
  title: 'LST Analytics: Triple-Satellite (L7+L8+L9) Paired BACI',
  vAxis: {title: 'LST Celsius'},
  pointSize: 3,
  dataOpacity: 0.6
});

print("[ACTION REQUIRED]");
print("1. Triple-satellite fusion (L7+L8+L9), no NDBI masking (pure Paired BACI).");
print("2. Impact Zone: full-pixel mean temperature. Control Zone: stable greenbelt.");
print("3. Click the pop-out arrow -> Download CSV.");
print("4. Save as: data/raw_telemetry/ee-chart_lst.csv");
print(consolidatedChart);

// ==============================================================================
// UHI Anomaly: Multi-year summer composite (triple-satellite data)
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
// Map Visualisation
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
