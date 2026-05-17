CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_metric_history` AS
SELECT
  site_id,
  site_name,
  profile,
  month,
  metric,
  current_value,
  baseline_median,
  robust_z_score,
  classification,
  direction,
  confidence,
  disposition,
  run_timestamp
FROM
  `sentry-v.sentry_v.metric_records`
ORDER BY
  site_id ASC,
  metric ASC,
  month DESC;