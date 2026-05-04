from engine.calculate_baseline import get_historical_baseline


def get_phenophase_context(
    collection,
    site_geometry,
    site_id,
    current_year,
    target_month,
    current_ndvi,
    lookback_years=8
):
    """
    Compare the current NDVI against historical NDVI baselines for the
    previous, current, and next month.

    This helps classify seasonal timing as:
    - delayed
    - expected
    - early
    - uncertain
    """
    print("\n--- Phase 8D: Phenophase Timing Context ---")

    if current_ndvi is None:
        return {
            "status": "uncertain",
            "closest_month": None,
            "note": "No current NDVI available for phenophase comparison."
        }

    def wrap_month(month):
        if month < 1:
            return 12
        if month > 12:
            return 1
        return month

    previous_month = wrap_month(target_month - 1)
    next_month = wrap_month(target_month + 1)

    print("Fetching neighboring NDVI baselines for temporal comparison...")

    previous_median, _, _ = get_historical_baseline(
        collection=collection,
        site_geometry=site_geometry,
        site_id=site_id,
        target_month=previous_month,
        current_year=current_year,
        metric="NDVI",
        lookback_years=lookback_years
    )

    current_median, _, _ = get_historical_baseline(
        collection=collection,
        site_geometry=site_geometry,
        site_id=site_id,
        target_month=target_month,
        current_year=current_year,
        metric="NDVI",
        lookback_years=lookback_years
    )

    next_median, _, _ = get_historical_baseline(
        collection=collection,
        site_geometry=site_geometry,
        site_id=site_id,
        target_month=next_month,
        current_year=current_year,
        metric="NDVI",
        lookback_years=lookback_years
    )

    distances = {}

    if previous_median is not None:
        distances["delayed"] = {
            "distance": abs(current_ndvi - previous_median),
            "closest_month": previous_month,
            "baseline_median": previous_median
        }

    if current_median is not None:
        distances["expected"] = {
            "distance": abs(current_ndvi - current_median),
            "closest_month": target_month,
            "baseline_median": current_median
        }

    if next_median is not None:
        distances["early"] = {
            "distance": abs(current_ndvi - next_median),
            "closest_month": next_month,
            "baseline_median": next_median
        }

    if not distances:
        return {
            "status": "uncertain",
            "closest_month": None,
            "note": "Insufficient historical data for phenophase comparison."
        }

    status = min(distances, key=lambda label: distances[label]["distance"])
    closest_month = distances[status]["closest_month"]
    closest_baseline = distances[status]["baseline_median"]
    closest_distance = distances[status]["distance"]

    print("\n[PHENOPHASE RESULTS]")
    print(f"Current NDVI: {current_ndvi:.4f}")

    if previous_median is not None:
        print(f"Previous Month ({previous_month:02d}) NDVI Baseline: {previous_median:.4f}")

    if current_median is not None:
        print(f"Current Month ({target_month:02d}) NDVI Baseline: {current_median:.4f}")

    if next_median is not None:
        print(f"Next Month ({next_month:02d}) NDVI Baseline: {next_median:.4f}")

    print(f"Phenophase Status: {status.upper()}")
    print(f"Closest Baseline Month: {closest_month:02d}")

    return {
        "status": status,
        "target_month": target_month,
        "closest_month": closest_month,
        "closest_baseline_median": round(closest_baseline, 4),
        "distance_from_closest_baseline": round(closest_distance, 4),
        "comparison_months": {
            "delayed_reference_month": previous_month,
            "expected_reference_month": target_month,
            "early_reference_month": next_month
        },
        "note": (
            f"Current vegetation greenness most closely resembles the historical "
            f"NDVI baseline for month {closest_month:02d}."
        )
    }