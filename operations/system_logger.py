import json
from pathlib import Path
from datetime import datetime, timezone


def get_utc_timestamp():
    """
    Return the current UTC time in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()


def create_run_id(site_id, target_month):
    """
    Create a readable unique run ID.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"sentry_v_{site_id}_{target_month}_{timestamp}"


def save_run_log(
    site_id,
    target_month,
    metric,
    status,
    started_at,
    finished_at,
    artifact_path=None,
    error=None,
    output_dir="outputs/run_logs"
):
    """
    Save a Sentry-V execution log as a JSON artifact.

    This creates an audit trail for each system run.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    started_dt = datetime.fromisoformat(started_at)
    finished_dt = datetime.fromisoformat(finished_at)
    duration_seconds = round((finished_dt - started_dt).total_seconds(), 2)

    run_id = create_run_id(site_id, target_month)

    run_log = {
        "run_id": run_id,
        "system": "Sentry-V",
        "site_id": site_id,
        "target_month": target_month,
        "metric": metric,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
        "artifact_path": str(artifact_path) if artifact_path else None,
        "error": str(error) if error else None
    }

    filename = f"{run_id}_run_log.json"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(run_log, file, indent=2)

    print("\n--- Phase 6: Orchestration & Observability ---")
    print(f"[SUCCESS] Run log saved to: {filepath}")

    return filepath