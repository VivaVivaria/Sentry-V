import ee
import json
import yaml
from pathlib import Path

from engine.collect_imagery import (
    load_config,
    get_site_geometry,
    collect_imagery
)
from engine.calculate_indices import add_indices
from engine.build_monthly_composite import get_monthly_metric_stats
from engine.create_monthly_record import build_monitoring_record
from engine.calculate_baseline import get_historical_baseline
from engine.calculate_phenophase import get_phenophase_context
from engine.classify_status import classify_vegetation_status
from engine.action_logic import determine_disposition
from engine.signal_fusion import generate_fusion_summary
from validation.quality_checks import assess_confidence
from operations.export_record import save_monitoring_artifact
from operations.system_logger import get_utc_timestamp, save_run_log


def load_profiles(profile_path="config/profiles.yaml"):
    """
    Load ecosystem profiles.
    """
    with open(profile_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def process_metric(
    site_config,
    profile_name,
    ecosystem_profile,
    site_geometry,
    collection_with_indices,
    target_year,
    target_month,
    target_metric,
    phenophase_callback=None
):
    """
    Run the full Sentry-V monitoring pipeline for one site and one metric.

    Example:
    - rouge_eic / NDVI
    - rouge_eic / NDMI
    - tti_mangrove / NDVI
    - tti_mangrove / NDMI

    The phenophase callback only runs during the NDVI pass because NDVI is
    the main seasonal greenness/timing signal.
    """
    started_at = get_utc_timestamp()
    saved_path = None

    site_id = site_config["site_id"]
    site_name = site_config["site_name"]
    target_month_label = f"{target_year}-{target_month:02d}"

    try:
        baseline_start_year = ecosystem_profile.get("baseline_start_year", 2018)
        lookback_years = target_year - baseline_start_year

        print(f"\n   >>> ANALYZING METRIC: {target_metric} <<<")

        print(f"\n[Running] Phase 2C: Monthly {target_metric} Composite")

        monthly_signal, image_count, site_stdev, pixel_count = get_monthly_metric_stats(
            collection=collection_with_indices,
            site_geometry=site_geometry,
            site_id=site_id,
            year=target_year,
            month=target_month,
            metric=target_metric
        )

        # Phase 8D hook:
        # Calculate phenophase only from the NDVI signal.
        if target_metric == "NDVI" and monthly_signal is not None and phenophase_callback is not None:
            phenophase_callback(monthly_signal)

        print("\n[Running] Phase 2D: Monthly Output Record")

        record = build_monitoring_record(
            site_id=site_id,
            site_name=site_name,
            year=target_year,
            month=target_month,
            metric=target_metric,
            mean_value=monthly_signal,
            image_count=image_count,
            site_metric_stdev=site_stdev,
            pixel_count=pixel_count
        )

        print(json.dumps(record, indent=2))
        print("[SUCCESS] Monthly structured record created.")

        print(
            f"\n[Running] Phase 3A: Robust Historical {target_metric} Baseline "
            f"({lookback_years}-Year Lookback to {baseline_start_year})"
        )

        baseline_median, baseline_mad, historical_values = get_historical_baseline(
            collection=collection_with_indices,
            site_geometry=site_geometry,
            site_id=site_id,
            target_month=target_month,
            current_year=target_year,
            metric=target_metric,
            lookback_years=lookback_years
        )

        print(f"\n[Running] Phase 3B: Robust {target_metric} Status Classification")

        status_record = classify_vegetation_status(
            current_value=monthly_signal,
            baseline_median=baseline_median,
            baseline_mad=baseline_mad
        )

        print("\n[Running] Phase 4 + 4D + 4F: Validation Guardrails + Seasonal Logic + Composite Support")

        (
            confidence_level,
            validation_reasons,
            season_status,
            season_note,
            composite_support,
            spatial_status
        ) = assess_confidence(
            current_value=monthly_signal,
            images_used=image_count,
            historical_values=historical_values,
            site_ndvi_stdev=site_stdev,
            pixel_count=pixel_count,
            target_month=target_month,
            profile=ecosystem_profile
        )

        print("\n[Running] Phase 4E: Disposition & Action Logic")

        disposition, recommended_action = determine_disposition(
            classification=status_record["classification"],
            confidence=confidence_level,
            season_status=season_status
        )

        print("\n[Running] Phase 3C: Final Schema Assembly")

        final_record = {
            "site_id": record["site_id"],
            "site_name": record["site_name"],
            "profile": profile_name,
            "month": record["month"],
            "metric": record["metric"],
            "current_value": record["current_value"],
            "site_metric_stdev": record["site_metric_stdev"],
            "pixel_count": record["pixel_count"],
            "baseline_median": round(baseline_median, 4) if baseline_median is not None else None,
            "baseline_mad": round(baseline_mad, 4) if baseline_mad is not None else None,
            "baseline_years_used": len(historical_values) if historical_values else 0,
            "robust_z_score": status_record.get("robust_z_score", status_record.get("z_score")),
            "classification": status_record["classification"],
            "direction": status_record["direction"],
            "confidence": confidence_level,
            "images_used": record["images_used"],
            "historical_values": [round(value, 4) for value in historical_values] if historical_values else [],
            "interpretation": status_record["interpretation"],
            "note": "Detection only. Human interpretation required.",
            "season_status": season_status,
            "season_note": season_note,
            "composite_days": record["images_used"],
            "composite_support": composite_support,
            "spatial_variability_status": spatial_status,
            "disposition": disposition,
            "recommended_action": recommended_action
        }

        if validation_reasons:
            warning_text = ", ".join(validation_reasons)
            final_record["note"] += f" Guardrail warnings: {warning_text}."

        print("\n--- Final Enriched Monitoring Record Production Schema ---")
        print(json.dumps(final_record, indent=2))
        print("[SUCCESS] Production-ready monitoring record created.")

        print("\n[Running] Phase 5: Output Generation")

        saved_path = save_monitoring_artifact(record=final_record)

        finished_at = get_utc_timestamp()

        run_log_path = save_run_log(
            site_id=site_id,
            target_month=target_month_label,
            metric=target_metric,
            status="success",
            started_at=started_at,
            finished_at=finished_at,
            artifact_path=saved_path,
            error=None
        )

        print("\n========================================")
        print(f"   METRIC COMPLETE: {site_id} / {target_metric}")
        print(f"   Artifact: {saved_path}")
        print(f"   Run Log: {run_log_path}")
        print("========================================\n")

        return {
            "result": {
                "site_id": site_id,
                "metric": target_metric,
                "status": "success",
                "artifact": str(saved_path),
                "run_log": str(run_log_path)
            },
            "record": final_record
        }

    except Exception as error:
        finished_at = get_utc_timestamp()

        run_log_path = save_run_log(
            site_id=site_id,
            target_month=target_month_label,
            metric=target_metric,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            artifact_path=saved_path,
            error=error
        )

        print(f"System Error for site {site_id}, metric {target_metric}: {error}")
        print(f"Run Log: {run_log_path}")

        return {
            "result": {
                "site_id": site_id,
                "metric": target_metric,
                "status": "failed",
                "artifact": None,
                "run_log": str(run_log_path),
                "error": str(error)
            },
            "record": None
        }


def save_fusion_artifact(fusion_payload, site_id, formatted_month):
    """
    Save a site-level fusion summary artifact.
    """
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    fusion_path = output_dir / f"{site_id}_{formatted_month}_fusion_summary.json"

    with open(fusion_path, "w", encoding="utf-8") as file:
        json.dump(fusion_payload, file, indent=2)

    print(f"\n[SUCCESS] Fusion summary saved to: {fusion_path}")

    return fusion_path


def process_site(site_config, profiles_config, target_year, target_month):
    """
    Collect imagery once for a site, add all indices once,
    loop through configured metrics, calculate phenophase during NDVI,
    then generate a fusion summary.
    """
    site_id = site_config["site_id"]
    site_name = site_config["site_name"]
    formatted_month = f"{target_year}-{target_month:02d}"

    profile_name = site_config.get("profile", "michigan_deciduous_riparian")

    if profile_name not in profiles_config["profiles"]:
        raise ValueError(f"Profile '{profile_name}' not found in config/profiles.yaml")

    ecosystem_profile = profiles_config["profiles"][profile_name]
    baseline_start_year = ecosystem_profile.get("baseline_start_year", 2018)

    site_geometry = get_site_geometry(site_config)

    print("\n========================================")
    print(f"   PROCESSING SITE: {site_id}")
    print("========================================")
    print(f"Site name: {site_name}")
    print(f"Site profile loaded: {profile_name}")
    print(f"Baseline start year: {baseline_start_year}")

    print("\n[Running] Phase 2A: Imagery Collection")

    single_site_config = {
        "sites": [site_config]
    }

    imagery = collect_imagery(
        site_id=site_id,
        config_data=single_site_config,
        start_year=baseline_start_year,
        end_year=target_year
    )

    print("\n[Running] Phase 2B: Vegetation Index Calculation")
    print("Adding NDVI and NDMI bands to image collection...")

    collection_with_indices = imagery.map(add_indices)

    first_image = collection_with_indices.first()
    band_names = first_image.bandNames().getInfo()

    required_indices = ["NDVI", "NDMI"]
    missing_indices = [band for band in required_indices if band not in band_names]

    if missing_indices:
        print(f"[ERROR] Missing index bands: {missing_indices}")
    else:
        print("[SUCCESS] Sentry-V calculated NDVI and NDMI.")
        print("Bands 'NDVI' and 'NDMI' found.")

    site_results = []
    site_completed_records = []

    site_phenophase_data = {
        "status": "uncertain",
        "closest_month": None,
        "note": "No phenophase calculated."
    }

    def capture_phenophase(current_ndvi):
        """
        Capture phenophase context during the NDVI metric pass.

        Uses the current NDVI value and compares it to historical previous/current/next
        month NDVI baselines.
        """
        nonlocal site_phenophase_data

        lookback_years = target_year - baseline_start_year

        site_phenophase_data = get_phenophase_context(
            collection=collection_with_indices,
            site_geometry=site_geometry,
            site_id=site_id,
            current_year=target_year,
            target_month=target_month,
            current_ndvi=current_ndvi,
            lookback_years=lookback_years
        )

    metrics = site_config.get("metrics", ["NDVI"])

    for target_metric in metrics:
        metric_output = process_metric(
            site_config=site_config,
            profile_name=profile_name,
            ecosystem_profile=ecosystem_profile,
            site_geometry=site_geometry,
            collection_with_indices=collection_with_indices,
            target_year=target_year,
            target_month=target_month,
            target_metric=target_metric,
            phenophase_callback=capture_phenophase
        )

        site_results.append(metric_output["result"])

        if metric_output["record"] is not None:
            site_completed_records.append(metric_output["record"])

    # ==========================================
    #   POST-METRIC FUSION SUMMARY
    # ==========================================
    if len(site_completed_records) > 1:
        fusion_payload = generate_fusion_summary(
            site_id=site_id,
            site_name=site_name,
            profile=profile_name,
            month=formatted_month,
            metric_records=site_completed_records,
            pheno_data=site_phenophase_data
        )

        fusion_path = save_fusion_artifact(
            fusion_payload=fusion_payload,
            site_id=site_id,
            formatted_month=formatted_month
        )

        site_results.append({
            "site_id": site_id,
            "metric": "fusion_summary",
            "status": "success",
            "artifact": str(fusion_path),
            "run_log": None
        })
    else:
        print(f"\n[INFO] Fusion summary skipped for {site_id}. More than one metric is required.")

    print("\n========================================")
    print(f"   SITE COMPLETE: {site_id}")
    print("========================================\n")

    return site_results


def main():
    print("\n========================================")
    print("   SENTRY-V INITIALIZATION SEQUENCE")
    print("========================================")

    target_year = 2026
    target_month = 4

    try:
        ee.Initialize()

        print("\n[Running] Phase 1B: Configuration & Ecosystem Profiles")

        config = load_config()
        profiles_config = load_profiles()

        sites = config.get("sites", [])

        if not sites:
            raise ValueError("No sites found in config/sites.yaml")

        total_sites = len(sites)

        print(f"Found {total_sites} target site(s). Initiating Sentry loop...")

        all_results = []

        for index, site_config in enumerate(sites, start=1):
            print(f"\n\n########## TARGET {index}/{total_sites} ##########")

            site_results = process_site(
                site_config=site_config,
                profiles_config=profiles_config,
                target_year=target_year,
                target_month=target_month
            )

            all_results.extend(site_results)

        print("\n========================================")
        print("   SENTRY-V MULTI-SITE MULTI-METRIC RUN COMPLETE")
        print("========================================")

        print(json.dumps(all_results, indent=2))

    except Exception as error:
        print(f"System Error: {error}")


if __name__ == "__main__":
    main()