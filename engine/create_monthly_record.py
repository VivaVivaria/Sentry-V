def build_monitoring_record(
    site_id,
    site_name,
    year,
    month,
    metric,
    mean_value,
    image_count,
    site_metric_stdev,
    pixel_count
):
    """
    Build a standardized monthly monitoring record for any supported metric.

    Supported examples:
    - NDVI
    - NDMI
    - future EVI
    """
    formatted_month = f"{year}-{month:02d}"

    if mean_value is not None:
        status = "success"
        note = f"Monthly {metric} signal generated from Sentinel-2 imagery."
        rounded_value = round(mean_value, 4)
    else:
        status = "insufficient_data"
        note = "No valid imagery found for this period."
        rounded_value = None

    record = {
        "site_id": site_id,
        "site_name": site_name,
        "month": formatted_month,
        "metric": metric,
        "current_value": rounded_value,
        "site_metric_stdev": round(site_metric_stdev, 4) if site_metric_stdev is not None else None,
        "pixel_count": int(pixel_count) if pixel_count is not None else 0,
        "images_used": image_count,
        "status": status,
        "note": note
    }

    return record