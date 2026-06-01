from google.cloud import bigquery

# ---------------------------------------------------------
# TABLE 1: METRIC RECORDS
# ---------------------------------------------------------
METRIC_RECORDS_SCHEMA = [
    bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("site_name", "STRING"),
    bigquery.SchemaField("profile", "STRING"),
    bigquery.SchemaField("month", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("metric", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("current_value", "FLOAT"),
    bigquery.SchemaField("site_metric_stdev", "FLOAT"),
    bigquery.SchemaField("pixel_count", "INTEGER"),
    bigquery.SchemaField("baseline_median", "FLOAT"),
    bigquery.SchemaField("baseline_mad", "FLOAT"),
    bigquery.SchemaField("baseline_years_used", "INTEGER"),
    bigquery.SchemaField("robust_z_score", "FLOAT"),
    bigquery.SchemaField("classification", "STRING"),
    bigquery.SchemaField("direction", "STRING"),
    bigquery.SchemaField("confidence", "STRING"),
    bigquery.SchemaField("images_used", "INTEGER"),
    bigquery.SchemaField("composite_days", "INTEGER"),
    bigquery.SchemaField("composite_support", "STRING"),
    bigquery.SchemaField("spatial_variability_status", "STRING"),
    bigquery.SchemaField("season_status", "STRING"),
    bigquery.SchemaField("disposition", "STRING"),
    bigquery.SchemaField("recommended_action", "STRING"),
    bigquery.SchemaField("artifact_path", "STRING"),
    bigquery.SchemaField("run_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("raw_record_json", "STRING"),
]

# ---------------------------------------------------------
# TABLE 2: FUSION SUMMARIES
# ---------------------------------------------------------
FUSION_SUMMARIES_SCHEMA = [
    bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("site_name", "STRING"),
    bigquery.SchemaField("profile", "STRING"),
    bigquery.SchemaField("month", "STRING", mode="REQUIRED"),

    bigquery.SchemaField("ndvi_classification", "STRING"),
    bigquery.SchemaField("ndvi_direction", "STRING"),
    bigquery.SchemaField("ndvi_value", "FLOAT"),
    bigquery.SchemaField("ndvi_robust_z_score", "FLOAT"),

    bigquery.SchemaField("ndmi_classification", "STRING"),
    bigquery.SchemaField("ndmi_direction", "STRING"),
    bigquery.SchemaField("ndmi_value", "FLOAT"),
    bigquery.SchemaField("ndmi_robust_z_score", "FLOAT"),

    bigquery.SchemaField("phenophase_status", "STRING"),
    bigquery.SchemaField("phenophase_closest_month", "STRING"),

    bigquery.SchemaField("precipitation_classification", "STRING"),
    bigquery.SchemaField("precipitation_current_total_mm", "FLOAT"),
    bigquery.SchemaField("precipitation_baseline_median_mm", "FLOAT"),
    bigquery.SchemaField("precipitation_robust_z_score", "FLOAT"),

    # Phase 11C — Climate-driver fusion fields
    bigquery.SchemaField("climate_context_available", "BOOLEAN"),
    bigquery.SchemaField("climate_review_cue", "STRING"),

    bigquery.SchemaField("temperature_classification", "STRING"),
    bigquery.SchemaField("temperature_direction", "STRING"),
    bigquery.SchemaField("temperature_value_c", "FLOAT"),
    bigquery.SchemaField("temperature_robust_z_score", "FLOAT"),

    bigquery.SchemaField("vpd_classification", "STRING"),
    bigquery.SchemaField("vpd_direction", "STRING"),
    bigquery.SchemaField("vpd_value_kpa", "FLOAT"),
    bigquery.SchemaField("vpd_robust_z_score", "FLOAT"),

    bigquery.SchemaField("eto_classification", "STRING"),
    bigquery.SchemaField("eto_direction", "STRING"),
    bigquery.SchemaField("eto_value_mm", "FLOAT"),
    bigquery.SchemaField("eto_robust_z_score", "FLOAT"),

    bigquery.SchemaField("gridmet_precipitation_classification", "STRING"),
    bigquery.SchemaField("gridmet_precipitation_direction", "STRING"),
    bigquery.SchemaField("gridmet_precipitation_value_mm", "FLOAT"),
    bigquery.SchemaField("gridmet_precipitation_robust_z_score", "FLOAT"),

    bigquery.SchemaField("hypothesis", "STRING"),
    bigquery.SchemaField("fusion_disposition", "STRING"),
    bigquery.SchemaField("artifact_path", "STRING"),
    bigquery.SchemaField("run_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("raw_record_json", "STRING"),
]

# ---------------------------------------------------------
# TABLE 3: RUN LOGS
# ---------------------------------------------------------
RUN_LOGS_SCHEMA = [
    bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("month", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("metric", "STRING"),
    bigquery.SchemaField("status", "STRING"),
    bigquery.SchemaField("started_at", "TIMESTAMP"),
    bigquery.SchemaField("finished_at", "TIMESTAMP"),
    bigquery.SchemaField("artifact_path", "STRING"),
    bigquery.SchemaField("error", "STRING"),
    bigquery.SchemaField("run_log_path", "STRING"),
    bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("raw_record_json", "STRING"),
]

# ---------------------------------------------------------
# TABLE 4: CLIMATE DRIVER RECORDS
# ---------------------------------------------------------
CLIMATE_DRIVER_RECORDS_SCHEMA = [
    bigquery.SchemaField("site_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("site_name", "STRING"),
    bigquery.SchemaField("month", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("driver", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("driver_label", "STRING"),
    bigquery.SchemaField("context_type", "STRING"),
    bigquery.SchemaField("current_value", "FLOAT"),
    bigquery.SchemaField("baseline_median", "FLOAT"),
    bigquery.SchemaField("baseline_mad", "FLOAT"),
    bigquery.SchemaField("baseline_years_used", "INTEGER"),
    bigquery.SchemaField("robust_z_score", "FLOAT"),
    bigquery.SchemaField("classification", "STRING"),
    bigquery.SchemaField("direction", "STRING"),
    bigquery.SchemaField("confidence", "STRING"),
    bigquery.SchemaField("units", "STRING"),
    bigquery.SchemaField("aggregation", "STRING"),
    bigquery.SchemaField("source_dataset", "STRING"),
    bigquery.SchemaField("note", "STRING"),
    bigquery.SchemaField("artifact_path", "STRING"),
    bigquery.SchemaField("run_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("load_timestamp", "TIMESTAMP"),
    bigquery.SchemaField("raw_record_json", "STRING"),
]