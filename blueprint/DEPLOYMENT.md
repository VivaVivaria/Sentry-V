# Sentry-V Deployment Blueprint

This document outlines the infrastructure and environment requirements needed to run **Sentry-V**, an automated ecological monitoring system.

Sentry-V is designed as a reusable monitoring blueprint. The prototype runs in the developer's environment, while future partner or client deployments should be recreated inside their own Google Cloud project.

---

## 1. System Purpose

Sentry-V monitors vegetation behavior over time and flags when the current monthly signal looks unusual compared to expected seasonal behavior.

The system currently uses:

- Sentinel-2 Surface Reflectance imagery
- NDVI as a vegetation activity proxy
- Monthly median compositing
- Same-month historical baseline comparison
- Z-score classification
- Validation guardrails
- JSON artifact export
- Run logging

Important rule:

> Detection does not equal causation.  
> Sentry-V detects unusual vegetation activity. Human interpretation is required.

---

## 2. Cloud Infrastructure Prerequisites

To run Sentry-V in a Google Cloud environment, the following must be configured:

### Required Google Cloud Resources

- A dedicated Google Cloud project
- Google Earth Engine access registered to that project

### Required APIs

- Google Earth Engine API  
  `earthengine.googleapis.com`

### Future cloud deployment APIs

These are not required for the current local prototype, but will likely be needed for a future Cloud Run deployment:

- Cloud Run Admin API
- Cloud Scheduler API
- Cloud Storage API
- Cloud Logging API
- Cloud Monitoring API
- Artifact Registry API
- Cloud Build API
- BigQuery API

---

## 3. Python Environment Setup

Sentry-V runs on Python.

### Recommended Python version

```bash
Python 3.9+
Required libraries
pip install earthengine-api pyyaml
4. Earth Engine Authentication

Before the first run, authenticate the environment with Google Earth Engine.

Authenticate Earth Engine
earthengine authenticate

Follow the browser prompt and log in with the Google account connected to Earth Engine.

Set the active Earth Engine project
earthengine set_project YOUR-GCP-PROJECT-ID

Example:

earthengine set_project sentry-v

The Google Cloud project must also be registered for Earth Engine access.

5. Required Directory Structure

The execution environment should contain the following structure:

sentry-v/
├── config/
│   └── sites.yaml
├── engine/
│   ├── collect_imagery.py
│   ├── calculate_indices.py
│   ├── build_monthly_composite.py
│   ├── create_monthly_record.py
│   ├── calculate_baseline.py
│   └── classify_status.py
├── validation/
│   └── quality_checks.py
├── operations/
│   ├── export_record.py
│   └── system_logger.py
├── outputs/
│   └── run_logs/
├── blueprint/
│   └── DEPLOYMENT.md
└── run_sentry.py
6. Configuration File

Sentry-V reads monitoring targets from:

config/sites.yaml

The first configured site is:

client:
  client_id: friends_of_the_rouge
  client_name: Friends of the Rouge
  region: Southeast Michigan

sites:
  - site_id: rouge_eic
    site_name: UM-Dearborn EIC / Rouge River
    region: Dearborn, Michigan
    ecosystem_type: urban riparian woodland
    data_source: COPERNICUS/S2_SR_HARMONIZED
    metrics:
      - NDVI
    time_step: monthly
    monitoring_season:
      start_month: 4
      end_month: 10
    geometry:
      type: Point
      coordinates: [-83.235, 42.316]
    purpose: Detect unusual vegetation activity in Rouge River urban riparian sites.
7. Execution Command

Run Sentry-V from the project root directory:

python run_sentry.py

This command runs the full monitoring sequence:

Configuration
→ imagery collection
→ NDVI calculation
→ monthly composite
→ historical baseline
→ status classification
→ validation confidence
→ monitoring artifact export
→ system run log export
8. Expected Outputs

A successful run generates two permanent artifacts.

Monitoring artifact

Saved to:

outputs/[site_id]_[YYYY-MM]_[metric]_status.json

Example:

outputs/rouge_eic_2026-04_NDVI_status.json

This file contains the validated ecological monitoring result.

System run log

Saved to:

outputs/run_logs/sentry_v_[site_id]_[YYYY-MM]_[timestamp]_run_log.json

Example:

outputs/run_logs/sentry_v_rouge_eic_2026-04_20260503T133022Z_run_log.json

This file records whether the sentry run succeeded or failed.

9. Current Production Schema

The current monitoring artifact uses this schema:

{
  "site_id": "rouge_eic",
  "site_name": "UM-Dearborn EIC / Rouge River",
  "month": "2026-04",
  "metric": "NDVI",
  "current_value": 0.4596,
  "baseline_mean": 0.3752,
  "baseline_stdev": 0.0323,
  "z_score": 2.61,
  "classification": "unusual",
  "direction": "higher_than_expected",
  "confidence": "high",
  "images_used": 6,
  "historical_values": [
    0.351,
    0.339,
    0.3797,
    0.3842,
    0.422
  ],
  "interpretation": "Unusual high vegetation activity detected.",
  "note": "Detection only. Human interpretation required."
}
10. Deployment Principle

The current sentry-v project is a prototype and reference implementation.

Future partner or client deployments should be recreated inside a separate Google Cloud project using this blueprint.

Recommended model:

Developer project
└── prototype, testing, reference implementation

Client project
└── production deployment, client-owned data, client-specific permissions

This keeps the system portable, reproducible, and easier to govern.

11. Future Cloud Deployment Path

The next deployment stage may include:

Docker container
Cloud Run job
Cloud Scheduler monthly trigger
Cloud Storage artifact bucket
BigQuery monitoring table
Cloud Logging integration
Cloud Monitoring alerts
Service account IAM setup

These are not part of the current local prototype, but this blueprint prepares the system for that path.


Save the file.

---

# Step 3 — Confirm it exists

Run:

```powershell
dir blueprint

You should see:

DEPLOYMENT.md