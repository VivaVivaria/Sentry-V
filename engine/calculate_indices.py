import ee


def add_indices(image):
    """
    Calculate and add vegetation index bands to a Sentinel-2 image.

    NDVI:
    - Proxy for vegetation greenness/activity
    - Formula: (NIR - Red) / (NIR + Red)
    - Sentinel-2: B8 and B4

    NDMI:
    - Proxy for vegetation/canopy moisture
    - Formula: (NIR - SWIR1) / (NIR + SWIR1)
    - Sentinel-2: B8 and B11
    """
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    ndmi = image.normalizedDifference(["B8", "B11"]).rename("NDMI")

    return image.addBands([ndvi, ndmi])