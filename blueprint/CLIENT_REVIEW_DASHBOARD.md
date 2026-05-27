# Sentry-V Client Review Dashboard Blueprint

This document defines the client-facing dashboard direction for Sentry-V.

The Client Review Dashboard is designed for conservation organizations, field teams, and environmental stakeholders. Unlike the Operator Dashboard, its purpose is not to expose every raw data field. Its purpose is to explain what needs review, why it matters, what evidence supports the review cue, and what action should happen next.

---

## Dashboard Name

```text
Sentry-V Client Review Dashboard
```

Product context:

```text
Sentry-V Environmental Dashboard
Client Review Dashboard • Conservation Operations
```

Current prototype status:

```text
Client Review Dashboard mockup v1.1
```

Primary audience:

```text
Conservation organizations
field teams
environmental stakeholders
pilot partners
```

---

## Purpose

The Client Review Dashboard answers:

```text
What site needs attention?
What happened this month?
Why was it flagged?
What action is recommended?
How does the current signal compare to historical seasonal behavior?
```

It should feel like a calm environmental review terminal, not a raw analytics table.

---

## Core Design Principle

Client-facing hierarchy:

```text
Alert → Takeaway → Hypothesis → Action → Historical Trend Evidence
```

The dashboard should make the client remember the interpretation, not just the numbers.

Example:

```text
Vegetation activity is higher than expected during a wetter-than-normal month.
```

is more client-useful than:

```text
NDVI = 0.4834
NDMI = -0.1056
```

Raw metrics are supporting evidence, not the headline.

---

## Layout Structure

Current one-page client layout:

```text
1. Left Sidebar / Reportable Signals Feed
2. Site Identity Header
3. Main Review Card
4. Historical Context Explorer
5. Detection ≠ Causation footer
```

Removed from the main client layout:

```text
Supporting Evidence pill row
Site Metric Cards
```

Reason:

These were useful internally, but they created extra cognitive load and competed with the trend graph. The historical graph now acts as the primary evidence feature.

---

## Left Sidebar / Reportable Signals Feed

Purpose:

```text
Show which sites currently need attention.
```

Example site cards:

```text
Rouge EIC
42.315764, -83.239361
Review Required
```

```text
TTI Mangrove
Florida mangrove
Routine Log
```

The sidebar should be compact and should not repeat the full hypothesis or review cue.

---

## Site Identity Header

Current site name:

```text
Lower Rouge Riparian
```

Location:

```text
42.315764, -83.239361
```

Month:

```text
Apr 2026
```

Status:

```text
Review Required
```

Avoid repeating phenophase in the top identity row. Phenophase context should be shown through the Historical Context Explorer and optional phenophase overlay.

---

## Main Review Card

The Main Review Card is the primary client explanation block.

It contains:

```text
Main Takeaway
Hypothesis
Recommended Action
```

### Main Takeaway

For Rouge EIC:

```text
Vegetation activity is higher than expected during a wetter-than-normal month.
```

For TTI Mangrove:

```text
Vegetation and canopy moisture are within expected seasonal ranges.
```

### Hypothesis

Rouge EIC hypothesis:

```text
Higher-than-expected vegetation activity and canopy moisture, combined with above-normal precipitation, suggest a rainfall-related review cue. Review for saturated soils, flooding, drainage issues, storm effects, or favorable moisture support.
```

TTI Mangrove hypothesis:

```text
The site appears stable for April 2026. Early phenophase is noted, but rainfall is near normal and no immediate reportable vegetation or moisture signal is present.
```

### Recommended Action

Rouge EIC recommended action:

```text
Review recent imagery, precipitation context, and field conditions before interpretation. Escalate only if the signal persists across adjacent months or aligns with field concerns.
```

TTI Mangrove recommended action:

```text
Routine log. No immediate field review required. Continue routine monitoring.
```

---

## Historical Context Explorer

The Historical Context Explorer is the defining evidence feature of the client dashboard.

Purpose:

```text
Show how the current month compares to historical seasonal behavior.
```

It helps clients see that Sentry-V is not reacting to isolated numbers. It is comparing the current month against the site's historical ecological rhythm.

### Module Title

```text
Historical Context Explorer
```

Subtitle:

```text
Compare current monthly signals against historical seasonal behavior.
```

### Controls

Site selector:

```text
Rouge EIC
TTI Mangrove
```

Metric toggle:

```text
NDVI
NDMI
Precipitation
```

Optional toggles:

```text
Hide / Show Historical Baseline
Phenophase Overlay
Compare Metrics
```

### Terminology

Use:

```text
Historical Baseline
```

instead of:

```text
Expected Baseline
```

Reason:

Expected can sound like a forecast. Historical Baseline better communicates that the dashed comparison line is derived from prior seasonal behavior.

---

## Metric Color System

Use intuitive metric colors:

```text
NDVI = green
NDMI = purplish blue / indigo
Precipitation = blue
Historical Baseline = neutral gray dashed line
```

Metric toggles should include small colored dots:

```text
NDVI toggle → green dot
NDMI toggle → purple-blue dot
Precipitation toggle → blue dot
```

---

## Trend Chart Behavior

The chart should show:

```text
Actual/current year line
Historical Baseline dashed line
Highlighted current reporting month
Annotation callout
Optional phenophase background overlay
```

Current month:

```text
April 2026
```

The latest/current point should use a calm pulsing marker:

```text
soft expanding halo
subtle ping animation
not alarm-like
```

Metric switching should animate smoothly:

```text
trend line transition
highlighted marker transition
annotation content change
Y-axis scale transition
```

The graph should feel like a live environmental monitoring terminal.

---

## Phenophase Overlay

The phenophase overlay is optional and should default to off or be lightly enabled depending on visual clarity.

When active, it should show soft background bands behind the trend chart.

For Michigan deciduous riparian profile:

```text
Dormancy
Greenup
Maturity
Senescence
Dormancy
```

The overlay should remain low-opacity and should not overpower the metric line.

Phenophase note:

```text
Phenophase context helps interpret seasonal timing but does not prove causation.
```

---

## Real April 2026 Data

### Rouge EIC / Lower Rouge Riparian

Full site name:

```text
UM-Dearborn EIC / Rouge River
```

Display name:

```text
Lower Rouge Riparian
```

Coordinates:

```text
42.315764, -83.239361
```

Month:

```text
Apr 2026
```

Phenophase:

```text
Expected
```

Fusion disposition:

```text
reportable_signal
```

Status:

```text
Review Required
```

Metrics:

```text
NDVI: 0.48 | Unusual | higher_than_expected
NDMI: -0.11 | Watch | higher_than_expected
Precipitation: 112.8mm | Above Normal
```

Review cue:

```text
Rainfall-related review cue
```

### TTI Mangrove

Full site name:

```text
Ten Thousand Islands Mangrove Test Site
```

Display name:

```text
TTI Mangrove
```

Month:

```text
Apr 2026
```

Phenophase:

```text
Early
```

Fusion disposition:

```text
routine_log
```

Status:

```text
Routine Log
```

Metrics:

```text
NDVI: 0.88 | Normal
NDMI: 0.49 | Normal
Precipitation: 62.5mm | Near Normal
```

---

## Scientific Boundary

Footer text:

```text
Detection does not equal causation. Sentry-V flags unusual patterns and suggests review cues; final interpretation requires human and field context.
```

Trend explorer note:

```text
Trend context supports review decisions but does not prove causation.
```

The dashboard should never imply that Sentry-V proves a cause.

---

## Future Engineering Needs

To build this for real, Sentry-V will likely need new BigQuery semantic views:

```text
v_client_site_review_cards
v_historical_context_monthly
v_client_reportable_signal_feed
```

Potential fields for `v_client_site_review_cards`:

```text
site_id
display_name
full_site_name
coordinates
month
status_label
main_takeaway
hypothesis
recommended_action
review_cue
phenophase_status
fusion_disposition
```

Potential fields for `v_historical_context_monthly`:

```text
site_id
display_name
month
metric
actual_value
historical_baseline
classification
trend_status
phenophase_stage
is_current_reporting_month
annotation_text
```

---

## Version Milestone

This prototype represents:

```text
Client Review Dashboard v1.1
```

Meaning:

```text
The client-facing product direction is now defined:
Alert → Takeaway → Hypothesis → Action → Historical Context.
```
