# Sentry-V Deployment Blueprint

Sentry-V is a reusable ecological vegetation monitoring system designed to observe vegetation behavior over time, compare current signals against historical seasonal baselines, validate confidence, and produce human-readable monitoring artifacts.

This document outlines the environment, structure, and operational requirements needed to run Sentry-V in a new local or cloud environment.

---

## 1. System Purpose

Sentry-V is designed to function as a vegetation observatory for ecosystems.

It monitors:

- Vegetation greenness/activity through NDVI
- Canopy moisture through NDMI
- Seasonal timing through phenophase context
- Data reliability through validation guardrails
- Site-level ecological behavior through signal fusion summaries

Sentry-V does **not** diagnose causation.

It detects unusual vegetation behavior, evaluates confidence, and generates review cues for human interpretation.

---

## 2. System Pattern

Sentry-V follows a reusable digital sentry pattern:

1. Load target sites from `config/sites.yaml`
2. Load ecosystem rulebooks from `config/profiles.yaml`
3. Pull Sentinel-2 Surface Reflectance imagery once per site
4. Add NDVI and NDMI bands
5. Run each configured metric through robust baseline comparison
6. Validate data quality and seasonal context
7. Generate metric-level JSON artifacts
8. Compare NDVI against nearby monthly baselines for phenophase timing
9. Fuse NDVI, NDMI, and phenophase timing into a site-level summary
10. Write run logs for observability

---

## 3. Cloud Infrastructure Prerequisites

To run Sentry-V within a Google Cloud Platform environment, the following must be configured:

### Required

- A dedicated Google Cloud Project
- Earth Engine API enabled
- Earth Engine registered to the project
- Python runtime environment
- Access to Sentinel-2 Surface Reflectance data through Google Earth Engine

### Required Google Cloud API

```text
earthengine.googleapis.com
Future Cloud Deployment Components

For a future Cloud Run deployment, Sentry-V may also use:

Cloud Run
Cloud Scheduler
Cloud Storage
BigQuery
Cloud Logging
Cloud Monitoring
Service Accounts
Secret Manager

These are not required for the current local prototype, but they are part of the future serverless deployment blueprint.

4. Earth Engine Registration

Before running Sentry-V, the Google account or service account must be registered for Earth Engine access.

Sentry-V currently uses:

COPERNICUS/S2_SR_HARMONIZED

This is the Sentinel-2 Harmonized Surface Reflectance dataset.

The system intentionally uses Surface Reflectance instead of mixing Surface Reflectance with Top-of-Atmosphere imagery. This keeps the historical baseline scientifically consistent.

5. Python Environment Setup

Sentry-V runs on Python.

Recommended Python version:

Python 3.9+

Current local testing has been performed with a modern Python environment.

Install dependencies:

pip install earthengine-api pyyaml

If future modules require additional packages, document them in requirements.txt.

Recommended future file:

requirements.txt

Example:

earthengine-api
pyyaml
6. Earth Engine Authentication

Before the first run, authenticate Earth Engine:

earthengine authenticate

Follow the browser login prompt.

Then set the active Earth Engine project:

earthengine set_project YOUR-GCP-PROJECT-ID

Example:

earthengine set_project sentry-v
7. Required Directory Structure

The execution environment should follow this structure:

Sentry-V/
├── blueprint/
│   └── DEPLOYMENT.md
│
├── config/
│   ├── sites.yaml
│   └── profiles.yaml
│
├── engine/
│   ├── action_logic.py
│   ├── build_monthly_composite.py
│   ├── calculate_baseline.py
│   ├── calculate_indices.py
│   ├── calculate_phenophase.py
│   ├── classify_status.py
│   ├── collect_imagery.py
│   ├── create_monthly_record.py
│   └── signal_fusion.py
│
├── operations/
│   ├── export_record.py
│   └── system_logger.py
│
├── outputs/
│   ├── [site_id]_[YYYY-MM]_NDVI_status.json
│   ├── [site_id]_[YYYY-MM]_NDMI_status.json
│   ├── [site_id]_[YYYY-MM]_fusion_summary.json
│   └── run_logs/
│       └── sentry_v_[site_id]_[YYYY-MM]_[timestamp]_run_log.json
│
├── validation/
│   └── quality_checks.py
│
└── run_sentry.py

The outputs/ and outputs/run_logs/ folders may be created automatically during execution.

8. Configuration Files

Sentry-V is controlled by configuration files.

The core engine should not need to be rewritten for each new site.

Instead:

sites.yaml = what to monitor
profiles.yaml = how to interpret it
9. config/sites.yaml

This file defines the monitoring targets.

Each site includes:

Site ID
Site name
Ecosystem profile
Region
Ecosystem type
Data source
Metrics
Monitoring season
Geometry
Purpose

Example:

client:
  client_id: sentry_v_demo
  client_name: Sentry-V Demo Sites
  region: United States

sites:
  - site_id: rouge_eic
    site_name: UM-Dearborn EIC / Rouge River
    profile: michigan_deciduous_riparian
    region: Dearborn, Michigan
    ecosystem_type: urban riparian woodland

    data_source: COPERNICUS/S2_SR_HARMONIZED

    metrics:
      - NDVI
      - NDMI

    time_step: monthly

    monitoring_season:
      start_month: 4
      end_month: 10

    geometry:
      type: Point
      coordinates: [-83.235, 42.316]

    purpose: Detect unusual vegetation activity in Rouge River urban riparian sites.

A second site can use a different profile:

  - site_id: tti_mangrove
    site_name: Ten Thousand Islands Mangrove Test Site
    profile: florida_mangrove
    region: Southwest Florida
    ecosystem_type: tropical mangrove

    data_source: COPERNICUS/S2_SR_HARMONIZED

    metrics:
      - NDVI
      - NDMI

    time_step: monthly

    monitoring_season:
      start_month: 1
      end_month: 12

    geometry:
      type: Point
      coordinates: [-81.36, 25.85]

    purpose: Detect unusual vegetation activity in stable tropical mangrove canopy.
10. config/profiles.yaml

This file defines ecosystem-specific interpretation rules.

Profiles control:

Active months
Shoulder months
Dormant months
NDVI/NDMI spread threshold
Minimum pixel count
Minimum baseline years
Minimum composite days
Baseline start year
Seasonal notes

Example:

profiles:
  michigan_deciduous_riparian:
    active_months: [4, 5, 6, 7, 8, 9, 10]
    shoulder_months: [3, 11]
    dormant_months: [12, 1, 2]

    ndvi_spread_high: 0.30
    min_pixel_count: 50
    min_baseline_years: 5
    min_composite_days: 6
    baseline_start_year: 2018

    seasonal_notes:
      active: Vegetation interpretation is most reliable during the active growing season.
      shoulder: Interpretation should be treated as provisional because green-up or senescence may be underway.
      dormant: Vegetation anomaly interpretation is weak during dormant season.

  florida_mangrove:
    active_months: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    shoulder_months: []
    dormant_months: []

    ndvi_spread_high: 0.25
    min_pixel_count: 100
    min_baseline_years: 3
    min_composite_days: 4
    baseline_start_year: 2018

    seasonal_notes:
      active: Mangrove vegetation can be interpreted year-round, but rainfall, salinity, storm surge, and drought context may be needed.
      shoulder: No shoulder season defined for this profile.
      dormant: No dormant season defined for this profile.
11. Execution Command

Run Sentry-V from the root directory:

python run_sentry.py

On Windows PowerShell, first move into the project root:

cd "\\100.81.159.73\one_piece\Ecological_Obsevatory\Sentry-V"
python run_sentry.py

The command must be run from the project root so relative paths like config/sites.yaml resolve correctly.

12. Expected Runtime Behavior

When executed, Sentry-V will:

Load all configured sites
Load each site’s ecosystem profile
Pull Sentinel-2 Surface Reflectance imagery once per site
Add NDVI and NDMI bands
Loop through each configured metric
Build monthly composites
Calculate site-level mean values
Calculate site metric spread
Count valid pixels
Build robust historical baselines using median and MAD
Calculate robust z-scores
Classify metric status
Apply validation guardrails
Assign confidence
Assign disposition and recommended action
Export metric-level artifacts
Calculate phenophase context from NDVI
Fuse NDVI, NDMI, and phenophase into a site-level summary
Export fusion summary artifacts
Export run logs
13. Metric Artifacts

Sentry-V produces one metric artifact per site per metric.

Example outputs:

outputs/rouge_eic_2026-04_NDVI_status.json
outputs/rouge_eic_2026-04_NDMI_status.json
outputs/tti_mangrove_2026-04_NDVI_status.json
outputs/tti_mangrove_2026-04_NDMI_status.json

Each metric artifact includes:

Site ID
Site name
Ecosystem profile
Month
Metric
Current value
Site metric standard deviation
Pixel count
Baseline median
Baseline MAD
Baseline years used
Robust z-score
Classification
Direction
Confidence
Historical values
Composite days
Composite support
Spatial variability status
Season status
Season note
Disposition
Recommended action
Scientific note

Example metric schema:

{
  "site_id": "rouge_eic",
  "site_name": "UM-Dearborn EIC / Rouge River",
  "profile": "michigan_deciduous_riparian",
  "month": "2026-04",
  "metric": "NDVI",
  "current_value": 0.4596,
  "site_metric_stdev": 0.1994,
  "pixel_count": 10729,
  "baseline_median": 0.381,
  "baseline_mad": 0.0149,
  "baseline_years_used": 8,
  "robust_z_score": 3.57,
  "classification": "unusual",
  "direction": "higher_than_expected",
  "confidence": "high",
  "images_used": 6,
  "historical_values": [0.356, 0.3823, 0.3857, 0.351, 0.339, 0.3797, 0.3842, 0.422],
  "interpretation": "Unusual high vegetation activity detected.",
  "note": "Detection only. Human interpretation required.",
  "season_status": "active",
  "season_note": "Vegetation interpretation is most reliable during the active growing season.",
  "composite_days": 6,
  "composite_support": "sufficient",
  "spatial_variability_status": "acceptable",
  "disposition": "reportable_signal",
  "recommended_action": "Review imagery and compare with weather/site context. Escalate only if the deviation persists across adjacent months or aligns with field concerns."
}
14. Fusion Summary Artifacts

Sentry-V also produces one fusion summary per site.

Example outputs:

outputs/rouge_eic_2026-04_fusion_summary.json
outputs/tti_mangrove_2026-04_fusion_summary.json

Fusion summaries combine:

NDVI greenness/activity
NDMI canopy moisture
Phenophase timing context
Site-level hypothesis
Fusion disposition

Example fusion schema:

{
  "site_id": "tti_mangrove",
  "site_name": "Ten Thousand Islands Mangrove Test Site",
  "profile": "florida_mangrove",
  "month": "2026-04",
  "phenophase_context": {
    "status": "delayed",
    "target_month": 4,
    "closest_month": 3,
    "closest_baseline_median": 0.7079,
    "distance_from_closest_baseline": 0.006,
    "comparison_months": {
      "delayed_reference_month": 3,
      "expected_reference_month": 4,
      "early_reference_month": 5
    },
    "note": "Current vegetation greenness most closely resembles the historical NDVI baseline for month 03."
  },
  "signal_summary": {
    "NDVI": {
      "classification": "normal",
      "direction": "lower_than_expected",
      "confidence": "high",
      "current_value": 0.7139,
      "robust_z_score": -0.88,
      "disposition": "routine_log"
    },
    "NDMI": {
      "classification": "watch",
      "direction": "lower_than_expected",
      "confidence": "high",
      "current_value": 0.3325,
      "robust_z_score": -1.17,
      "disposition": "watch_signal"
    }
  },
  "hypothesis": "Canopy greenness remains within expected range, but canopy moisture signal is lower than expected for this month. The site appears to be showing delayed seasonal development. Review next month for persistence and compare with precipitation context.",
  "fusion_disposition": "watch_signal",
  "note": "Fusion summary is detection support only. Human interpretation required."
}
15. Run Logs

Sentry-V writes run logs for observability.

Example:

outputs/run_logs/sentry_v_rouge_eic_2026-04_20260504T013034Z_run_log.json

Run logs track:

Site ID
Target month
Metric
Run status
Start time
Finish time
Artifact path
Error message, if any

Run logs are important for future Cloud Scheduler and Cloud Run deployments because automated cloud jobs need an audit trail.

16. Data Quality Guardrails

Sentry-V validates each metric result before assigning confidence.

Current guardrails include:

NDVI/NDMI Physical Bounds

Checks whether the metric value is within the expected index range:

-1 to 1
Composite Support

Checks whether enough image observations were available to summarize the month.

Example:

"composite_days": 6,
"composite_support": "sufficient"
Pixel Support

Checks whether enough valid pixels are available inside the site geometry.

Example:

"pixel_count": 10729
Spatial Variability

Checks whether the site-level metric spread is unusually high.

Example:

"site_metric_stdev": 0.1994,
"spatial_variability_status": "acceptable"
Historical Baseline Support

Checks whether enough historical years were available.

Example:

"baseline_years_used": 8
Seasonal Context

Uses the ecosystem profile to determine whether the target month is:

active
shoulder
dormant
unknown
17. Robust Baseline Logic

Sentry-V uses robust statistics instead of fragile mean-only logic.

For each metric and month, it calculates:

historical same-month median
historical same-month MAD
robust z-score

The robust z-score is used to classify whether the current value is:

normal
watch
unusual
insufficient_data

This is more resistant to noisy outlier years.

18. Phenophase Timing Logic

Sentry-V uses NDVI as the phenophase timing signal.

For the target month, Sentry-V compares the current NDVI against:

previous month historical NDVI median
current month historical NDVI median
next month historical NDVI median

Example for April:

March baseline  → delayed reference
April baseline  → expected reference
May baseline    → early reference

The closest baseline month determines phenophase status:

delayed
expected
early
uncertain

This helps distinguish:

unusually strong April signal

from:

early green-up signal
19. Signal Fusion Logic

Sentry-V fuses NDVI, NDMI, and phenophase context into a site-level hypothesis.

Examples:

NDVI normal + NDMI normal
Stable baseline conditions.
NDVI normal + NDMI lower than expected
Canopy greenness remains within expected range, but canopy moisture signal is lower than expected for this month.
NDVI higher than expected + NDMI higher than expected
Vegetation activity is higher than expected and supported by higher-than-expected canopy moisture.
NDVI lower than expected + NDMI lower than expected
Both vegetation activity and canopy moisture signals are lower than expected.
Phenophase delayed

Adds context such as:

The site appears to be showing delayed seasonal development.
Phenophase early

Adds context such as:

The site appears to be undergoing early seasonal development.
20. Scientific Boundary

Sentry-V does not diagnose causation.

It separates:

Detection: what changed
Context: moisture and seasonal timing
Confidence: how reliable the signal is
Disposition: what should be reviewed
Interpretation: left to human experts and field context

Sentry-V should not say:

The vegetation is dying.

Sentry-V should say:

Vegetation activity and canopy moisture are lower than expected. Review imagery, weather context, and field observations before interpretation.
21. Developer Project vs Client Project

Sentry-V can be used as a developer prototype or replicated into a client environment.

Developer Project

The developer project is used for:

Prototyping
Testing
Demonstration
Portfolio evidence
Internal development
Client Project

A client project should contain:

Client-specific Google Cloud project
Client-specific Earth Engine registration
Client-specific service account
Client-specific site configuration
Client-specific outputs and logs
Client-specific storage and BigQuery tables

This separation keeps deployments secure and reproducible.

22. Current Prototype Status

The current local prototype supports:

Multi-site monitoring
Ecosystem profiles
Sentinel-2 Surface Reflectance
NDVI greenness/activity monitoring
NDMI canopy moisture monitoring
Robust baseline comparison using median and MAD
Robust z-score classification
Composite support validation
Spatial variability validation
Pixel support validation
Seasonal context logic
Phenophase timing context
Signal fusion summaries
JSON artifact export
Run log export
23. Current Limitations

The current prototype does not yet include:

Precipitation context
Soil moisture context
BigQuery ingestion
Dashboard visualization
Cloud Run deployment
Cloud Scheduler automation
Email or notification alerts
Raster export for anomaly review
Field observation integration

These can be added in future phases.

24. Future Deployment Path

The future cloud-native deployment path is:

Local Python prototype
→ Docker container
→ Cloud Run job
→ Cloud Scheduler trigger
→ Cloud Storage artifact bucket
→ BigQuery environmental memory table
→ Dashboard / alerting layer

Future cloud outputs may include:

JSON artifacts in Cloud Storage
Metric rows in BigQuery
Fusion summaries in BigQuery
Cloud Logging records
Cloud Monitoring alerts
Looker Studio dashboard views
25. Future BigQuery Schema Direction

Metric-level records may map into a table like:

site_id
site_name
profile
month
metric
current_value
site_metric_stdev
pixel_count
baseline_median
baseline_mad
baseline_years_used
robust_z_score
classification
direction
confidence
images_used
composite_days
composite_support
spatial_variability_status
season_status
disposition
recommended_action
artifact_path
run_timestamp

Fusion-level records may map into a table like:

site_id
site_name
profile
month
ndvi_classification
ndvi_direction
ndvi_value
ndmi_classification
ndmi_direction
ndmi_value
phenophase_status
phenophase_closest_month
hypothesis
fusion_disposition
artifact_path
run_timestamp
26. Future Precipitation Context

The next major context layer is precipitation.

Precipitation can help frame NDMI and phenophase signals.

Examples:

Low NDMI + low precipitation
→ possible moisture limitation context

Low NDMI + high precipitation
→ review flooding, storm disturbance, salinity, drainage, or site-specific effects

High NDVI + high NDMI + high precipitation
→ possible favorable growth context

Delayed phenophase + low precipitation
→ possible drought-related development lag

Precipitation should be added as context, not causation.

27. Operational Command Summary

From the project root:

python run_sentry.py

Expected successful output:

SENTRY-V MULTI-SITE MULTI-METRIC RUN COMPLETE

Expected output artifacts:

outputs/[site_id]_[YYYY-MM]_NDVI_status.json
outputs/[site_id]_[YYYY-MM]_NDMI_status.json
outputs/[site_id]_[YYYY-MM]_fusion_summary.json
outputs/run_logs/sentry_v_[site_id]_[YYYY-MM]_[timestamp]_run_log.json
28. Deployment Principle

Sentry-V is designed with foreknowledge that it may be replicated into other accounts.

The core idea is:

One reusable engine.
Many configured sites.
Many ecosystem profiles.
Client-specific deployment.
Human interpretation required.

The system is not just a script.

It is a reproducible monitoring unit for ecological observation.