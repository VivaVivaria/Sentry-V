"""
Sentry-V gridMET Climate Driver Module

Phase 11B — Thermal & Evaporative Demand Context

Purpose:
- Extract monthly atmospheric / thermal driver context from gridMET.
- Produce flat climate_driver_records that can later be loaded into BigQuery.
- Preserve Sentry-V's scientific boundary: detection support only, not causation.

Drivers:
- temperature_mean_c  : monthly average daily mean air temperature
- vpd_mean_kpa        : monthly average vapor pressure deficit
- eto_total_mm        : monthly total reference evapotranspiration
- precip_total_mm     : monthly total gridMET precipitation cross-check

Notes:
- CHIRPS remains the primary precipitation context for Sentry-V.
- gridMET precipitation is kept as a secondary meteorological cross-check.
"""

from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import ee


GRIDMET_COLLECTION = "IDAHO_EPSCOR/GRIDMET"
GRIDMET_SCALE_METERS = 4000

DRIVER_METADATA = {
    "temperature_mean_c": {
        "label": "Mean Temperature",
        "units": "C",
        "aggregation": "monthly_average_daily_mean",
        "context_type": "thermal_context",
    },
    "vpd_mean_kpa": {
        "label": "Vapor Pressure Deficit",
        "units": "kPa",
        "aggregation": "monthly_average",
        "context_type": "moisture_demand_context",
    },
    "eto_total_mm": {
        "label": "Reference Evapotranspiration",
        "units": "mm",
        "aggregation": "monthly_sum",
        "context_type": "evaporative_demand_context",
    },
    "precip_total_mm": {
        "label": "gridMET Precipitation",
        "units": "mm",
        "aggregation": "monthly_sum",
        "context_type": "precipitation_cross_check",
    },
}


def initialize_earth_engine(project: Optional[str] = None) -> None:
    """
    Initialize Earth Engine without interactive authentication.

    Do not call ee.Authenticate() here because Cloud Run cannot use browser-based auth.
    Local and cloud environments should already be authenticated before execution.
    """
    try:
        if project:
            ee.Initialize(project=project)
        else:
            ee.Initialize()
    except Exception as exc:
        raise RuntimeError(
            "Earth Engine failed to initialize. "
            "Authenticate locally with gcloud/earthengine, or ensure the Cloud Run "
            "service account has Earth Engine access."
        ) from exc


def safe_round(value: Any, digits: int = 4) -> Optional[float]:
    if value is None:
        return None
    try:
        if math.isnan(float(value)):
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def median_absolute_deviation(values: List[float], median_value: float) -> Optional[float]:
    if not values:
        return None

    deviations = [abs(v - median_value) for v in values if v is not None]

    if not deviations:
        return None

    return statistics.median(deviations)


def robust_z_score(
    current_value: Optional[float],
    baseline_median: Optional[float],
    baseline_mad: Optional[float],
) -> Optional[float]:
    """
    Robust z-score using MAD.

    Formula:
    robust_z = 0.6745 * (current - median) / MAD
    """
    if current_value is None or baseline_median is None or baseline_mad in (None, 0):
        return None

    return 0.6745 * (current_value - baseline_median) / baseline_mad


def classify_direction(z_score: Optional[float]) -> str:
    if z_score is None:
        return "pending_baseline"

    if abs(z_score) < 1:
        return "near_expected"

    if z_score > 0:
        return "higher_than_expected"

    return "lower_than_expected"


def classify_driver(driver: str, z_score: Optional[float]) -> str:
    """
    Convert robust z-score into a driver-specific client-safe context label.
    """
    if z_score is None:
        return "pending_baseline"

    # Near normal band
    if abs(z_score) < 1:
        if driver in {"vpd_mean_kpa", "eto_total_mm"}:
            return "normal_demand"
        return "near_normal"

    # High side
    if z_score >= 2:
        if driver == "temperature_mean_c":
            return "unusually_warm"
        if driver in {"vpd_mean_kpa", "eto_total_mm"}:
            return "very_high_demand"
        if driver == "precip_total_mm":
            return "well_above_normal"
        return "unusually_high"

    if z_score >= 1:
        if driver == "temperature_mean_c":
            return "above_normal"
        if driver in {"vpd_mean_kpa", "eto_total_mm"}:
            return "high_demand"
        if driver == "precip_total_mm":
            return "above_normal"
        return "above_normal"

    # Low side
    if z_score <= -2:
        if driver == "temperature_mean_c":
            return "unusually_cool"
        if driver in {"vpd_mean_kpa", "eto_total_mm"}:
            return "very_low_demand"
        if driver == "precip_total_mm":
            return "well_below_normal"
        return "unusually_low"

    if z_score <= -1:
        if driver == "temperature_mean_c":
            return "below_normal"
        if driver in {"vpd_mean_kpa", "eto_total_mm"}:
            return "low_demand"
        if driver == "precip_total_mm":
            return "below_normal"
        return "below_normal"

    return "near_normal"


def confidence_from_baseline_years(baseline_years_used: int) -> str:
    if baseline_years_used >= 8:
        return "high"
    if baseline_years_used >= 5:
        return "medium"
    if baseline_years_used > 0:
        return "low"
    return "insufficient_baseline"


def build_monthly_gridmet_image(
    geometry: ee.Geometry,
    target_year: int,
    target_month: int,
) -> ee.Image:
    """
    Build one monthly aggregate image from daily gridMET images.

    Monthly aggregation rules:
    - temperature_mean_c: mean of daily mean temperature
    - vpd_mean_kpa: mean of daily VPD
    - eto_total_mm: sum of daily ETo
    - precip_total_mm: sum of daily precipitation
    """
    start_date = ee.Date.fromYMD(target_year, target_month, 1)
    end_date = start_date.advance(1, "month")

    collection = (
        ee.ImageCollection(GRIDMET_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
    )

    def process_daily(image: ee.Image) -> ee.Image:
        tmmx = image.select("tmmx")
        tmmn = image.select("tmmn")

        daily_mean_c = (
            tmmx.add(tmmn)
            .divide(2)
            .subtract(273.15)
            .rename("temperature_mean_c")
        )

        vpd = image.select("vpd").rename("vpd_mean_kpa")
        eto = image.select("eto").rename("eto_total_mm")
        precip = image.select("pr").rename("precip_total_mm")

        return (
            ee.Image.cat([daily_mean_c, vpd, eto, precip])
            .copyProperties(image, ["system:time_start"])
        )

    processed = collection.map(process_daily)

    monthly_image = ee.Image.cat(
        [
            processed.select("temperature_mean_c").mean(),
            processed.select("vpd_mean_kpa").mean(),
            processed.select("eto_total_mm").sum(),
            processed.select("precip_total_mm").sum(),
        ]
    )

    return monthly_image


def reduce_monthly_gridmet_values(
    geometry: ee.Geometry,
    target_year: int,
    target_month: int,
) -> Dict[str, Optional[float]]:
    """
    Reduce monthly gridMET image over site geometry.
    """
    monthly_image = build_monthly_gridmet_image(
        geometry=geometry,
        target_year=target_year,
        target_month=target_month,
    )

    stats = monthly_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=GRIDMET_SCALE_METERS,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()

    return {
        "temperature_mean_c": safe_round(stats.get("temperature_mean_c"), 4),
        "vpd_mean_kpa": safe_round(stats.get("vpd_mean_kpa"), 4),
        "eto_total_mm": safe_round(stats.get("eto_total_mm"), 4),
        "precip_total_mm": safe_round(stats.get("precip_total_mm"), 4),
    }


def get_historical_same_month_values(
    geometry: ee.Geometry,
    target_month: int,
    baseline_start_year: int,
    baseline_end_year: int,
) -> Dict[str, List[float]]:
    """
    Pull same-month historical monthly values for baseline calculation.

    Example:
    target_month = 4
    baseline = all Aprils from baseline_start_year through baseline_end_year
    """
    historical_values = {driver: [] for driver in DRIVER_METADATA.keys()}

    for year in range(baseline_start_year, baseline_end_year + 1):
        monthly_values = reduce_monthly_gridmet_values(
            geometry=geometry,
            target_year=year,
            target_month=target_month,
        )

        for driver, value in monthly_values.items():
            if value is not None:
                historical_values[driver].append(value)

    return historical_values


def build_climate_driver_records(
    site_id: str,
    site_name: str,
    geometry: ee.Geometry,
    target_year: int,
    target_month: int,
    baseline_start_year: int = 2010,
) -> List[Dict[str, Any]]:
    """
    Build flat climate_driver_records for one site/month.

    Returns one row per driver.
    """
    month_label = f"{target_year}-{target_month:02d}"
    run_timestamp = datetime.now(timezone.utc).isoformat()

    current_values = reduce_monthly_gridmet_values(
        geometry=geometry,
        target_year=target_year,
        target_month=target_month,
    )

    baseline_end_year = target_year - 1
    historical_values = get_historical_same_month_values(
        geometry=geometry,
        target_month=target_month,
        baseline_start_year=baseline_start_year,
        baseline_end_year=baseline_end_year,
    )

    records = []

    for driver, metadata in DRIVER_METADATA.items():
        current_value = current_values.get(driver)
        baseline_series = historical_values.get(driver, [])
        baseline_years_used = len(baseline_series)

        baseline_median = (
            statistics.median(baseline_series)
            if baseline_series
            else None
        )

        baseline_mad = (
            median_absolute_deviation(baseline_series, baseline_median)
            if baseline_median is not None
            else None
        )

        z_score = robust_z_score(current_value, baseline_median, baseline_mad)

        record = {
            "site_id": site_id,
            "site_name": site_name,
            "month": month_label,
            "driver": driver,
            "driver_label": metadata["label"],
            "context_type": metadata["context_type"],
            "current_value": safe_round(current_value, 4),
            "baseline_median": safe_round(baseline_median, 4),
            "baseline_mad": safe_round(baseline_mad, 4),
            "baseline_years_used": baseline_years_used,
            "robust_z_score": safe_round(z_score, 2),
            "classification": classify_driver(driver, z_score),
            "direction": classify_direction(z_score),
            "confidence": confidence_from_baseline_years(baseline_years_used),
            "units": metadata["units"],
            "aggregation": metadata["aggregation"],
            "source_dataset": "IDAHO_EPSCOR/GRIDMET",
            "run_timestamp": run_timestamp,
            "note": (
                "Climate driver context supports review cues only. "
                "It does not establish causation."
            ),
        }

        records.append(record)

    return records


if __name__ == "__main__":
    print("\n========================================")
    print("   SENTRY-V GRIDMET CLIMATE DRIVER TEST")
    print("========================================\n")

    initialize_earth_engine(project="sentry-v")

    test_site_id = "rouge_eic"
    test_site_name = "UM-Dearborn EIC / Rouge River"

    # Approximate Lower Rouge Riparian / EIC point used for local module test.
    # Later, run_sentry.py should pass the real site geometry from config/sites.yaml.
    test_geometry = ee.Geometry.Point([-83.239361, 42.315764]).buffer(250)

    records = build_climate_driver_records(
        site_id=test_site_id,
        site_name=test_site_name,
        geometry=test_geometry,
        target_year=2026,
        target_month=4,
        baseline_start_year=2010,
    )

    print(json.dumps(records, indent=2))