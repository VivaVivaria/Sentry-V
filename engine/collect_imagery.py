import ee
import yaml
from pathlib import Path


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