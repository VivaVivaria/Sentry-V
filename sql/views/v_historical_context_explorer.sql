CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_historical_context_explorer` AS

-- Vegetation metrics: NDVI / NDMI
SELECT
  site_id,
  site_name,
  profile,
  month,
  metric AS metric_key,

  CASE
    WHEN metric = 'NDVI' THEN 'NDVI'
    WHEN metric = 'NDMI' THEN 'NDMI'
    ELSE metric
  END AS metric_label,

  CASE
    WHEN metric = 'NDVI' THEN 'Vegetation Greenness'
    WHEN metric = 'NDMI' THEN 'Canopy Moisture'
    ELSE 'Vegetation Metric'
  END AS metric_description,

  'vegetation' AS metric_group,
  current_value,
  baseline_median AS historical_baseline,
  robust_z_score,
  classification,
  direction,
  confidence,
  'index' AS units,
  'Sentinel-2 SR Harmonized' AS source_dataset,

  CASE
    WHEN metric = 'NDVI' THEN 1
    WHEN metric = 'NDMI' THEN 2
    ELSE 99
  END AS metric_sort_order,

  CASE
    WHEN metric = 'NDVI' THEN 'Vegetation greenness index'
    WHEN metric = 'NDMI' THEN 'Canopy moisture index'
    ELSE 'Metric value'
  END AS chart_axis_label,

  TRUE AS current_month_marker

FROM
  `sentry-v.sentry_v.metric_records`

WHERE
  metric IN ('NDVI', 'NDMI')

UNION ALL

-- Primary precipitation context from CHIRPS
SELECT
  site_id,
  site_name,
  profile,
  month,
  'chirps_precipitation_mm' AS metric_key,
  'Precipitation' AS metric_label,
  'Monthly precipitation total' AS metric_description,
  'precipitation' AS metric_group,
  precipitation_current_total_mm AS current_value,
  precipitation_baseline_median_mm AS historical_baseline,
  precipitation_robust_z_score AS robust_z_score,
  precipitation_classification AS classification,

  CASE
    WHEN precipitation_robust_z_score > 0.5 THEN 'higher_than_expected'
    WHEN precipitation_robust_z_score < -0.5 THEN 'lower_than_expected'
    ELSE 'near_expected'
  END AS direction,

  'context' AS confidence,
  'mm' AS units,
  'CHIRPS Daily' AS source_dataset,
  3 AS metric_sort_order,
  'Monthly precipitation in mm' AS chart_axis_label,
  TRUE AS current_month_marker

FROM
  `sentry-v.sentry_v.fusion_summaries`

WHERE
  precipitation_current_total_mm IS NOT NULL

UNION ALL

-- gridMET climate drivers
SELECT
  site_id,
  site_name,
  NULL AS profile,
  month,
  driver AS metric_key,
  driver_label AS metric_label,

  CASE
    WHEN driver = 'temperature_mean_c' THEN 'Mean thermal context'
    WHEN driver = 'vpd_mean_kpa' THEN 'Atmospheric thirst / vapor pressure deficit'
    WHEN driver = 'eto_total_mm' THEN 'Reference evapotranspiration'
    WHEN driver = 'precip_total_mm' THEN 'gridMET precipitation cross-check'
    ELSE 'Climate driver'
  END AS metric_description,

  CASE
    WHEN driver = 'temperature_mean_c' THEN 'thermal'
    WHEN driver = 'vpd_mean_kpa' THEN 'moisture_demand'
    WHEN driver = 'eto_total_mm' THEN 'evaporative_demand'
    WHEN driver = 'precip_total_mm' THEN 'precipitation_cross_check'
    ELSE 'climate'
  END AS metric_group,

  current_value,
  baseline_median AS historical_baseline,
  robust_z_score,
  classification,
  direction,
  confidence,
  units,
  source_dataset,

  CASE
    WHEN driver = 'temperature_mean_c' THEN 4
    WHEN driver = 'vpd_mean_kpa' THEN 5
    WHEN driver = 'eto_total_mm' THEN 6
    WHEN driver = 'precip_total_mm' THEN 7
    ELSE 99
  END AS metric_sort_order,

  CASE
    WHEN driver = 'temperature_mean_c' THEN 'Mean temperature in °C'
    WHEN driver = 'vpd_mean_kpa' THEN 'Vapor pressure deficit in kPa'
    WHEN driver = 'eto_total_mm' THEN 'Reference evapotranspiration in mm'
    WHEN driver = 'precip_total_mm' THEN 'gridMET precipitation in mm'
    ELSE 'Climate driver value'
  END AS chart_axis_label,

  TRUE AS current_month_marker

FROM
  `sentry-v.sentry_v.climate_driver_records`

ORDER BY
  site_id ASC,
  metric_sort_order ASC,
  month DESC;
