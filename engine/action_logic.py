def determine_disposition(classification, confidence, season_status):
    """
    Translate classification, confidence, and seasonal context into
    an operational disposition and recommended human action.

    This function does not diagnose causes.
    It only decides how the signal should be handled.
    """
    print("\n--- Phase 4E: Disposition & Action Logic ---")

    if season_status == "dormant":
        disposition = "suppressed"
        recommended_action = (
            "Do not trigger vegetation alert. Wait for active-season data "
            "and review supporting context only."
        )

    elif confidence == "low":
        disposition = "unreliable_data"
        recommended_action = (
            "Do not treat this as confirmed vegetation change. Inspect imagery "
            "for contamination, low pixel support, or unstable compositing."
        )

    elif season_status == "shoulder" and classification != "normal":
        disposition = "provisional_signal"
        recommended_action = (
            "Do not trigger alert from this month alone. Shoulder-season interpretation "
            "is provisional. Re-check next month for persistence."
        )

    elif classification == "normal":
        disposition = "routine_log"
        recommended_action = (
            "No action required. File record and continue routine monitoring."
        )

    elif classification == "watch":
        disposition = "watch_signal"
        recommended_action = (
            "Review next monthly run for persistence. Compare with weather, site context, "
            "and imagery before escalating."
        )

    elif classification == "unusual" and confidence in ["high", "medium"] and season_status == "active":
        disposition = "reportable_signal"
        recommended_action = (
            "Review imagery and compare with weather/site context. Escalate only if "
            "the deviation persists across adjacent months or aligns with field concerns."
        )

    else:
        disposition = "review_needed"
        recommended_action = (
            "Review the monitoring record manually before deciding whether to escalate."
        )

    print(f"Disposition: {disposition.upper()}")
    print(f"Recommended Action: {recommended_action}")

    return disposition, recommended_action