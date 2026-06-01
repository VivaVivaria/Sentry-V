"""
Sentry-V gridMET Climate Driver Artifact Runner

Phase 11B.2 — Generate climate driver artifacts

Purpose:
- Read configured Sentry-V sites from config/sites.yaml
- Extract monthly gridMET climate drivers for each site
- Use a gridMET-safe climate sampling geometry
- Write JSON artifacts into outputs/climate_drivers/

Output example:
outputs/climate_drivers/rouge_eic_2026-04_gridmet_climate_drivers.json

Important architecture note:
- Sentinel-2 vegetation metrics should use the precise site polygon.
- gridMET climate drivers should use a regional climate sampling geometry.
- This prevents small vegetation polygons from returning null values against coarse
  ~4 km gridMET pixels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import ee
import yaml

from climate.gridmet import (
    build_climate_driver_records,
    initialize_earth_engine,
)


DEFAULT_CONFIG_PATH = Path("config/sites.yaml")
DEFAULT_OUTPUT_DIR = Path("outputs/climate_drivers")
DEFAULT_CLIMATE_BUFFER_METERS = 5000


def load_sites_config(config_path: Path) -> Dict[str, Any]:
    """Load Sentry-V YAML config."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_ee_geometry(site: Dict[str, Any]) -> ee.Geometry:
    """
    Convert a site geometry block from config/sites.yaml into an Earth Engine geometry.

    Expected config shape:

    geometry:
      type: Polygon
      coordinates:
        - - [lon, lat]
          - [lon, lat]
          ...

    Notes:
    - This geometry represents the precise vegetation monitoring area.
    - It is appropriate for Sentinel-2 NDVI / NDMI.
    - It may be too small for coarse climate datasets like gridMET.
    """
    geometry = site.get("geometry", {})
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if not geometry_type or not coordinates:
        raise ValueError(
            f"Site {site.get('site_id')} is missing geometry type or coordinates."
        )

    if geometry_type == "Polygon":
        return ee.Geometry.Polygon(coordinates)

    if geometry_type == "Point":
        return ee.Geometry.Point(coordinates)

    raise ValueError(
        f"Unsupported geometry type for site {site.get('site_id')}: {geometry_type}"
    )


def build_climate_sampling_geometry(
    site_geometry: ee.Geometry,
    buffer_meters: int = DEFAULT_CLIMATE_BUFFER_METERS,
) -> ee.Geometry:
    """
    Convert a precise site geometry into a gridMET-safe sampling geometry.

    Why this exists:
    - Sentinel-2 pixels are about 10 m, so small site polygons work well.
    - gridMET pixels are roughly 4 km, so tiny polygons can return null values.
    - For atmospheric context, a centroid-based regional buffer is more stable.

    Scientific interpretation:
    - Vegetation geometry = precise local canopy / site footprint.
    - Climate geometry = regional atmospheric context around the site.

    This keeps Sentry-V scientifically cleaner:
    - Do not buffer vegetation metrics.
    - Do buffer coarse climate context.
    """
    return site_geometry.centroid(maxError=1).buffer(buffer_meters)


def write_json_artifact(
    records: List[Dict[str, Any]],
    output_dir: Path,
    site_id: str,
    month: str,
) -> Path:
    """Write climate driver records to a JSON artifact."""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{site_id}_{month}_gridmet_climate_drivers.json"

    payload = {
        "artifact_type": "gridmet_climate_drivers",
        "site_id": site_id,
        "month": month,
        "record_count": len(records),
        "records": records,
        "note": (
            "gridMET climate driver context supports review cues only. "
            "It does not establish causation."
        ),
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return output_path


def generate_gridmet_artifacts(
    target_year: int,
    target_month: int,
    config_path: Path = DEFAULT_CONFIG_PATH,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    baseline_start_year: int = 2010,
    ee_project: str | None = "sentry-v",
    climate_buffer_meters: int = DEFAULT_CLIMATE_BUFFER_METERS,
) -> List[Path]:
    """
    Generate gridMET climate driver artifacts for all configured sites.

    This function:
    1. Loads sites from config/sites.yaml
    2. Builds the precise vegetation site geometry
    3. Converts it to a climate-safe centroid buffer
    4. Extracts gridMET driver records
    5. Writes one JSON artifact per site/month
    """
    initialize_earth_engine(project=ee_project)

    config = load_sites_config(config_path)
    sites = config.get("sites", [])

    if not sites:
        raise ValueError(f"No sites found in config: {config_path}")

    month_label = f"{target_year}-{target_month:02d}"
    written_paths: List[Path] = []

    print("\n========================================")
    print("   SENTRY-V GRIDMET ARTIFACT GENERATOR")
    print("========================================")
    print(f"Target month: {month_label}")
    print(f"Sites found: {len(sites)}")
    print(f"Output dir: {output_dir}")
    print(f"Climate buffer: {climate_buffer_meters} m")
    print("========================================\n")

    for site in sites:
        site_id = site["site_id"]
        site_name = site["site_name"]

        print(f"[Running] {site_id} — {site_name}")

        site_geometry = build_ee_geometry(site)
        climate_geometry = build_climate_sampling_geometry(
            site_geometry=site_geometry,
            buffer_meters=climate_buffer_meters,
        )

        records = build_climate_driver_records(
            site_id=site_id,
            site_name=site_name,
            geometry=climate_geometry,
            target_year=target_year,
            target_month=target_month,
            baseline_start_year=baseline_start_year,
        )

        output_path = write_json_artifact(
            records=records,
            output_dir=output_dir,
            site_id=site_id,
            month=month_label,
        )

        written_paths.append(output_path)

        print(f"[SUCCESS] Wrote {len(records)} driver record(s): {output_path}\n")

    print("[SUCCESS] All gridMET climate driver artifacts generated.")
    return written_paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Sentry-V gridMET climate driver artifacts."
    )

    parser.add_argument(
        "--year",
        type=int,
        required=True,
        help="Target year, e.g. 2026",
    )

    parser.add_argument(
        "--month",
        type=int,
        required=True,
        help="Target month number, e.g. 4",
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to Sentry-V sites.yaml config.",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where climate driver artifacts will be written.",
    )

    parser.add_argument(
        "--baseline-start-year",
        type=int,
        default=2010,
        help="First year for same-month historical baseline.",
    )

    parser.add_argument(
        "--ee-project",
        type=str,
        default="sentry-v",
        help="Earth Engine / Google Cloud project ID.",
    )

    parser.add_argument(
        "--climate-buffer-meters",
        type=int,
        default=DEFAULT_CLIMATE_BUFFER_METERS,
        help=(
            "Buffer size around the site centroid for gridMET climate sampling. "
            "Default is 5000 meters."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    generate_gridmet_artifacts(
        target_year=args.year,
        target_month=args.month,
        config_path=args.config,
        output_dir=args.output_dir,
        baseline_start_year=args.baseline_start_year,
        ee_project=args.ee_project,
        climate_buffer_meters=args.climate_buffer_meters,
    )