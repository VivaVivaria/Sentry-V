def generate_fusion_summary(site_id, site_name, profile, month, metric_records, pheno_data=None):
    """
    Synthesize multiple metric records and phenophase timing into a single
    site-level ecological hypothesis.

    This does not diagnose causation.
    It provides detection support for human review.
    """
    print("\n[Running] Phase 8C & 8D: Signal Fusion + Phenophase Summary")

    pheno_data = pheno_data or {
        "status": "uncertain",
        "closest_month": None,
        "note": "No phenophase context available."
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

    if pheno_status == "early":
        pheno_text = " The site appears to be undergoing early seasonal development."
    elif pheno_status == "delayed":
        pheno_text = " The site appears to be showing delayed seasonal development."
    elif pheno_status == "expected":
        pheno_text = " Seasonal timing appears close to the expected baseline."
    else:
        pheno_text = " Seasonal timing is uncertain."

    if not ndvi or not ndmi:
        hypothesis = "Insufficient metrics for fusion. Both NDVI and NDMI records are required."
        fusion_disposition = "incomplete_data"

    elif ndvi["classification"] == "normal" and ndmi["classification"] == "normal":
        hypothesis = (
            "Vegetation activity and canopy moisture are both within expected seasonal ranges."
            f"{pheno_text} Stable baseline conditions."
        )
        fusion_disposition = "routine_log"

    elif ndvi["classification"] == "normal" and ndmi["direction"] == "lower_than_expected":
        hypothesis = (
            "Canopy greenness remains within expected range, but canopy moisture signal is "
            f"lower than expected for this month.{pheno_text} Review next month for persistence "
            "and compare with precipitation context."
        )
        fusion_disposition = "watch_signal"

    elif ndvi["direction"] == "higher_than_expected" and ndmi["direction"] == "higher_than_expected":
        hypothesis = (
            "Vegetation activity is higher than expected and supported by higher-than-expected "
            f"canopy moisture.{pheno_text} Review imagery and weather context before interpretation."
        )
        fusion_disposition = "reportable_signal"

    elif ndvi["direction"] == "lower_than_expected" and ndmi["direction"] == "lower_than_expected":
        hypothesis = (
            "Both vegetation activity and canopy moisture signals are lower than expected."
            f"{pheno_text} This may indicate a stronger vegetation stress signal, but human "
            "interpretation and weather/site context are required."
        )
        fusion_disposition = "reportable_signal"

    elif ndvi["direction"] == "lower_than_expected" and ndmi["direction"] != "lower_than_expected":
        hypothesis = (
            "Vegetation greenness is lower than expected, but canopy moisture is not similarly low."
            f"{pheno_text} Review for possible phenology, canopy structure, disturbance, or data "
            "context rather than assuming moisture stress."
        )
        fusion_disposition = "watch_signal"

    else:
        hypothesis = (
            f"Complex signal detected. NDVI is {ndvi['classification']} "
            f"({ndvi['direction']}) while NDMI is {ndmi['classification']} "
            f"({ndmi['direction']}).{pheno_text} Manual interpretation required."
        )
        fusion_disposition = "watch_signal"

    fusion_record = {
        "site_id": site_id,
        "site_name": site_name,
        "profile": profile,
        "month": month,
        "phenophase_context": pheno_data,
        "signal_summary": signals,
        "hypothesis": hypothesis,
        "fusion_disposition": fusion_disposition,
        "note": "Fusion summary is detection support only. Human interpretation required."
    }

    print(f"Fusion Hypothesis: {hypothesis}")
    print(f"Fusion Disposition: {fusion_disposition}")

    return fusion_record