import ee


def get_monthly_metric_stats(
    collection,
    site_geometry,
    site_id,
    year,
    month,
    metric,
    quiet=False
):
    """
    Build a monthly composite and calculate site-level statistics
    for the target metric.

    Returns:
    - metric mean
    - image count
    - site metric standard deviation
    - pixel count
    """
    monthly_collection = (
        collection
        .filter(ee.Filter.calendarRange(year, year, "year"))
        .filter(ee.Filter.calendarRange(month, month, "month"))
    )

    image_count = monthly_collection.size().getInfo()

    if image_count == 0:
        if not quiet:
            print(f"\n[WARNING] No images found for site: {site_id} in {year}-{month:02d}")
        return None, 0, None, None

    composite = monthly_collection.median()
    metric_composite = composite.select(metric)

    combined_reducer = (
        ee.Reducer.mean()
        .combine(reducer2=ee.Reducer.stdDev(), sharedInputs=True)
        .combine(reducer2=ee.Reducer.count(), sharedInputs=True)
    )

    stats = metric_composite.reduceRegion(
        reducer=combined_reducer,
        geometry=site_geometry,
        scale=10,
        maxPixels=1e9
    )

    mean_value = stats.get(f"{metric}_mean").getInfo()
    site_metric_stdev = stats.get(f"{metric}_stdDev").getInfo()
    pixel_count = stats.get(f"{metric}_count").getInfo()

    if mean_value is None:
        if not quiet:
            print(f"\n[WARNING] Mean {metric} is missing/null for site: {site_id} in {year}-{month:02d}")
        return None, image_count, None, None

    if not quiet:
        print(f"\n--- Phase 2C: Monthly {metric} Composite ---")
        print(f"Site: {site_id}")
        print(f"Month: {year}-{month:02d}")
        print(f"Images used: {image_count}")
        print(f"Mean {metric}: {mean_value:.4f}")

        if site_metric_stdev is not None:
            print(f"Site {metric} StDev: {site_metric_stdev:.4f}")

        if pixel_count is not None:
            print(f"Pixel count: {int(pixel_count)}")

        print(f"[SUCCESS] Monthly {metric} signal generated.")

    return mean_value, image_count, site_metric_stdev, pixel_count