# Sentry-V Data Studio Operator Dashboard Blueprint

This document records the first Sentry-V **Operator Dashboard** built in Google Data Studio.

The Operator Dashboard is not the final client-facing experience. Its purpose is to help the system operator verify that Sentry-V is running correctly, sending data to BigQuery, exposing query-ready views, and displaying monitoring outputs in a visual interface.

---

## Dashboard Name

```text
Sentry-V Environmental Dashboard
```

Dashboard type:

```text
Operator Dashboard
```

Phase:

```text
Phase 10B — Data Studio Operator Dashboard MVP
```

Version context:

```text
Sentry-V v0.5
```

---

## Purpose

The Operator Dashboard helps the builder/operator answer:

```text
Is the pipeline producing records?
Are the BigQuery views working?
Are reportable signals visible?
Are routine logs separated from review signals?
Are NDVI and NDMI values displayed correctly?
Are site and month filters working?
```

This dashboard is mainly for:

- Developer/operator review
- Data validation
- Pipeline debugging
- Monthly monitoring checks
- Demonstrating that BigQuery and Data Studio are connected

---

## Operator Dashboard vs Client Review Dashboard

| Dashboard | Audience | Purpose |
|---|---|---|
| **Operator Dashboard** | Developer / analyst / system operator | Verify system behavior, inspect data, validate outputs |
| **Client Review Dashboard** | Conservation teams / stakeholders | Explain what needs review, why, and what action is recommended |

The current Data Studio dashboard is the **Operator Dashboard**.

The Figma prototype is the direction for the **Client Review Dashboard**.

---

## Data Sources

Google Cloud Project:

```text
sentry-v
```

BigQuery dataset:

```text
sentry_v
```

Connected BigQuery views:

```text
sentry-v.sentry_v.v_site_monthly_summary
sentry-v.sentry_v.v_reportable_signals
sentry-v.sentry_v.v_metric_history
```

---

## BigQuery Views Used

### v_site_monthly_summary

Purpose:

```text
Main site/month monitoring summary.
```

Used for:

- Site Monthly Summary table
- Site filter control
- Month filter control

Key fields:

```text
site_id
site_name
profile
month
ndvi_classification
ndmi_classification
phenophase_status
precipitation_classification
fusion_disposition
hypothesis
run_timestamp
```

### v_reportable_signals

Purpose:

```text
Triage view that only shows non-routine signals.
```

Used for:

- Reportable Signals Feed table

Expected April 2026 behavior:

```text
Rouge EIC appears.
TTI Mangrove does not appear because it is routine_log.
```

### v_metric_history

Purpose:

```text
Metric-level history for trend visualization.
```

Used for:

- NDVI / NDMI Metric History chart

Configuration:

```text
Dimension / X-axis: month
Breakdown dimension: metric
Metric / Y-axis: current_value
Aggregation: Average
```

Important note:

```text
current_value must use Average aggregation, not Sum.
```

NDVI and NDMI are vegetation indices. They should not be summed across sites.

---

## Current Dashboard Sections

### Site Monthly Summary

Data source:

```text
v_site_monthly_summary
```

Chart type:

```text
Table
```

Fields:

```text
site_name
month
ndvi_classification
ndmi_classification
phenophase_status
precipitation_classification
fusion_disposition
```

### Reportable Signals Feed

Data source:

```text
v_reportable_signals
```

Chart type:

```text
Table
```

Purpose:

```text
Show only sites that need review.
```

### NDVI / NDMI Metric History

Data source:

```text
v_metric_history
```

Chart type:

```text
Line chart
```

Expected all-site April 2026 values:

```text
NDVI average ≈ 0.68
NDMI average ≈ 0.19
```

Expected Rouge EIC April 2026 values:

```text
NDVI ≈ 0.48
NDMI ≈ -0.11
```

Expected TTI Mangrove April 2026 values:

```text
NDVI ≈ 0.88
NDMI ≈ 0.49
```

---

## Controls

### Site Filter

Control type:

```text
Drop-down list
```

Control field:

```text
site_name
```

Expected behavior:

- Selecting Rouge EIC shows the reportable signal.
- Selecting TTI Mangrove shows no active reportable signal.
- The NDVI / NDMI chart updates to the selected site's values.

### Month Filter

Control type:

```text
Drop-down list
```

Control field:

```text
month
```

Current expected option:

```text
2026-04
```

---

## MVP Validation

The Operator Dashboard demonstrated:

```text
BigQuery views connect to Data Studio.
The monthly summary view displays both monitored sites.
The reportable signal view displays Rouge EIC only.
Routine logs are excluded from the reportable signal feed.
The NDVI / NDMI chart reads metric history correctly.
The chart uses Average aggregation to avoid invalid summed indices.
Site filter works.
Month filter works.
Rouge EIC displays the expected reportable behavior.
TTI Mangrove displays the expected routine behavior.
```

Status:

```text
Phase 10B Operator Dashboard MVP: Complete
```

---

## Interpretation Notes

The Operator Dashboard can expose technical fields directly:

```text
ndvi_classification
ndmi_classification
phenophase_status
precipitation_classification
fusion_disposition
```

These are useful for system validation, but they are not ideal as the primary client-facing experience.

For client-facing use, Sentry-V should translate these into:

```text
Signal level
Review cue
Main takeaway
Hypothesis
Recommended action
Historical context
```

---

## Design Principle

The Operator Dashboard can show data.

The Client Review Dashboard must explain meaning.

Sentry-V should preserve the scientific boundary:

```text
Detection does not equal causation.
```

The dashboard should never claim that Sentry-V proves the cause of ecological change.
