import json
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import bigquery

from storage.bigquery_client import PROJECT_ID, DATASET_ID
from storage.schemas import (
    METRIC_RECORDS_SCHEMA,
    FUSION_SUMMARIES_SCHEMA,
    RUN_LOGS_SCHEMA,
    CLIMATE_DRIVER_RECORDS_SCHEMA,
)


OUTPUTS_DIR = Path("outputs")
RUN_LOGS_DIR = OUTPUTS_DIR / "run_logs"
CLIMATE_DRIVERS_DIR = OUTPUTS_DIR / "climate_drivers"


# =========================================================
# TIME + JSON HELPERS
# =========================================================

def utc_now_iso():
    """
    Return current UTC timestamp as ISO string for BigQuery TIMESTAMP fields.
    """
    return datetime.now(timezone.utc).isoformat()


def file_mtime_iso(path):
    """
    Use the local file modified time as a fallback run timestamp.
    """
    timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return timestamp.isoformat()


def read_json(path):
    """
    Read JSON artifact from disk.
    """
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def compact_json(data):
    """
    Store original artifact as compact JSON string.
    """
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def get_table_id(table_name):
    """
    Build full BigQuery table ID.
    """
    return f"{PROJECT_ID}.{DATASET_ID}.{table_name}"


# =========================================================
# PARSERS
# =========================================================

def parse_metric_record(path):
    """
    Convert one NDVI/NDMI status artifact into a BigQuery row.

    One row represents:
    site_id + month + metric
    """
    record = read_json(path)

    row = {
        "site_id": record.get("site_id"),
        "site_name": record.get("site_name"),
        "profile": record.get("profile"),
        "month": record.get("month"),
        "metric": record.get("metric"),
        "current_value": record.get("current_value"),
        "site_metric_stdev": record.get("site_metric_stdev"),
        "pixel_count": record.get("pixel_count"),
        "baseline_median": record.get("baseline_median"),
        "baseline_mad": record.get("baseline_mad"),
        "baseline_years_used": record.get("baseline_years_used"),
        "robust_z_score": record.get("robust_z_score"),
        "classification": record.get("classification"),
        "direction": record.get("direction"),
        "confidence": record.get("confidence"),
        "images_used": record.get("images_used"),
        "composite_days": record.get("composite_days"),
        "composite_support": record.get("composite_support"),
        "spatial_variability_status": record.get("spatial_variability_status"),
        "season_status": record.get("season_status"),
        "disposition": record.get("disposition"),
        "recommended_action": record.get("recommended_action"),
        "artifact_path": str(path),
        "run_timestamp": file_mtime_iso(path),
        "load_timestamp": utc_now_iso(),
        "raw_record_json": compact_json(record),
    }

    return row


def parse_fusion_summary(path):
    """
    Convert one fusion summary artifact into a BigQuery row.

    One row represents:
    site_id + month

    Phase 11C adds typed climate-driver fusion fields so dashboard views
    do not need to parse raw_record_json.
    """
    record = read_json(path)

    signals = record.get("signal_summary", {})
    ndvi = signals.get("NDVI", {})
    ndmi = signals.get("NDMI", {})

    phenophase = record.get("phenophase_context", {})
    precipitation = record.get("precipitation_context", {})

    climate_summary = record.get("climate_driver_context", {})
    climate_drivers = climate_summary.get("drivers", {}) if isinstance(climate_summary, dict) else {}

    temperature = climate_drivers.get("temperature_mean_c", {})
    vpd = climate_drivers.get("vpd_mean_kpa", {})
    eto = climate_drivers.get("eto_total_mm", {})
    gridmet_precip = climate_drivers.get("precip_total_mm", {})

    closest_month = phenophase.get("closest_month")
    closest_month = str(closest_month) if closest_month is not None else None

    row = {
        "site_id": record.get("site_id"),
        "site_name": record.get("site_name"),
        "profile": record.get("profile"),
        "month": record.get("month"),

        "ndvi_classification": ndvi.get("classification"),
        "ndvi_direction": ndvi.get("direction"),
        "ndvi_value": ndvi.get("current_value"),
        "ndvi_robust_z_score": ndvi.get("robust_z_score"),

        "ndmi_classification": ndmi.get("classification"),
        "ndmi_direction": ndmi.get("direction"),
        "ndmi_value": ndmi.get("current_value"),
        "ndmi_robust_z_score": ndmi.get("robust_z_score"),

        "phenophase_status": phenophase.get("status"),
        "phenophase_closest_month": closest_month,

        "precipitation_classification": precipitation.get("classification"),
        "precipitation_current_total_mm": precipitation.get("current_total_mm"),
        "precipitation_baseline_median_mm": precipitation.get("baseline_median_mm"),
        "precipitation_robust_z_score": precipitation.get("robust_z_score"),

        "climate_context_available": climate_summary.get("available", False),
        "climate_review_cue": record.get("climate_review_cue"),

        "temperature_classification": temperature.get("classification"),
        "temperature_direction": temperature.get("direction"),
        "temperature_value_c": temperature.get("current_value"),
        "temperature_robust_z_score": temperature.get("robust_z_score"),

        "vpd_classification": vpd.get("classification"),
        "vpd_direction": vpd.get("direction"),
        "vpd_value_kpa": vpd.get("current_value"),
        "vpd_robust_z_score": vpd.get("robust_z_score"),

        "eto_classification": eto.get("classification"),
        "eto_direction": eto.get("direction"),
        "eto_value_mm": eto.get("current_value"),
        "eto_robust_z_score": eto.get("robust_z_score"),

        "gridmet_precipitation_classification": gridmet_precip.get("classification"),
        "gridmet_precipitation_direction": gridmet_precip.get("direction"),
        "gridmet_precipitation_value_mm": gridmet_precip.get("current_value"),
        "gridmet_precipitation_robust_z_score": gridmet_precip.get("robust_z_score"),

        "hypothesis": record.get("hypothesis"),
        "fusion_disposition": record.get("fusion_disposition"),
        "artifact_path": str(path),
        "run_timestamp": file_mtime_iso(path),
        "load_timestamp": utc_now_iso(),
        "raw_record_json": compact_json(record),
    }

    return row


def parse_run_log(path):
    """
    Convert one run log artifact into a BigQuery row.

    One row represents:
    one Sentry-V run log artifact.
    """
    record = read_json(path)

    month = (
        record.get("month")
        or record.get("target_month")
        or record.get("target_month_label")
    )

    row = {
        "site_id": record.get("site_id"),
        "month": month,
        "metric": record.get("metric"),
        "status": record.get("status"),
        "started_at": record.get("started_at"),
        "finished_at": record.get("finished_at"),
        "artifact_path": record.get("artifact_path"),
        "error": record.get("error"),
        "run_log_path": str(path),
        "load_timestamp": utc_now_iso(),
        "raw_record_json": compact_json(record),
    }

    return row


def parse_climate_driver_records(path):
    """
    Convert one gridMET climate driver artifact into BigQuery rows.

    One artifact contains multiple records:
    site_id + month + driver
    """
    artifact = read_json(path)
    records = artifact.get("records", [])

    rows = []

    for record in records:
        row = {
            "site_id": record.get("site_id"),
            "site_name": record.get("site_name"),
            "month": record.get("month"),
            "driver": record.get("driver"),
            "driver_label": record.get("driver_label"),
            "context_type": record.get("context_type"),
            "current_value": record.get("current_value"),
            "baseline_median": record.get("baseline_median"),
            "baseline_mad": record.get("baseline_mad"),
            "baseline_years_used": record.get("baseline_years_used"),
            "robust_z_score": record.get("robust_z_score"),
            "classification": record.get("classification"),
            "direction": record.get("direction"),
            "confidence": record.get("confidence"),
            "units": record.get("units"),
            "aggregation": record.get("aggregation"),
            "source_dataset": record.get("source_dataset"),
            "note": record.get("note"),
            "artifact_path": str(path),
            "run_timestamp": record.get("run_timestamp") or file_mtime_iso(path),
            "load_timestamp": utc_now_iso(),
            "raw_record_json": compact_json(record),
        }

        rows.append(row)

    return rows


# =========================================================
# LOAD LOCAL ARTIFACTS
# =========================================================

def load_metric_artifacts():
    """
    Load NDVI and NDMI status artifacts from outputs/.
    """
    metric_paths = []

    metric_paths.extend(OUTPUTS_DIR.glob("*_NDVI_status.json"))
    metric_paths.extend(OUTPUTS_DIR.glob("*_NDMI_status.json"))

    rows = []

    for path in sorted(metric_paths):
        rows.append(parse_metric_record(path))

    return rows


def load_fusion_artifacts():
    """
    Load site-level fusion summary artifacts from outputs/.
    """
    fusion_paths = sorted(OUTPUTS_DIR.glob("*_fusion_summary.json"))

    rows = []

    for path in fusion_paths:
        rows.append(parse_fusion_summary(path))

    return rows


def load_run_log_artifacts():
    """
    Load run log artifacts from outputs/run_logs/.
    """
    if not RUN_LOGS_DIR.exists():
        return []

    run_log_paths = sorted(RUN_LOGS_DIR.glob("*.json"))

    rows = []

    for path in run_log_paths:
        rows.append(parse_run_log(path))

    return rows


def load_climate_driver_artifacts():
    """
    Load gridMET climate driver artifacts from outputs/climate_drivers/.
    """
    if not CLIMATE_DRIVERS_DIR.exists():
        return []

    climate_paths = sorted(CLIMATE_DRIVERS_DIR.glob("*_gridmet_climate_drivers.json"))

    rows = []

    for path in climate_paths:
        rows.extend(parse_climate_driver_records(path))

    return rows


# =========================================================
# BIGQUERY TABLE REFRESH
# =========================================================

def refresh_table(client, table_name, rows, schema):
    """
    Replace a BigQuery table with the current local artifact rows.

    This makes the loader idempotent for the local prototype:
    running the loader multiple times will not duplicate rows.

    Uses a BigQuery load job with WRITE_TRUNCATE instead of streaming inserts.
    This avoids BigQuery streaming-buffer DELETE limitations.
    """
    table_id = get_table_id(table_name)

    if not rows:
        print(f"[INFO] No rows found for {table_name}. Table not refreshed.")
        return

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    load_job = client.load_table_from_json(
        rows,
        table_id,
        job_config=job_config,
    )

    load_job.result()

    print(f"[SUCCESS] Refreshed {table_id} with {len(rows)} row(s).")


# =========================================================
# MAIN LOADER
# =========================================================

def load_all_artifacts_to_bigquery():
    """
    Load local Sentry-V JSON artifacts into BigQuery.

    This loader is intentionally separate from run_sentry.py so the science
    engine remains decoupled from cloud storage.

    Idempotent behavior:
    - metric_records table is replaced with current local metric artifacts
    - fusion_summaries table is replaced with current local fusion artifacts
    - run_logs table is replaced with current local run log artifacts
    - climate_driver_records table is replaced with current climate driver artifacts
    """
    print("\n========================================")
    print("   SENTRY-V BIGQUERY ARTIFACT LOADER")
    print("========================================\n")

    client = bigquery.Client(project=PROJECT_ID)

    metric_rows = load_metric_artifacts()
    fusion_rows = load_fusion_artifacts()
    run_log_rows = load_run_log_artifacts()
    climate_driver_rows = load_climate_driver_artifacts()

    print(f"Metric records found: {len(metric_rows)}")
    print(f"Fusion summaries found: {len(fusion_rows)}")
    print(f"Run logs found: {len(run_log_rows)}")
    print(f"Climate driver records found: {len(climate_driver_rows)}")

    print("\n[Running] BigQuery table refresh...")

    refresh_table(client, "metric_records", metric_rows, METRIC_RECORDS_SCHEMA)
    refresh_table(client, "fusion_summaries", fusion_rows, FUSION_SUMMARIES_SCHEMA)
    refresh_table(client, "run_logs", run_log_rows, RUN_LOGS_SCHEMA)
    refresh_table(
        client,
        "climate_driver_records",
        climate_driver_rows,
        CLIMATE_DRIVER_RECORDS_SCHEMA,
    )

    print("\n[SUCCESS] All available Sentry-V artifacts refreshed in BigQuery.")


if __name__ == "__main__":
    load_all_artifacts_to_bigquery()