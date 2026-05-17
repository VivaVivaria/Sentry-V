import ee
import logging

logger = logging.getLogger(__name__)


def get_precipitation_context(
    site_geometry,
    target_year,
    target_month,
    baseline_start_year=2000
):
    """
    Calculate current and historical precipitation context using CHIRPS.

    This is an environmental driver context, not a vegetation metric.

    Args:
        site_geometry: Earth Engine geometry for the site.
        target_year: Year being analyzed.
        target_month: Month being analyzed.
        baseline_start_year: First year used for precipitation baseline.

    Returns:
        Dictionary payload for the fusion summary.
    """
    logger.info(f"Calculating precipitation context for {target_year}-{target_month:02d}...")

    try:
        start_date = ee.Date.fromYMD(target_year, target_month, 1)
        end_date = start_date.advance(1, "month")

        chirps = ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")

        # 1. Current month precipitation total.
        current_month_collection = (
            chirps
            .filterBounds(site_geometry)
            .filterDate(start_date, end_date)
        )

        current_month_total = current_month_collection.sum().clip(site_geometry)

        current_val = current_month_total.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=site_geometry,
            scale=5566,
            maxPixels=1e9
        ).get("precipitation")

        current_mm = ee.Number(current_val).getInfo()

        if current_mm is None:
            return _build_payload(
                target_year,
                target_month,
                None,
                None,
                None,
                None,
                "insufficient_data"
            )

        # 2. Historical same-month precipitation totals.
        years = ee.List.sequence(baseline_start_year, target_year - 1)

        def get_monthly_total(year):
            month_start = ee.Date.fromYMD(year, target_month, 1)
            month_end = month_start.advance(1, "month")

            monthly_total = (
                chirps
                .filterBounds(site_geometry)
                .filterDate(month_start, month_end)
                .sum()
            )

            return monthly_total.set("system:time_start", month_start.millis())

        historical_monthly_totals = ee.ImageCollection.fromImages(
            years.map(get_monthly_total)
        )

        # 3. Robust baseline: median + MAD.
        baseline_median_img = historical_monthly_totals.median().clip(site_geometry)

        def calc_abs_dev(image):
            return image.subtract(baseline_median_img).abs()

        mad_img = ee.ImageCollection(
            historical_monthly_totals.map(calc_abs_dev)
        ).median().clip(site_geometry)

        baseline_median = baseline_median_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=site_geometry,
            scale=5566,
            maxPixels=1e9
        ).get("precipitation")

        baseline_mad = mad_img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=site_geometry,
            scale=5566,
            maxPixels=1e9
        ).get("precipitation")

        median_mm = ee.Number(baseline_median).getInfo()
        mad_mm = ee.Number(baseline_mad).getInfo()

        if median_mm is None or mad_mm is None:
            return _build_payload(
                target_year,
                target_month,
                current_mm,
                None,
                None,
                None,
                "insufficient_data"
            )

        # Prevent division by zero.
        mad_mm = mad_mm if mad_mm > 0 else 0.1

        # 4. Robust z-score.
        robust_z = (current_mm - median_mm) / (mad_mm * 1.4826)

        # 5. Classification.
        classification = _classify_precipitation(robust_z)

        return _build_payload(
            target_year,
            target_month,
            current_mm,
            median_mm,
            mad_mm,
            robust_z,
            classification
        )

    except Exception as error:
        logger.error(f"Failed to calculate precipitation context: {error}")

        return _build_payload(
            target_year,
            target_month,
            None,
            None,
            None,
            None,
            "insufficient_data"
        )


def _classify_precipitation(robust_z):
    """
    Classify precipitation using robust z-score thresholds.
    """
    if robust_z is None:
        return "insufficient_data"

    if robust_z < -1.0:
        return "below_normal"

    if robust_z > 1.0:
        return "above_normal"

    return "near_normal"


def _build_payload(year, month, current, median, mad, z_score, classification):
    """
    Build standard precipitation context payload.
    """
    return {
        "dataset": "UCSB-CHG/CHIRPS/DAILY",
        "month": f"{year}-{month:02d}",
        "baseline_start_year": 2000,
        "current_total_mm": round(current, 1) if current is not None else None,
        "baseline_median_mm": round(median, 1) if median is not None else None,
        "baseline_mad_mm": round(mad, 1) if mad is not None else None,
        "robust_z_score": round(z_score, 2) if z_score is not None else None,
        "classification": classification,
        "note": (
            "Precipitation context is environmental support only. "
            "It does not establish causation."
        )
    }