def assess_confidence(
    current_value,
    images_used,
    historical_values,
    site_ndvi_stdev=None,
    pixel_count=None,
    target_month=None,
    profile=None
):
    """
    Evaluate the reliability of the monthly monitoring record.

    This checks:
    - seasonal context
    - NDVI physical bounds
    - composite temporal support
    - site internal NDVI spread
    - pixel support
    - historical baseline strength
    """
    print("\n--- Phase 4, 4D & 4F: Validation Guardrails ---")

    profile = profile or {}

    confidence_penalties = 0
    reasons = []

    season_status = "active"
    season_note = "No seasonal profile note available."

    active_months = profile.get("active_months", [])
    shoulder_months = profile.get("shoulder_months", [])
    dormant_months = profile.get("dormant_months", [])
    seasonal_notes = profile.get("seasonal_notes", {})

    ndvi_spread_high = profile.get("ndvi_spread_high", 0.30)
    min_pixel_count = profile.get("min_pixel_count", 50)
    min_baseline_years = profile.get("min_baseline_years", 3)
    min_composite_days = profile.get("min_composite_days", 4)

    composite_days = images_used if images_used is not None else 0
    composite_support = "unknown"
    spatial_variability_status = "unknown"

    # 1. Seasonal context.
    if target_month in dormant_months:
        season_status = "dormant"
        season_note = seasonal_notes.get(
            "dormant",
            "Vegetation anomaly interpretation is weak during dormant season."
        )
        confidence_penalties += 2
        reasons.append("Dormant season: vegetation anomaly alerts suppressed")
        print("[WARN] Target month is in dormant season.")

    elif target_month in shoulder_months:
        season_status = "shoulder"
        season_note = seasonal_notes.get(
            "shoulder",
            "Shoulder-season interpretation should be treated as provisional."
        )
        confidence_penalties += 1
        reasons.append("Shoulder season: provisional interpretation only")
        print("[WARN] Target month is in shoulder season.")

    elif target_month in active_months:
        season_status = "active"
        season_note = seasonal_notes.get(
            "active",
            "Vegetation interpretation is most reliable during active season."
        )
        print("[PASS] Target month is in active growing season.")

    else:
        season_status = "unknown"
        season_note = "Target month is not assigned to an ecosystem season profile."
        confidence_penalties += 1
        reasons.append("Target month missing from ecosystem profile")
        print("[WARN] Target month is not assigned to active, shoulder, or dormant months.")

    # 2. NDVI physical bounds.
    if current_value is None:
        print("[FAIL] Current NDVI value is missing.")
        return (
            "low",
            ["Missing current NDVI value"],
            season_status,
            season_note,
            "none",
            spatial_variability_status
        )

    if current_value < -1.0 or current_value > 1.0:
        print("[FAIL] NDVI value is outside physical bounds.")
        return (
            "low",
            ["NDVI value outside physical bounds"],
            season_status,
            season_note,
            "none",
            spatial_variability_status
        )

    print("[PASS] NDVI value is within physical bounds.")

    # 3. Composite temporal support.
    if composite_days == 0:
        print("[FAIL] No imagery available for current month.")
        return (
            "low",
            ["No imagery available for current month"],
            season_status,
            season_note,
            "none",
            spatial_variability_status
        )

    if composite_days < min_composite_days:
        confidence_penalties += 1
        composite_support = "low"
        reasons.append(f"Low composite support: {composite_days} days < {min_composite_days}")
        print(f"[WARN] Low composite support: {composite_days} days < {min_composite_days}")
    else:
        composite_support = "sufficient"
        print(f"[PASS] Sufficient composite support: {composite_days} days")

    # 4. Internal NDVI spread.
    if site_ndvi_stdev is None:
        confidence_penalties += 1
        spatial_variability_status = "unknown"
        reasons.append("Missing site NDVI spread")
        print("[WARN] Site NDVI spread is missing.")

    elif site_ndvi_stdev > ndvi_spread_high:
        confidence_penalties += 1
        spatial_variability_status = "high"
        reasons.append(f"High internal NDVI spread: {site_ndvi_stdev:.3f} > {ndvi_spread_high}")
        print(f"[WARN] High internal NDVI spread: {site_ndvi_stdev:.3f} > {ndvi_spread_high}")

    else:
        spatial_variability_status = "acceptable"
        print(f"[PASS] Site internal NDVI spread acceptable: {site_ndvi_stdev:.3f}")

    # 5. Pixel count.
    if pixel_count is None or pixel_count == 0:
        confidence_penalties += 1
        reasons.append("Missing or zero valid pixel count")
        print("[WARN] Pixel count is missing or zero.")

    elif pixel_count < min_pixel_count:
        confidence_penalties += 1
        reasons.append(f"Critically low pixel count: {pixel_count} < {min_pixel_count}")
        print(f"[WARN] Critically low pixel count: {pixel_count} < {min_pixel_count}")

    else:
        print(f"[PASS] Sufficient pixel count: {pixel_count}")

    # 6. Historical baseline sample size.
    baseline_years = len(historical_values) if historical_values else 0

    if baseline_years < min_baseline_years:
        confidence_penalties += 1
        reasons.append(f"Weak historical baseline: {baseline_years} years < {min_baseline_years}")
        print(f"[WARN] Weak historical baseline: {baseline_years} years < {min_baseline_years}")

    else:
        print(f"[PASS] Solid historical baseline: {baseline_years} years")

    # 7. Assign confidence.
    if confidence_penalties == 0:
        confidence = "high"
    elif confidence_penalties == 1:
        confidence = "medium"
    else:
        confidence = "low"

    print(f"Season status: {season_status.upper()}")
    print(f"Composite support: {composite_support.upper()}")
    print(f"Spatial variability: {spatial_variability_status.upper()}")
    print(f"Validation complete. Confidence: {confidence.upper()}")

    return (
        confidence,
        reasons,
        season_status,
        season_note,
        composite_support,
        spatial_variability_status
    )