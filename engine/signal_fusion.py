def normalize_climate_context(climate_context=None):
    """
    Normalize climate context into a consistent driver dictionary.

    Supports either:
    1. A full artifact wrapper:
       {
         "artifact_type": "gridmet_climate_drivers",
         "records": [...]
       }

    2. A direct driver dictionary:
       {
         "temperature_mean_c": {...},
         "vpd_mean_kpa": {...}
       }

    Returns:
    {
      "available": bool,
      "drivers": {
        "temperature_mean_c": {...},
        "vpd_mean_kpa": {...},
        "eto_total_mm": {...},
        "precip_total_mm": {...}
      },
      "note": str
    }
    """
    if not climate_context:
        return {
            "available": False,
            "drivers": {},
            "note": "No gridMET climate driver context available."
        }

    # Artifact wrapper format
    if isinstance(climate_context, dict) and "records" in climate_context:
        drivers = {}

        for record in climate_context.get("records", []):
            driver_name = record.get("driver")

            if driver_name:
                drivers[driver_name] = record

        return {
            "available": bool(drivers),
            "drivers": drivers,
            "note": climate_context.get(
                "note",
                "gridMET climate driver context loaded from artifact."
            )
        }

    # Direct driver dictionary format
    if isinstance(climate_context, dict):
        known_drivers = {
            "temperature_mean_c",
            "vpd_mean_kpa",
            "eto_total_mm",
            "precip_total_mm"
        }

        if any(driver in climate_context for driver in known_drivers):
            return {
                "available": True,
                "drivers": climate_context,
                "note": "gridMET climate driver context loaded from direct dictionary."
            }

    return {
        "available": False,
        "drivers": {},
        "note": "Climate context was provided but could not be normalized."
    }


def get_driver(climate_summary, driver_name):
    """
    Safely fetch one climate driver from normalized climate context.
    """
    return climate_summary.get("drivers", {}).get(driver_name, {})


def get_classification(driver_record):
    """
    Safely fetch driver classification.
    """
    return driver_record.get("classification", "insufficient_data")


def get_direction(driver_record):
    """
    Safely fetch driver direction.
    """
    return driver_record.get("direction", "unknown")


def is_high_demand(driver_record):
    """
    Determine whether a VPD or ETo driver indicates elevated atmospheric demand.
    """
    classification = get_classification(driver_record)
    direction = get_direction(driver_record)

    return (
        classification in {
            "high_demand",
            "very_high_demand",
            "above_normal",
            "well_above_normal",
            "unusually_high"
        }
        or direction == "higher_than_expected"
        and driver_record.get("robust_z_score", 0) is not None
        and driver_record.get("robust_z_score", 0) >= 1
    )


def is_normal_demand(driver_record):
    """
    Determine whether a VPD or ETo driver is near expected.
    """
    classification = get_classification(driver_record)
    direction = get_direction(driver_record)

    return (
        classification in {
            "normal_demand",
            "near_normal"
        }
        or direction == "near_expected"
    )


def is_low_demand(driver_record):
    """
    Determine whether a VPD or ETo driver is below expected.
    """
    classification = get_classification(driver_record)
    direction = get_direction(driver_record)

    return (
        classification in {
            "low_demand",
            "very_low_demand",
            "below_normal",
            "well_below_normal",
            "unusually_low"
        }
        or direction == "lower_than_expected"
    )


def is_above_normal_temperature(driver_record):
    """
    Determine whether temperature is above expected.
    """
    classification = get_classification(driver_record)
    direction = get_direction(driver_record)

    return (
        classification in {
            "above_normal",
            "unusually_warm"
        }
        or direction == "higher_than_expected"
        and driver_record.get("robust_z_score", 0) is not None
        and driver_record.get("robust_z_score", 0) >= 1
    )


def build_climate_text(
    climate_summary,
    precipitation_context=None
):
    """
    Build client-safe climate context text.

    This does not diagnose cause.
    It describes whether thermal / atmospheric demand context supports
    or weakens possible review cues.
    """
    if not climate_summary.get("available"):
        return (
            " Climate driver context is unavailable, so thermal and atmospheric "
            "moisture-demand interpretation remains limited."
        )

    precipitation_context = precipitation_context or {}

    temperature = get_driver(climate_summary, "temperature_mean_c")
    vpd = get_driver(climate_summary, "vpd_mean_kpa")
    eto = get_driver(climate_summary, "eto_total_mm")
    gridmet_precip = get_driver(climate_summary, "precip_total_mm")

    temp_class = get_classification(temperature)
    vpd_class = get_classification(vpd)
    eto_class = get_classification(eto)
    gridmet_precip_class = get_classification(gridmet_precip)
    chirps_precip_class = precipitation_context.get("classification", "insufficient_data")

    temp_above = is_above_normal_temperature(temperature)
    vpd_high = is_high_demand(vpd)
    eto_high = is_high_demand(eto)
    vpd_normal = is_normal_demand(vpd)
    eto_normal = is_normal_demand(eto)
    vpd_low = is_low_demand(vpd)
    eto_low = is_low_demand(eto)

    climate_parts = []

    # Thermal + atmospheric demand interpretation
    if temp_above and vpd_normal and eto_normal:
        climate_parts.append(
            " Thermal context is above normal, but atmospheric moisture demand "
            "and reference evapotranspiration remain near expected levels."
        )
    elif vpd_high and eto_high:
        climate_parts.append(
            " Atmospheric moisture demand and reference evapotranspiration are elevated, "
            "which supports review of evaporative-demand pressure as possible context."
        )
    elif vpd_high or eto_high:
        climate_parts.append(
            " At least one atmospheric demand indicator is elevated, so review for "
            "possible moisture-demand pressure in combination with vegetation and field context."
        )
    elif vpd_low or eto_low:
        climate_parts.append(
            " Atmospheric moisture demand is lower than expected, which weakens a heat "
            "or evaporative-stress interpretation for this month."
        )
    elif vpd_normal and eto_normal:
        climate_parts.append(
            " Atmospheric moisture demand and reference evapotranspiration are near expected levels."
        )
    else:
        climate_parts.append(
            " Climate driver context is mixed or uncertain and should be treated as supporting context only."
        )

    # Precipitation source cross-check
    if chirps_precip_class == "above_normal" and gridmet_precip_class == "near_normal":
        climate_parts.append(
            " CHIRPS precipitation is above normal, while gridMET precipitation is near normal; "
            "treat rainfall support as useful context, not proof."
        )
    elif chirps_precip_class == "above_normal" and gridmet_precip_class in {
        "above_normal",
        "well_above_normal"
    }:
        climate_parts.append(
            " CHIRPS and gridMET both support wetter-than-normal precipitation context."
        )
    elif chirps_precip_class == "below_normal" and gridmet_precip_class in {
        "below_normal",
        "well_below_normal"
    }:
        climate_parts.append(
            " CHIRPS and gridMET both support drier-than-normal precipitation context."
        )
    elif chirps_precip_class == "near_normal" and gridmet_precip_class == "near_normal":
        climate_parts.append(
            " CHIRPS and gridMET both indicate near-normal precipitation context."
        )
    elif gridmet_precip_class not in {"insufficient_data", "pending_baseline"}:
        climate_parts.append(
            f" gridMET precipitation cross-check is classified as {gridmet_precip_class}."
        )

    return "".join(climate_parts)


def infer_climate_review_cue(
    ndvi,
    ndmi,
    precipitation_context,
    climate_summary
):
    """
    Infer a review cue from vegetation + precipitation + climate context.

    This is not causation.
    It is a rule-based cue to support human review.
    """
    if not ndvi or not ndmi:
        return "incomplete_data"

    if not climate_summary.get("available"):
        return "climate_context_unavailable"

    temperature = get_driver(climate_summary, "temperature_mean_c")
    vpd = get_driver(climate_summary, "vpd_mean_kpa")
    eto = get_driver(climate_summary, "eto_total_mm")

    precip_class = precipitation_context.get("classification", "insufficient_data")

    ndvi_class = ndvi.get("classification")
    ndmi_class = ndmi.get("classification")

    ndvi_direction = ndvi.get("direction")
    ndmi_direction = ndmi.get("direction")

    temp_above = is_above_normal_temperature(temperature)
    vpd_high = is_high_demand(vpd)
    eto_high = is_high_demand(eto)
    vpd_normal = is_normal_demand(vpd)
    eto_normal = is_normal_demand(eto)

    ndvi_high = ndvi_direction == "higher_than_expected"
    ndmi_high = ndmi_direction == "higher_than_expected"

    ndvi_low = ndvi_direction == "lower_than_expected"
    ndmi_low = ndmi_direction == "lower_than_expected"

    ndvi_normal = ndvi_class == "normal"
    ndmi_normal = ndmi_class == "normal"

    # Moisture-supported / rainfall review cue
    if (
        ndvi_high
        and ndmi_high
        and precip_class == "above_normal"
        and vpd_normal
        and eto_normal
    ):
        return "rainfall_moisture_context_review_cue"

    # Atmospheric demand / drought-stress review cue
    if (
        ndvi_low
        and ndmi_low
        and (vpd_high or eto_high)
        and precip_class in {"below_normal", "near_normal", "insufficient_data"}
    ):
        return "atmospheric_demand_moisture_stress_review_cue"

    # Warm but not thirsty
    if temp_above and vpd_normal and eto_normal:
        return "warm_but_not_thirsty_context"

    # Possible non-climate disturbance cue
    if (
        ndvi_low
        and precip_class == "near_normal"
        and vpd_normal
        and eto_normal
    ):
        return "possible_non_climate_disturbance_review_cue"

    # Resilience / possible irrigation cue
    if (
        ndvi_normal
        and ndmi_normal
        and (vpd_high or eto_high)
    ):
        return "resilience_or_possible_irrigation_context"

    return "general_climate_context"


def build_review_cue_text(review_cue):
    """
    Convert climate review cue into client-safe explanation text.
    """
    if review_cue == "rainfall_moisture_context_review_cue":
        return (
            " This supports a rainfall or moisture-context review cue rather than "
            "a heat or evaporative-stress cue."
        )

    if review_cue == "atmospheric_demand_moisture_stress_review_cue":
        return (
            " Elevated atmospheric moisture demand supports a drought or moisture-stress "
            "review cue, but field context is required."
        )

    if review_cue == "warm_but_not_thirsty_context":
        return (
            " The month was warmer than normal, but the atmosphere was not unusually "
            "thirsty, so heat stress is not strongly supported by the climate drivers alone."
        )

    if review_cue == "possible_non_climate_disturbance_review_cue":
        return (
            " Vegetation change is not strongly supported by rainfall or atmospheric "
            "demand context. Review imagery for local disturbance, mowing, clearing, "
            "pest damage, or site management changes."
        )

    if review_cue == "resilience_or_possible_irrigation_context":
        return (
            " Vegetation remained stable despite elevated atmospheric demand. This may "
            "indicate site resilience, supplemental watering, or tolerant vegetation."
        )

    if review_cue == "climate_context_unavailable":
        return (
            " Climate driver context is unavailable, so review cue confidence is limited."
        )

    return (
        " Climate drivers provide supporting context but do not independently explain the signal."
    )


def generate_fusion_summary(
    site_id,
    site_name,
    profile,
    month,
    metric_records,
    pheno_data=None,
    precipitation_context=None,
    climate_context=None
):
    """
    Synthesize multiple vegetation metric records, phenophase timing,
    precipitation context, and gridMET climate driver context into a single
    site-level ecological hypothesis.

    This does not diagnose causation.
    It provides detection support for human review.

    Inputs:
    - NDVI: vegetation greenness/activity
    - NDMI: canopy moisture
    - Phenophase: seasonal timing
    - CHIRPS precipitation: rainfall context
    - gridMET temperature: thermal context
    - gridMET VPD: atmospheric thirst / moisture demand context
    - gridMET ETo: evaporative demand context
    - gridMET precipitation: secondary precipitation cross-check
    """
    print(
        "\n[Running] Phase 8C, 8D, 8E & 11C: "
        "Signal Fusion + Phenophase + Precipitation + Climate Driver Summary"
    )

    pheno_data = pheno_data or {
        "status": "uncertain",
        "closest_month": None,
        "note": "No phenophase context available."
    }

    precipitation_context = precipitation_context or {
        "classification": "insufficient_data",
        "note": "Precipitation context was not calculated."
    }

    climate_summary = normalize_climate_context(climate_context)

    signals = {}

    for record in metric_records:
        metric = record["metric"]

        signals[metric] = {
            "classification": record["classification"],
            "direction": record["direction"],
            "confidence": record["confidence"],
            "current_value": record["current_value"],
            "robust_z_score": record["robust_z_score"],
            "disposition": record["disposition"]
        }

    ndvi = signals.get("NDVI")
    ndmi = signals.get("NDMI")

    pheno_status = pheno_data.get("status", "uncertain")
    precip_classification = precipitation_context.get("classification", "insufficient_data")

    # ------------------------------------------
    # Phenophase text helper
    # ------------------------------------------
    if pheno_status == "early":
        pheno_text = " The site appears to be undergoing early seasonal development."
    elif pheno_status == "delayed":
        pheno_text = " The site appears to be showing delayed seasonal development."
    elif pheno_status == "expected":
        pheno_text = " Seasonal timing appears close to the expected baseline."
    else:
        pheno_text = " Seasonal timing is uncertain."

    # ------------------------------------------
    # Precipitation text helper
    # ------------------------------------------
    if precip_classification == "below_normal":
        precip_text = (
            " CHIRPS precipitation context is below normal for this month, which may support "
            "review of moisture limitation as one possible factor."
        )
    elif precip_classification == "above_normal":
        precip_text = (
            " CHIRPS precipitation context is above normal for this month, so review for "
            "rainfall-related site conditions such as saturated soils, flooding, drainage, "
            "storm effects, or favorable moisture support."
        )
    elif precip_classification == "near_normal":
        precip_text = (
            " CHIRPS precipitation context is near normal for this month, so rainfall alone does "
            "not strongly explain the vegetation signal."
        )
    else:
        precip_text = (
            " CHIRPS precipitation context is unavailable or insufficient, so weather-driver "
            "interpretation remains limited."
        )

    climate_text = build_climate_text(
        climate_summary=climate_summary,
        precipitation_context=precipitation_context
    )

    climate_review_cue = infer_climate_review_cue(
        ndvi=ndvi,
        ndmi=ndmi,
        precipitation_context=precipitation_context,
        climate_summary=climate_summary
    )

    review_cue_text = build_review_cue_text(climate_review_cue)

    driver_context_text = (
        f"{pheno_text}"
        f"{precip_text}"
        f"{climate_text}"
        f"{review_cue_text}"
    )

    # ------------------------------------------
    # Main fusion logic
    # ------------------------------------------
    if not ndvi or not ndmi:
        hypothesis = (
            "Insufficient metrics for fusion. Both NDVI and NDMI records are required."
            f"{driver_context_text}"
        )
        fusion_disposition = "incomplete_data"

    elif ndvi["classification"] == "normal" and ndmi["classification"] == "normal":
        hypothesis = (
            "Vegetation activity and canopy moisture are both within expected seasonal ranges."
            f"{driver_context_text} Stable baseline conditions."
        )
        fusion_disposition = "routine_log"

    elif ndvi["classification"] == "normal" and ndmi["direction"] == "lower_than_expected":
        hypothesis = (
            "Canopy greenness remains within expected range, but canopy moisture signal is "
            f"lower than expected for this month.{driver_context_text} Review next month "
            "for persistence and compare with imagery, field notes, and site context."
        )
        fusion_disposition = "watch_signal"

    elif ndvi["direction"] == "higher_than_expected" and ndmi["direction"] == "higher_than_expected":
        hypothesis = (
            "Vegetation activity is higher than expected and supported by higher-than-expected "
            f"canopy moisture.{driver_context_text} Review imagery, field conditions, and "
            "site context before interpretation."
        )
        fusion_disposition = "reportable_signal"

    elif ndvi["direction"] == "lower_than_expected" and ndmi["direction"] == "lower_than_expected":
        hypothesis = (
            "Both vegetation activity and canopy moisture signals are lower than expected."
            f"{driver_context_text} This may indicate a stronger vegetation stress signal, "
            "but human interpretation, imagery review, weather context, and field observations "
            "are required."
        )
        fusion_disposition = "reportable_signal"

    elif ndvi["direction"] == "lower_than_expected" and ndmi["direction"] != "lower_than_expected":
        hypothesis = (
            "Vegetation greenness is lower than expected, but canopy moisture is not similarly low."
            f"{driver_context_text} Review for possible phenology, canopy structure, disturbance, "
            "or data context rather than assuming moisture stress."
        )
        fusion_disposition = "watch_signal"

    else:
        hypothesis = (
            f"Complex signal detected. NDVI is {ndvi['classification']} "
            f"({ndvi['direction']}) while NDMI is {ndmi['classification']} "
            f"({ndmi['direction']}).{driver_context_text} Manual interpretation required."
        )
        fusion_disposition = "watch_signal"

    fusion_record = {
        "site_id": site_id,
        "site_name": site_name,
        "profile": profile,
        "month": month,
        "phenophase_context": pheno_data,
        "precipitation_context": precipitation_context,
        "climate_driver_context": climate_summary,
        "climate_review_cue": climate_review_cue,
        "signal_summary": signals,
        "hypothesis": hypothesis,
        "fusion_disposition": fusion_disposition,
        "note": (
            "Fusion summary is detection support only. "
            "Precipitation and climate driver context do not establish causation. "
            "Human interpretation required."
        )
    }

    print(f"Fusion Hypothesis: {hypothesis}")
    print(f"Climate Review Cue: {climate_review_cue}")
    print(f"Fusion Disposition: {fusion_disposition}")

    return fusion_record