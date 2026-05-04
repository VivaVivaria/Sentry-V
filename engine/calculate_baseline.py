from statistics import median
from engine.build_monthly_composite import get_monthly_metric_stats


def calculate_mad(values):
    """
    Calculate Median Absolute Deviation.

    MAD = median(|x - median(x)|)
    """
    baseline_median = median(values)
    absolute_deviations = [abs(value - baseline_median) for value in values]

    return median(absolute_deviations)


def get_historical_baseline(
    collection,
    site_geometry,
    site_id,
    target_month,
    current_year,
    metric,
    lookback_years=8
):
    """
    Calculate a same-month historical baseline for the selected metric
    using robust statistics.

    Uses:
    - median
    - MAD: Median Absolute Deviation
    """
    historical_values = []

    print(f"\n--- Phase 3A: Robust Historical {metric} Values ---")
    print(f"Target month: {target_month:02d}")
    print(f"Lookback window: {lookback_years} years")

    start_year = current_year - lookback_years
    end_year = current_year - 1

    print(f"Historical years: {start_year} to {end_year}")

    for year in range(start_year, current_year):
        mean_value, image_count, _, _ = get_monthly_metric_stats(
            collection=collection,
            site_geometry=site_geometry,
            site_id=site_id,
            year=year,
            month=target_month,
            metric=metric,
            quiet=True
        )

        if mean_value is not None:
            historical_values.append(mean_value)
            print(f"{year}-{target_month:02d}: {metric} = {mean_value:.4f} | images used = {image_count}")
        else:
            print(f"{year}-{target_month:02d}: insufficient data")

    if not historical_values:
        print(f"[WARNING] No historical {metric} values found. Baseline cannot be calculated.")
        return None, None, []

    baseline_median = median(historical_values)

    if len(historical_values) > 1:
        baseline_mad = calculate_mad(historical_values)
    else:
        baseline_mad = 0.0

    print(f"\n[SUCCESS] Robust {metric} historical baseline calculated.")
    print(f"Historical values used: {[round(value, 4) for value in historical_values]}")
    print(f"Baseline median: {baseline_median:.4f}")
    print(f"Baseline MAD: {baseline_mad:.4f}")

    return baseline_median, baseline_mad, historical_values