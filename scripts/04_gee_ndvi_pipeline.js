// Shepperton NDVI
// 1. 宏观缓冲带 (1km)
var shepperton = ee.Geometry.Point([-0.4640, 51.4065]); 
var analysisBuffer = shepperton.buffer(1000);

// 2. 微观灾区
var sprawlZone = ee.Geometry.Point([-0.469366, 51.410315]).buffer(100);

var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(analysisBuffer)
  .filterDate('2018-01-01', '2026-03-04')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20));

function maskS2clouds(image) {
  var qa = image.select('QA60');
  var cloudBitMask = 1 << 10;
  var cirrusBitMask = 1 << 11;
  var mask = qa.bitwiseAnd(cloudBitMask).eq(0).and(qa.bitwiseAnd(cirrusBitMask).eq(0));
  return image.updateMask(mask).divide(10000);
}

// 直接在原图上计算 NDVI
var ndviCollection = sentinel2.map(function(img) {
  var masked = maskS2clouds(img);
  var ndvi = masked.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return masked.addBands(ndvi).copyProperties(img, ['system:time_start', 'system:index']);
}).select('NDVI');

// 只统计 Sprawl Zone 的 NDVI 均值
var tsChart = ui.Chart.image.series(ndviCollection, sprawlZone, ee.Reducer.mean(), 10)
  .setOptions({
    title: 'Micro-Scale Audit: NDVI Collapse in the Sprawl Zone (2018-2026)',
    vAxis: {title: 'NDVI (Chlorophyll Reflectance)', min: 0, max: 0.8},
    hAxis: {title: 'Date'},
    lineWidth: 2,
    pointSize: 3,
    colors: ['#FF3333'] // 把折线变成警示的血红色
  });
print(tsChart);

// 损失图（2018基线 vs 2026现状）
var baseline2018 = ndviCollection.filterDate('2018-01-01', '2019-01-01').mean();
var recent2026 = ndviCollection.filterDate('2025-09-01', '2026-03-04').mean();
var loss = baseline2018.subtract(recent2026).rename('NDVI_Loss');

Map.centerObject(shepperton, 15);

// 图层1：1km范围的损失图
Map.addLayer(loss.clip(analysisBuffer), 
             {min:-0.3, max:0.3, palette:['darkgreen','green','white','red','darkred']}, 
             'Macro Level: Loss & Gain (Red=Sprawl)');

// 图层2：标出折线图统计的微观重灾区
Map.addLayer(sprawlZone, {color: 'red'}, 'Micro Level: Sprawl Zone Target', false);