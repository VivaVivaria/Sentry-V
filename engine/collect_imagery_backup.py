import ee
import yaml
import json
import sys
import os
from pathlib import Path

from calculate_indices import add_ndvi
from build_monthly_composite import get_monthly_ndvi_mean
from create_monthly_record import build_monitoring_record
from calculate_baseline import get_historical_baseline
from classify_status import classify_vegetation_status

# Add the parent directory so Python can import from validation/ and operations/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validation.quality_checks import assess_confidence
from operations.export_record import save_monitoring_artifact


def load_config(config_path="config/sites.yaml"):
    """
    Load the Sentry-V monitoring configuration.
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_file, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def get_site_config(site_id, config_data):
    """
    Find one site from the sites.yaml file using its site_id.
    """
    for site in config_data["sites"]:
        if site["site_id"] == site_id:
            return site

    raise ValueError(f"Site ID '{site_id}' not found in configuration.")


def get_site_geometry(site_config):
    """
    Convert the YAML geometry into an Earth Engine geometry.
    """
    geometry = site_config["geometry"]
    geometry_type = geometry["type"]
    coordinates = geometry["coordinates"]

    if geometry_type == "Point":
        return ee.Geometry.Point(coordinates).buffer(500)

    if geometry_type == "Polygon":
        return ee.Geometry.Polygon(coordinates)

    raise ValueError(f"Unsupported geometry type: {geometry_type}")


def collect_imagery(site_id, config_data, start_year=2021, end_year=2026):
    """
    Pull Sentinel-2 imagery for one configured monitoring site across a year range.
    """
    site_config = get_site_config(site_id, config_data)

    print(f"Target locked: {site_config['site_name']}")

    collection_name = site_config["data_source"]
    geometry = get_site_geometry(site_config)

    start_month = site_config["monitoring_season"]["start_month"]
    end_month = site_config["monitoring_season"]["end_month"]

    start_date = f"{start_year}-{start_month:02d}-01"
    end_date = f"{end_year}-{end_month:02d}-31"

    print(f"Data source: {collection_name}")
    print(f"Date range: {start_date} to {end_date}")
    print("Requesting Sentinel-2 imagery from Google Earth Engine...")

    collection = (
        ee.ImageCollection(collection_name)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
    )

    image_count = collection.size().getInfo()

    print(f"Images found: {image_count}")

    if image_count == 0:
        print("No viable images found. Try loosening the cloud filter or checking the site geometry.")
    else:
        print("Analytical Engine heartbeat successful.")
        print("Sentry-V can read its target and find satellite imagery.")

    return collection


if __name__ == "__main__":
    print("Starting Sentry-V Analytical Engine heartbeat...")

    try:
        ee.Initialize()

        site_id = "rouge_eic"
        target_year = 2026
        target_month = 4
        lookback_years = 5
        baseline_start_year = target_year - lookback_years

        config = load_config()
        site_config = get_site_config(site_id, config)
        site_geometry = get_site_geometry(site_config)

        imagery = collect_imagery(
            site_id,
            config,
            start_year=baseline_start_year,
            end_year=target_year
        )

        print("\n--- Phase 2B: NDVI Calculation ---")
        print("Applying NDVI calculation to the image collection...")

        collection_with_ndvi = imagery.map(add_ndvi)

        first_image = collection_with_ndvi.first()
        band_names = first_image.bandNames().getInfo()

        if "NDVI" in band_names:
            print("[SUCCESS] Sentry-V calculated NDVI.")
            print("Band 'NDVI' found.")
        else:
            print("[ERROR] NDVI band is missing.")

        monthly_signal, image_count = get_monthly_ndvi_mean(
            collection=collection_with_ndvi,
            site_geometry=site_geometry,
            site_id=site_id,
            year=target_year,
            month=target_month
        )

        print("\n--- Phase 2D: Monthly Output Record ---")

        record = build_monitoring_record(
            site_id=site_id,
            site_name=site_config["site_name"],
            year=target_year,
            month=target_month,
            metric="NDVI",
            mean_value=monthly_signal,
            image_count=image_count
        )

        print(json.dumps(record, indent=2))
        print("[SUCCESS] Monthly structured record created.")

        baseline_mean, baseline_stdev, historical_values = get_historical_baseline(
            collection=collection_with_ndvi,
            site_geometry=site_geometry,
            site_id=site_id,
            target_month=target_month,
            current_year=target_year,
            lookback_years=lookback_years
        )

        status_record = classify_vegetation_status(
            current_value=monthly_signal,
            baseline_mean=baseline_mean,
            baseline_stdev=baseline_stdev
        )

        print("\n--- Phase 3C: Baseline-Enriched Record Cleanup ---")

        final_record = {
            "site_id": record["site_id"],
            "site_name": record["site_name"],
            "month": record["month"],
            "metric": record["metric"],
            "current_value": record["mean_value"],
            "baseline_mean": round(baseline_mean, 4) if baseline_mean is not None else None,
            "baseline_stdev": round(baseline_stdev, 4) if baseline_stdev is not None else None,
            "z_score": status_record["z_score"],
            "classification": status_record["classification"],
            "direction": status_record["direction"],
            "confidence": "pending_validation",
            "images_used": record["images_used"],
            "historical_values": [round(value, 4) for value in historical_values],
            "interpretation": status_record["interpretation"],
            "note": "Detection only. Human interpretation required."
        }

        confidence_level, validation_reasons = assess_confidence(
            current_value=final_record["current_value"],
            images_used=final_record["images_used"],
            historical_values=final_record["historical_values"]
        )

        final_record["confidence"] = confidence_level

        if validation_reasons:
            warning_text = ", ".join(validation_reasons)
            final_record["note"] += f" Guardrail warnings: {warning_text}."

        print("\n--- Final Enriched Monitoring Record Production Schema ---")
        print(json.dumps(final_record, indent=2))
        print("[SUCCESS] Production-ready monitoring record created.")

        saved_path = save_monitoring_artifact(record=final_record)

    except Exception as error:
        print(f"System Error: {error}")