CREATE OR REPLACE VIEW `sentry-v.sentry_v.v_site_monthly_summary` AS
SELECT
  site_id,
  site_name,
  profile,
  month,
  ndvi_classification,
  ndmi_classification,
  phenophase_status,
  precipitation_classification,
  fusion_disposition,
  hypothesis,
  run_timestamp
FROM
  `sentry-v.sentry_v.fusion_summaries`
ORDER BY
  month DESC,
  site_id ASC;