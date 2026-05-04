def classify_vegetation_status(current_value, baseline_median, baseline_mad):
    """
    Compare the current monthly NDVI against the historical same-month baseline
    using a robust z-score.

    Robust z-score formula:

    robust_z = 0.6745 * (current_value - baseline_median) / MAD

    This function does not diagnose plant health.
    It only classifies whether vegetation activity is within, near, or outside
    the expected seasonal range.
    """
    print("\n--- Phase 3B: Robust Status Classification ---")

    if current_value is None or baseline_median is None:
        print("[ERROR] Missing current or baseline data. Cannot classify.")

        return {
            "classification": "insufficient_data",
            "direction": "unknown",
            "robust_z_score": None,
            "interpretation": "Cannot classify due to missing current or baseline data."
        }

    if baseline_mad is None or baseline_mad == 0:
        print("[WARNING] Baseline MAD is missing or zero. Cannot calculate robust z-score.")

        return {
            "classification": "watch",
            "direction": "unknown",
            "robust_z_score": None,
            "interpretation": "Historical variation is too low or unavailable for a reliable robust z-score."
        }

    robust_z_score = 0.6745 * (current_value - baseline_median) / baseline_mad
    abs_z = abs(robust_z_score)

    if abs_z < 1.0:
        classification = "normal"
    elif abs_z < 2.5:
        classification = "watch"
    else:
        classification = "unusual"

    if robust_z_score > 0:
        direction = "higher_than_expected"
        direction_text = "high"
    elif robust_z_score < 0:
        direction = "lower_than_expected"
        direction_text = "low"
    else:
        direction = "within_expected_range"
        direction_text = "expected"

    if classification == "normal":
        interpretation = "Vegetation activity is within the expected seasonal range."
    elif classification == "watch":
        interpretation = f"Watch-level {direction_text} vegetation activity detected."
    else:
        interpretation = f"Unusual {direction_text} vegetation activity detected."

    print(f"Current Value: {current_value:.4f}")
    print(f"Baseline Median: {baseline_median:.4f}")
    print(f"Baseline MAD: {baseline_mad:.4f}")
    print(f"Robust Z-score: {robust_z_score:.2f}")
    print(f"Final Status: {classification.upper()} ({direction})")

    return {
        "classification": classification,
        "direction": direction,
        "robust_z_score": round(robust_z_score, 2),
        "interpretation": interpretation
    }