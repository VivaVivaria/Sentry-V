CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_reportable_signals` AS
SELECT
  site_id,
  site_name,
  profile,
  month,
  fusion_disposition,
  ndvi_classification,
  ndmi_classification,
  phenophase_status,
  precipitation_classification,
  hypothesis,
  run_timestamp
FROM
  `sentry-v.sentry_v.fusion_summaries`
WHERE
  fusion_disposition != 'routine_log'
ORDER BY
  month DESC,
  site_id ASC;