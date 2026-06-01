CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_client_signal_feed` AS
SELECT
  site_id,
  site_name,
  profile,
  month,
  month AS reporting_month,

  fusion_disposition,
  climate_review_cue,

  CASE
    WHEN fusion_disposition = 'reportable_signal' THEN 'Review Required'
    WHEN fusion_disposition = 'watch_signal' THEN 'Watch'
    WHEN fusion_disposition = 'routine_log' THEN 'Routine Log'
    WHEN fusion_disposition = 'incomplete_data' THEN 'Incomplete Data'
    ELSE 'Review'
  END AS review_status,

  CASE
    WHEN fusion_disposition = 'reportable_signal' THEN TRUE
    WHEN fusion_disposition = 'watch_signal' THEN TRUE
    ELSE FALSE
  END AS active_signal,

  CASE
    WHEN fusion_disposition = 'reportable_signal' THEN 1
    WHEN fusion_disposition = 'watch_signal' THEN 2
    WHEN fusion_disposition = 'routine_log' THEN 3
    ELSE 4
  END AS priority_rank,

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

  CASE
    WHEN climate_review_cue = 'rainfall_moisture_context_review_cue'
      THEN 'Higher-than-expected vegetation activity with rainfall/moisture-context support.'
    WHEN climate_review_cue = 'atmospheric_demand_moisture_stress_review_cue'
      THEN 'Lower vegetation and canopy moisture signals with elevated atmospheric demand context.'
    WHEN climate_review_cue = 'warm_but_not_thirsty_context'
      THEN 'Thermal context is elevated, but atmospheric moisture demand remains near expected levels.'
    WHEN climate_review_cue = 'possible_non_climate_disturbance_review_cue'
      THEN 'Vegetation change is not strongly supported by rainfall or atmospheric demand context.'
    WHEN climate_review_cue = 'resilience_or_possible_irrigation_context'
      THEN 'Vegetation appears stable despite elevated atmospheric demand.'
    WHEN fusion_disposition = 'routine_log'
      THEN 'Vegetation activity and canopy moisture are within expected seasonal ranges.'
    WHEN fusion_disposition = 'watch_signal'
      THEN 'Watch-level vegetation signal detected; review for persistence.'
    WHEN fusion_disposition = 'reportable_signal'
      THEN 'Reportable vegetation signal detected; field or imagery review is warranted.'
    ELSE 'Monitoring summary available.'
  END AS main_takeaway,

  CASE
    WHEN climate_review_cue = 'rainfall_moisture_context_review_cue'
      THEN 'Review recent imagery, rainfall context, drainage, saturated soils, flooding, storm effects, or favorable moisture support before interpretation.'
    WHEN climate_review_cue = 'atmospheric_demand_moisture_stress_review_cue'
      THEN 'Review field conditions for possible moisture stress, drought pressure, canopy drying, or persistent low vegetation response.'
    WHEN climate_review_cue = 'possible_non_climate_disturbance_review_cue'
      THEN 'Review imagery for local disturbance, mowing, clearing, pest damage, site management, or data quality context.'
    WHEN fusion_disposition = 'routine_log'
      THEN 'Routine log. No immediate field review required.'
    WHEN fusion_disposition = 'watch_signal'
      THEN 'Review next monthly run for persistence and compare with imagery or field notes.'
    WHEN fusion_disposition = 'reportable_signal'
      THEN 'Review imagery and field conditions before interpretation.'
    ELSE 'Review available context before interpretation.'
  END AS recommended_action,

  ndvi_classification,
  ndmi_classification,
  phenophase_status,
  precipitation_classification,

  climate_context_available,
  temperature_classification,
  vpd_classification,
  eto_classification,
  gridmet_precipitation_classification,

  hypothesis,
  run_timestamp

FROM
  `sentry-v.sentry_v.fusion_summaries`

ORDER BY
  month DESC,
  priority_rank ASC,
  site_id ASC;
