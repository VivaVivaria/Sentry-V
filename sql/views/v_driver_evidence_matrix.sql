CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_driver_evidence_matrix` AS

SELECT
  site_id,
  site_name,
  profile,
  month,
  1 AS evidence_order,
  'ndvi' AS evidence_key,
  'NDVI' AS evidence_label,
  'Vegetation Greenness' AS evidence_group,
  ndvi_classification AS classification,
  ndvi_direction AS direction,
  ndvi_value AS evidence_value,
  ndvi_robust_z_score AS robust_z_score,
  'index' AS units,
  CASE
    WHEN ndvi_classification = 'unusual' THEN 'Unusual vegetation activity'
    WHEN ndvi_classification = 'watch' THEN 'Watch-level vegetation activity'
    WHEN ndvi_classification = 'normal' THEN 'Vegetation activity within expected range'
    ELSE 'Vegetation activity context'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  2 AS evidence_order,
  'ndmi' AS evidence_key,
  'NDMI' AS evidence_label,
  'Canopy Moisture' AS evidence_group,
  ndmi_classification AS classification,
  ndmi_direction AS direction,
  ndmi_value AS evidence_value,
  ndmi_robust_z_score AS robust_z_score,
  'index' AS units,
  CASE
    WHEN ndmi_classification = 'unusual' THEN 'Unusual canopy moisture signal'
    WHEN ndmi_classification = 'watch' THEN 'Watch-level canopy moisture signal'
    WHEN ndmi_classification = 'normal' THEN 'Canopy moisture within expected range'
    ELSE 'Canopy moisture context'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  3 AS evidence_order,
  'phenophase' AS evidence_key,
  'Phenophase' AS evidence_label,
  'Seasonal Timing' AS evidence_group,
  phenophase_status AS classification,
  NULL AS direction,
  CAST(NULL AS FLOAT64) AS evidence_value,
  CAST(NULL AS FLOAT64) AS robust_z_score,
  NULL AS units,
  CASE
    WHEN phenophase_status = 'expected' THEN 'Seasonal timing appears expected'
    WHEN phenophase_status = 'early' THEN 'Seasonal timing appears early'
    WHEN phenophase_status = 'delayed' THEN 'Seasonal timing appears delayed'
    ELSE 'Seasonal timing uncertain'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  4 AS evidence_order,
  'chirps_precipitation' AS evidence_key,
  'CHIRPS Precipitation' AS evidence_label,
  'Precipitation' AS evidence_group,
  precipitation_classification AS classification,
  CASE
    WHEN precipitation_robust_z_score > 0.5 THEN 'higher_than_expected'
    WHEN precipitation_robust_z_score < -0.5 THEN 'lower_than_expected'
    ELSE 'near_expected'
  END AS direction,
  precipitation_current_total_mm AS evidence_value,
  precipitation_robust_z_score AS robust_z_score,
  'mm' AS units,
  CASE
    WHEN precipitation_classification = 'above_normal' THEN 'Above-normal precipitation context'
    WHEN precipitation_classification = 'below_normal' THEN 'Below-normal precipitation context'
    WHEN precipitation_classification = 'near_normal' THEN 'Near-normal precipitation context'
    ELSE 'Precipitation context limited'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  5 AS evidence_order,
  'temperature_mean_c' AS evidence_key,
  'Mean Temperature' AS evidence_label,
  'Thermal Context' AS evidence_group,
  temperature_classification AS classification,
  temperature_direction AS direction,
  temperature_value_c AS evidence_value,
  temperature_robust_z_score AS robust_z_score,
  'C' AS units,
  CASE
    WHEN temperature_classification = 'above_normal' THEN 'Above-normal thermal context'
    WHEN temperature_classification = 'near_normal' THEN 'Near-normal thermal context'
    WHEN temperature_classification = 'below_normal' THEN 'Below-normal thermal context'
    ELSE 'Thermal context limited'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  6 AS evidence_order,
  'vpd_mean_kpa' AS evidence_key,
  'Vapor Pressure Deficit' AS evidence_label,
  'Atmospheric Thirst' AS evidence_group,
  vpd_classification AS classification,
  vpd_direction AS direction,
  vpd_value_kpa AS evidence_value,
  vpd_robust_z_score AS robust_z_score,
  'kPa' AS units,
  CASE
    WHEN vpd_classification = 'high_demand' THEN 'Elevated atmospheric moisture demand'
    WHEN vpd_classification = 'normal_demand' THEN 'Atmospheric moisture demand near expected'
    WHEN vpd_classification = 'low_demand' THEN 'Atmospheric moisture demand below expected'
    ELSE 'Atmospheric demand context limited'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  7 AS evidence_order,
  'eto_total_mm' AS evidence_key,
  'Reference Evapotranspiration' AS evidence_label,
  'Evaporative Demand' AS evidence_group,
  eto_classification AS classification,
  eto_direction AS direction,
  eto_value_mm AS evidence_value,
  eto_robust_z_score AS robust_z_score,
  'mm' AS units,
  CASE
    WHEN eto_classification = 'high_demand' THEN 'Elevated evaporative demand'
    WHEN eto_classification = 'normal_demand' THEN 'Evaporative demand near expected'
    WHEN eto_classification = 'low_demand' THEN 'Evaporative demand below expected'
    ELSE 'Evaporative demand context limited'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

UNION ALL

SELECT
  site_id,
  site_name,
  profile,
  month,
  8 AS evidence_order,
  'gridmet_precipitation' AS evidence_key,
  'gridMET Precipitation' AS evidence_label,
  'Precipitation Cross-Check' AS evidence_group,
  gridmet_precipitation_classification AS classification,
  gridmet_precipitation_direction AS direction,
  gridmet_precipitation_value_mm AS evidence_value,
  gridmet_precipitation_robust_z_score AS robust_z_score,
  'mm' AS units,
  CASE
    WHEN gridmet_precipitation_classification = 'above_normal' THEN 'gridMET supports wetter-than-normal context'
    WHEN gridmet_precipitation_classification = 'near_normal' THEN 'gridMET precipitation cross-check is near normal'
    WHEN gridmet_precipitation_classification = 'below_normal' THEN 'gridMET supports drier-than-normal context'
    ELSE 'gridMET precipitation cross-check limited'
  END AS evidence_summary
FROM
  `sentry-v.sentry_v.fusion_summaries`

ORDER BY
  site_id ASC,
  month DESC,
  evidence_order ASC;
