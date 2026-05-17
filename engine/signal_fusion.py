def generate_fusion_summary(
    site_id,
    site_name,
    profile,
    month,
    metric_records,
    pheno_data=None,
    precipitation_context=None
):
    """
    Synthesize multiple vegetation metric records, phenophase timing,
    and precipitation context into a single site-level ecological hypothesis.

    This does not diagnose causation.
    It provides detection support for human review.

    Inputs:
    - NDVI: vegetation greenness/activity
    - NDMI: canopy moisture
    - Phenophase: seasonal timing
    - Precipitation: environmental driver context
    """
    print("\n[Running] Phase 8C, 8D & 8E: Signal Fusion + Phenophase + Precipitation Summary")

    pheno_data = pheno_data or {
        "status": "uncertain",
        "closest_month": None,
        "note": "No phenophase context available."
    }

    precipitation_context = precipitation_context or {
        "classification": "insufficient_data",
        "note": "Precipitation context was not calculated."
    }

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
            " Precipitation context is below normal for this month, which may support "
            "review of moisture limitation as one possible factor."
        )
    elif precip_classification == "above_normal":
        precip_text = (
            " Precipitation context is above normal for this month, so review for "
            "rainfall-related site conditions such as saturated soils, flooding, drainage, "
            "storm effects, or favorable moisture support."
        )
    elif precip_classification == "near_normal":
        precip_text = (
            " Precipitation context is near normal for this month, so rainfall alone does "
            "not strongly explain the vegetation signal."
        )
    else:
        precip_text = (
            " Precipitation context is unavailable or insufficient, so weather-driver "
            "interpretation remains limited."
        )

    # ------------------------------------------
    # Main fusion logic
    # ------------------------------------------
    if not ndvi or not ndmi:
        hypothesis = (
            "Insufficient metrics for fusion. Both NDVI and NDMI records are required."
            f"{pheno_text}{precip_text}"
        )
        fusion_disposition = "incomplete_data"

    elif ndvi["classification"] == "normal" and ndmi["classification"] == "normal":
        hypothesis = (
            "Vegetation activity and canopy moisture are both within expected seasonal ranges."
            f"{pheno_text}{precip_text} Stable baseline conditions."
        )
        fusion_disposition = "routine_log"

    elif ndvi["classification"] == "normal" and ndmi["direction"] == "lower_than_expected":
        hypothesis = (
            "Canopy greenness remains within expected range, but canopy moisture signal is "
            f"lower than expected for this month.{pheno_text}{precip_text} Review next month "
            "for persistence and compare with imagery, field notes, and site context."
        )
        fusion_disposition = "watch_signal"

    elif ndvi["direction"] == "higher_than_expected" and ndmi["direction"] == "higher_than_expected":
        hypothesis = (
            "Vegetation activity is higher than expected and supported by higher-than-expected "
            f"canopy moisture.{pheno_text}{precip_text} Review imagery and field/weather context "
            "before interpretation."
        )
        fusion_disposition = "reportable_signal"

    elif ndvi["direction"] == "lower_than_expected" and ndmi["direction"] == "lower_than_expected":
        hypothesis = (
            "Both vegetation activity and canopy moisture signals are lower than expected."
            f"{pheno_text}{precip_text} This may indicate a stronger vegetation stress signal, "
            "but human interpretation, imagery review, weather context, and field observations "
            "are required."
        )
        fusion_disposition = "reportable_signal"

    elif ndvi["direction"] == "lower_than_expected" and ndmi["direction"] != "lower_than_expected":
        hypothesis = (
            "Vegetation greenness is lower than expected, but canopy moisture is not similarly low."
            f"{pheno_text}{precip_text} Review for possible phenology, canopy structure, disturbance, "
            "or data context rather than assuming moisture stress."
        )
        fusion_disposition = "watch_signal"

    else:
        hypothesis = (
            f"Complex signal detected. NDVI is {ndvi['classification']} "
            f"({ndvi['direction']}) while NDMI is {ndmi['classification']} "
            f"({ndmi['direction']}).{pheno_text}{precip_text} Manual interpretation required."
        )
        fusion_disposition = "watch_signal"

    fusion_record = {
        "site_id": site_id,
        "site_name": site_name,
        "profile": profile,
        "month": month,
        "phenophase_context": pheno_data,
        "precipitation_context": precipitation_context,
        "signal_summary": signals,
        "hypothesis": hypothesis,
        "fusion_disposition": fusion_disposition,
        "note": (
            "Fusion summary is detection support only. "
            "Precipitation context does not establish causation. "
            "Human interpretation required."
        )
    }

    print(f"Fusion Hypothesis: {hypothesis}")
    print(f"Fusion Disposition: {fusion_disposition}")

    return fusion_record