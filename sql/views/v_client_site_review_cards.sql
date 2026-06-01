CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_client_site_review_cards` AS
SELECT
  site_id,
  site_name,
  profile,
  month,
  month AS reporting_month,

  CASE
    WHEN fusion_disposition = 'reportable_signal' THEN 'Review Required'
    WHEN fusion_disposition = 'watch_signal' THEN 'Watch'
    WHEN fusion_disposition = 'routine_log' THEN 'Routine Log'
    WHEN fusion_disposition = 'incomplete_data' THEN 'Incomplete Data'
    ELSE 'Review'
  END AS review_status,

  CASE
    WHEN climate_review_cue = 'rainfall_moisture_context_review_cue'
      THEN 'Rainfall / moisture-context review cue'
    WHEN climate_review_cue = 'atmospheric_demand_moisture_stress_review_cue'
      THEN 'Atmospheric demand / moisture-stress review cue'
    WHEN climate_review_cue = 'warm_but_not_thirsty_context'
      THEN 'Warm month, normal atmospheric demand'
    WHEN climate_review_cue = 'possible_non_climate_disturbance_review_cue'
      THEN 'Possible non-climate disturbance review cue'
    WHEN climate_review_cue = 'resilience_or_possible_irrigation_context'
      THEN 'Resilience / possible irrigation context'
    WHEN climate_review_cue = 'general_climate_context'
      THEN 'General climate context'
    ELSE 'General review cue'
  END AS review_cue_label,

  climate_review_cue,
  fusion_disposition,

  ndvi_value,
  ndvi_classification,
  ndvi_direction,
  ndvi_robust_z_score,

  ndmi_value,
  ndmi_classification,
  ndmi_direction,
  ndmi_robust_z_score,

  phenophase_status,
  phenophase_closest_month,

  precipitation_classification,
  precipitation_current_total_mm,
  precipitation_baseline_median_mm,
  precipitation_robust_z_score,

  climate_context_available,

  temperature_classification,
  temperature_direction,
  temperature_value_c,
  temperature_robust_z_score,

  vpd_classification,
  vpd_direction,
  vpd_value_kpa,
  vpd_robust_z_score,

  eto_classification,
  eto_direction,
  eto_value_mm,
  eto_robust_z_score,

  gridmet_precipitation_classification,
  gridmet_precipitation_direction,
  gridmet_precipitation_value_mm,
  gridmet_precipitation_robust_z_score,

  CASE
    WHEN climate_review_cue = 'rainfall_moisture_context_review_cue'
      THEN 'Higher-than-expected vegetation activity with rainfall/moisture-context support.'
    WHEN climate_review_cue = 'atmospheric_demand_moisture_stress_review_cue'
      THEN 'Vegetation and canopy moisture signals may warrant review under elevated atmospheric demand.'
    WHEN climate_review_cue = 'warm_but_not_thirsty_context'
      THEN 'Warmer-than-normal month, but atmospheric moisture demand remains near expected levels.'
    WHEN fusion_disposition = 'routine_log'
      THEN 'Site conditions are currently consistent with routine monitoring.'
    ELSE 'Site review summary available.'
  END AS main_takeaway,

  CASE
    WHEN climate_review_cue = 'rainfall_moisture_context_review_cue'
      THEN 'Review recent imagery, rainfall context, drainage, saturated soils, flooding, storm effects, or favorable moisture support before interpretation.'
    WHEN climate_review_cue = 'atmospheric_demand_moisture_stress_review_cue'
      THEN 'Review field conditions for possible moisture stress or canopy drying.'
    WHEN fusion_disposition = 'routine_log'
      THEN 'Routine log. No immediate field review required.'
    WHEN fusion_disposition = 'watch_signal'
      THEN 'Review next monthly run for persistence and compare with imagery or field notes.'
    WHEN fusion_disposition = 'reportable_signal'
      THEN 'Review imagery and field conditions before interpretation.'
    ELSE 'Review available context before interpretation.'
  END AS recommended_action,

  hypothesis,
  run_timestamp

FROM
  `sentry-v.sentry_v.fusion_summaries`

ORDER BY
  month DESC,
  site_id ASC;
