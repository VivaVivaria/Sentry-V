import json
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import bigquery

from storage.bigquery_client import PROJECT_ID, DATASET_ID


OUTPUTS_DIR = Path("outputs")
RUN_LOGS_DIR = OUTPUTS_DIR / "run_logs"


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


def parse_metric_record(path):
    """
    Convert one NDVI/NDMI status artifact into a BigQuery row.
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
    """
    record = read_json(path)

    signals = record.get("signal_summary", {})
    ndvi = signals.get("NDVI", {})
    ndmi = signals.get("NDMI", {})

    phenophase = record.get("phenophase_context", {})
    precipitation = record.get("precipitation_context", {})

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
    """
    record = read_json(path)

    # Support slightly different key names safely.
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


def insert_rows(client, table_name, rows):
    """
    Insert rows into a BigQuery table.
    """
    if not rows:
        print(f"[INFO] No rows to insert into {table_name}.")
        return

    table_id = get_table_id(table_name)

    errors = client.insert_rows_json(table_id, rows)

    if errors:
        print(f"[ERROR] Failed inserting rows into {table_id}")
        print(json.dumps(errors, indent=2))
        raise RuntimeError(f"BigQuery insert failed for {table_name}")

    print(f"[SUCCESS] Inserted {len(rows)} row(s) into {table_id}")


def load_metric_artifacts():
    """
    Load NDVI and NDMI status artifacts.
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
    Load site-level fusion summary artifacts.
    """
    fusion_paths = sorted(OUTPUTS_DIR.glob("*_fusion_summary.json"))

    rows = []

    for path in fusion_paths:
        rows.append(parse_fusion_summary(path))

    return rows


def load_run_log_artifacts():
    """
    Load run log artifacts.
    """
    if not RUN_LOGS_DIR.exists():
        return []

    run_log_paths = sorted(RUN_LOGS_DIR.glob("*.json"))

    rows = []

    for path in run_log_paths:
        rows.append(parse_run_log(path))

    return rows


def load_all_artifacts_to_bigquery():
    """
    Load local Sentry-V JSON artifacts into BigQuery.

    This loader is intentionally separate from run_sentry.py so the science
    engine remains decoupled from cloud storage.
    """
    print("\n========================================")
    print("   SENTRY-V BIGQUERY ARTIFACT LOADER")
    print("========================================\n")

    client = bigquery.Client(project=PROJECT_ID)

    metric_rows = load_metric_artifacts()
    fusion_rows = load_fusion_artifacts()
    run_log_rows = load_run_log_artifacts()

    print(f"Metric records found: {len(metric_rows)}")
    print(f"Fusion summaries found: {len(fusion_rows)}")
    print(f"Run logs found: {len(run_log_rows)}")

    insert_rows(client, "metric_records", metric_rows)
    insert_rows(client, "fusion_summaries", fusion_rows)
    insert_rows(client, "run_logs", run_log_rows)

    print("\n[SUCCESS] All available Sentry-V artifacts loaded into BigQuery.")


if __name__ == "__main__":
    load_all_artifacts_to_bigquery()