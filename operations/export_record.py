import json
from pathlib import Path


def save_monitoring_artifact(record, output_dir="outputs"):
    """
    Export the finalized monitoring record as a JSON file.

    This creates a permanent artifact for future dashboarding,
    BigQuery ingestion, email alerts, or monthly review.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    site_id = record["site_id"]
    month = record["month"]
    metric = record["metric"]

    filename = f"{site_id}_{month}_{metric}_status.json"
    filepath = output_path / filename

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(record, file, indent=2)

    print("\n--- Phase 5: Output Format ---")
    print(f"[SUCCESS] Monitoring artifact saved to: {filepath}")

    return filepath