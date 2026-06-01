# Sentry-V Cloud Automation Blueprint

This document records the cloud automation setup for **Sentry-V v0.7**.

Sentry-V v0.7 runs as an automated monthly ecological monitoring job using **Google Cloud Run Jobs**, **Cloud Scheduler**, **Google Earth Engine**, **gridMET climate drivers**, and **BigQuery**.

---

## 1. Purpose

The purpose of the cloud automation layer is to make Sentry-V run without manual terminal execution.

Instead of manually running:

```bash
python run_sentry.py
python -m climate.run_gridmet_artifacts --year 2026 --month 4
python -m storage.load_artifacts
```

Sentry-V now runs through:

```text
Cloud Scheduler
→ Cloud Run Job
→ Sentry-V container
→ run_cloud.py
→ run_sentry.py
→ Sentinel-2 NDVI / NDMI artifacts
→ CHIRPS precipitation context
→ gridMET climate driver artifacts
→ BigQuery loader
→ BigQuery tables
→ Dashboard-ready views
```

This turns Sentry-V from a local vegetation analysis tool into an operational monthly environmental sentry.

---

## 2. Current Cloud Configuration

### Google Cloud Project

```text
Project ID: sentry-v
Project number: 1074222318910
```

### Region

```text
us-central1
```

### Artifact Registry Repository

```text
Repository: sentry-v-containers
Location: us-central1
Format: Docker
```

### Container Image

```text
us-central1-docker.pkg.dev/sentry-v/sentry-v-containers/sentry-v:latest
```

### Cloud Run Job

```text
Job name: sentry-v-monthly-run
Region: us-central1
Memory: 2Gi
CPU: 1
Task timeout: 3600 seconds
Max retries: 0
```

### Service Account

```text
sentry-v-runner@sentry-v.iam.gserviceaccount.com
```

### Cloud Scheduler Job

```text
Job name: sentry-v-monthly-schedule
Region: us-central1
Schedule: 0 9 5 * *
Timezone: America/Detroit
```

This means Sentry-V runs:

```text
On the 5th day of each month
At 9:00 AM Detroit time
```

---

## 3. Why the 5th of the Month?

The 5th of the month is used instead of the 1st to allow environmental datasets to settle.

Sentry-V summarizes the previous completed month. For example:

```text
June 5 run → summarizes May
July 5 run → summarizes June
```

This delay is intentional because:

- Sentinel-2 imagery may take time to process and appear in Earth Engine.
- End-of-month satellite scenes may not be available on the 1st.
- Michigan sites often need every usable cloud-free image for a reliable monthly composite.
- CHIRPS precipitation data may need time to populate for the final days of the previous month.
- gridMET updates quickly, but the full monthly context is most defensible after the month has closed.
- Waiting a few days improves confidence and reduces weak monthly composites.

The 5th is the official monthly production run date.

---

## 4. Required APIs

The following Google Cloud APIs must be enabled:

```bash
gcloud services enable artifactregistry.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable earthengine.googleapis.com
gcloud services enable serviceusage.googleapis.com
```

---

## 5. IAM Permissions

The Cloud Run service account is:

```text
sentry-v-runner@sentry-v.iam.gserviceaccount.com
```

It currently needs:

```text
roles/bigquery.dataEditor
roles/bigquery.jobUser
roles/run.invoker
roles/serviceusage.serviceUsageConsumer
roles/earthengine.viewer
```

### BigQuery roles

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### Cloud Run invoker role

Required so Cloud Scheduler can invoke the Cloud Run Job using the service account.

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### Service Usage Consumer role

Required because Earth Engine initialization uses the project:

```python
ee.Initialize(project="sentry-v")
```

The service account must be allowed to use enabled services in the project.

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

### Earth Engine Viewer role

Required because Cloud Run executes Earth Engine computations through the service account.

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/earthengine.viewer"
```

---

## 6. Earth Engine Access

Sentry-V uses Google Earth Engine through the Python Earth Engine API.

The Cloud Run Job uses the service account:

```text
sentry-v-runner@sentry-v.iam.gserviceaccount.com
```

Earth Engine must be initialized with the project ID inside cloud-executed code:

```python
ee.Initialize(project="sentry-v")
```

This avoids the Cloud Run error:

```text
ee.Initialize: no project found. Call with project=
```

The service account also needs Earth Engine computation permission. During v0.7 setup, this error occurred:

```text
Permission 'earthengine.computations.create' denied on resource 'projects/sentry-v'
```

It was fixed by granting:

```text
roles/earthengine.viewer
```

The successful Cloud Run execution confirmed that the deployed container can run Sentry-V end-to-end from the cloud.

---

## 7. Cloud Entry Point

The cloud entry point is:

```text
run_cloud.py
```

As of v0.7, it runs three steps:

```text
Step 1: run_sentry.py
Step 2: climate.run_gridmet_artifacts
Step 3: storage.load_artifacts
```

The pipeline sequence is:

```text
run_sentry.py
→ vegetation metric artifacts
→ fusion summary artifacts

climate.run_gridmet_artifacts
→ gridMET climate driver artifacts

storage.load_artifacts
→ BigQuery refresh
```

This keeps the cloud runtime simple while still separating science, climate context, and storage.

---

## 8. Cloud Runtime Pipeline

### Step 1 — Vegetation Monitoring Engine

```text
run_sentry.py
```

Produces:

```text
outputs/*_NDVI_status.json
outputs/*_NDMI_status.json
outputs/*_fusion_summary.json
outputs/run_logs/*.json
```

Core inputs:

```text
Sentinel-2 SR Harmonized
NDVI
NDMI
Phenophase context
CHIRPS precipitation context
```

### Step 2 — gridMET Climate Driver Artifacts

```text
climate/run_gridmet_artifacts.py
```

Produces:

```text
outputs/climate_drivers/*_gridmet_climate_drivers.json
```

Current gridMET drivers:

```text
temperature_mean_c
vpd_mean_kpa
eto_total_mm
precip_total_mm
```

Driver meanings:

```text
temperature_mean_c → thermal context
vpd_mean_kpa → atmospheric thirst / moisture demand context
eto_total_mm → total evaporative demand context
precip_total_mm → gridMET precipitation cross-check
```

### Step 3 — BigQuery Artifact Loader

```text
storage/load_artifacts.py
```

Refreshes:

```text
sentry-v.sentry_v.metric_records
sentry-v.sentry_v.fusion_summaries
sentry-v.sentry_v.run_logs
sentry-v.sentry_v.climate_driver_records
```

---

## 9. Climate Driver Architecture

Sentry-V v0.7 adds a dedicated climate module:

```text
climate/
├── __init__.py
├── gridmet.py
└── run_gridmet_artifacts.py
```

### Why gridMET?

gridMET is used as the operational climate-driver source because:

```text
It is daily.
It is near-current.
It covers the contiguous United States.
It supports monthly aggregation.
It includes temperature, VPD, ETo, and precipitation.
```

### Why not TerraClimate yet?

TerraClimate remains valuable for long-term global water-balance context, but it lags behind present-day operational monitoring. It is better suited for future historical/global observatory work.

Current architecture:

```text
gridMET → operational U.S. monthly monitoring
TerraClimate → future global / historical water-balance context
```

---

## 10. Climate Sampling Geometry

Sentinel-2 vegetation metrics and gridMET climate drivers use different sampling logic.

### Vegetation Geometry

For NDVI / NDMI:

```text
Use the precise site polygon.
```

Reason:

```text
Vegetation metrics should represent the exact monitored canopy/site footprint.
```

### Climate Geometry

For gridMET:

```text
Use site centroid → 5,000 meter buffer.
```

Reason:

```text
gridMET pixels are coarse, roughly 4 km.
Tiny site polygons may return null values if they do not intersect a gridMET pixel center.
Atmospheric context is regional, so a 5 km centroid buffer is more stable and scientifically appropriate.
```

This fixed the Rouge EIC null-value issue during Phase 11B.

Rule:

```text
Precise geometry for vegetation.
Regional centroid buffer for climate.
```

---

## 11. BigQuery Output Tables

The Cloud Run Job refreshes:

```text
sentry-v.sentry_v.metric_records
sentry-v.sentry_v.fusion_summaries
sentry-v.sentry_v.run_logs
sentry-v.sentry_v.climate_driver_records
```

### metric_records

One row per:

```text
site_id + month + metric
```

Used for NDVI / NDMI monitoring history.

### fusion_summaries

One row per:

```text
site_id + month
```

Used for site-level signal interpretation and dashboard triage.

### run_logs

One row per run-log artifact.

Used for operational observability.

### climate_driver_records

One row per:

```text
site_id + month + climate driver
```

Current drivers:

```text
temperature_mean_c
vpd_mean_kpa
eto_total_mm
precip_total_mm
```

Example row meaning:

```text
site_id: rouge_eic
month: 2026-04
driver: vpd_mean_kpa
classification: normal_demand
direction: near_expected
confidence: high
```

---

## 12. Dashboard-Ready Views

The dashboard-ready views are:

```text
sentry-v.sentry_v.v_site_monthly_summary
sentry-v.sentry_v.v_metric_history
sentry-v.sentry_v.v_reportable_signals
```

Future client dashboard semantic views may include:

```text
sentry-v.sentry_v.v_client_reportable_signal_feed
sentry-v.sentry_v.v_client_site_review_cards
sentry-v.sentry_v.v_historical_context_monthly
```

The client-facing dashboard should eventually combine:

```text
vegetation metrics
precipitation context
phenophase context
thermal context
atmospheric thirst context
evaporative demand context
```

---

## 13. Docker Files

Sentry-V includes:

```text
Dockerfile
.dockerignore
requirements.txt
run_cloud.py
```

### Dockerfile

The container uses:

```text
python:3.11-slim
```

The container command is:

```text
python run_cloud.py
```

### Important Platform Note

Because the development machine is Apple Silicon, the image must be built for:

```text
linux/amd64
```

This avoids Cloud Run startup failures caused by an ARM64 image.

---

## 14. Build and Push Container Image

From the Sentry-V project root:

```bash
docker buildx build \
  --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/sentry-v/sentry-v-containers/sentry-v:latest \
  --push .
```

This builds the correct image architecture and pushes it directly to Artifact Registry.

---

## 15. Update Cloud Run Job Image

After pushing a new image:

```bash
gcloud run jobs update sentry-v-monthly-run \
  --image=us-central1-docker.pkg.dev/sentry-v/sentry-v-containers/sentry-v:latest \
  --region=us-central1
```

---

## 16. Manually Execute the Cloud Run Job

To manually run Sentry-V in the cloud:

```bash
gcloud run jobs execute sentry-v-monthly-run \
  --region=us-central1
```

Then check execution status:

```bash
gcloud run jobs executions list \
  --job=sentry-v-monthly-run \
  --region=us-central1
```

Successful result should show:

```text
COMPLETE: 1 / 1
```

To describe a specific execution:

```bash
gcloud run jobs executions describe EXECUTION_NAME \
  --region=us-central1
```

---

## 17. Create the Cloud Scheduler Job

The monthly scheduler was created with:

```bash
gcloud scheduler jobs create http sentry-v-monthly-schedule \
  --location=us-central1 \
  --schedule="0 9 5 * *" \
  --time-zone="America/Detroit" \
  --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/sentry-v/jobs/sentry-v-monthly-run:run" \
  --http-method=POST \
  --oauth-service-account-email=sentry-v-runner@sentry-v.iam.gserviceaccount.com
```

---

## 18. Manually Trigger the Scheduler

To test the scheduler:

```bash
gcloud scheduler jobs run sentry-v-monthly-schedule \
  --location=us-central1
```

Then check Cloud Run executions:

```bash
gcloud run jobs executions list \
  --job=sentry-v-monthly-run \
  --region=us-central1
```

A successful scheduler-triggered execution should show:

```text
RUN BY: sentry-v-runner@sentry-v.iam.gserviceaccount.com
COMPLETE: 1 / 1
```

---

## 19. Cloud Run Logs

To read Cloud Run Job logs:

```bash
gcloud logging read \
'resource.type="cloud_run_job"
resource.labels.job_name="sentry-v-monthly-run"' \
--limit=100 \
--format="value(textPayload)"
```

For a specific execution:

```bash
gcloud logging read \
'resource.type="cloud_run_job"
resource.labels.job_name="sentry-v-monthly-run"
resource.labels.location="us-central1"
labels."run.googleapis.com/execution_name"="EXECUTION_NAME"' \
--limit=120 \
--format="value(textPayload)"
```

---

## 20. Verify BigQuery Tables

Metric records:

```bash
bq query --use_legacy_sql=false '
SELECT COUNT(*) AS metric_rows
FROM `sentry-v.sentry_v.metric_records`;
'
```

Fusion summaries:

```bash
bq query --use_legacy_sql=false '
SELECT COUNT(*) AS fusion_rows
FROM `sentry-v.sentry_v.fusion_summaries`;
'
```

Run logs:

```bash
bq query --use_legacy_sql=false '
SELECT COUNT(*) AS run_log_rows
FROM `sentry-v.sentry_v.run_logs`;
'
```

Climate driver records:

```bash
bq query --use_legacy_sql=false '
SELECT
  site_id,
  month,
  driver,
  current_value,
  baseline_median,
  robust_z_score,
  classification,
  direction,
  confidence
FROM `sentry-v.sentry_v.climate_driver_records`
ORDER BY site_id, driver;
'
```

Expected v0.7 test output:

```text
2 sites × 4 climate drivers = 8 rows
```

---

## 21. Known Troubleshooting Notes

### Docker daemon not running

Error:

```text
Cannot connect to the Docker daemon
```

Fix:

```text
Open Docker Desktop and wait until Docker is running.
```

### Dockerfile not found

Error:

```text
failed to read dockerfile: open Dockerfile: no such file or directory
```

Cause:

```text
The Docker build command was run outside the Sentry-V root folder.
```

Fix:

```bash
cd "/Volumes/ONE_PIECE/Ecological_Obsevatory/Sentry-V"
```

### Cloud Run application failed to start

Error:

```text
Application exec likely failed
```

Cause found during setup:

```text
Image was built on Apple Silicon as linux/arm64.
```

Fix:

```bash
docker buildx build \
  --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/sentry-v/sentry-v-containers/sentry-v:latest \
  --push .
```

### Scheduler trigger does not create execution

Fix:

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### Earth Engine no project found

Error:

```text
ee.Initialize: no project found. Call with project=
```

Fix:

```python
ee.Initialize(project="sentry-v")
```

### Service Usage permission denied

Error:

```text
Caller does not have required permission to use project sentry-v.
Grant the caller the roles/serviceusage.serviceUsageConsumer role.
```

Fix:

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

### Earth Engine computation permission denied

Error:

```text
Permission 'earthengine.computations.create' denied on resource 'projects/sentry-v'
```

Fix:

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/earthengine.viewer"
```

### gridMET returns null values for small polygons

Cause:

```text
gridMET is coarse compared to tiny site polygons.
```

Fix:

```text
Use centroid → 5 km buffer climate sampling geometry.
```

---

## 22. Confirmed Successful Cloud Executions

### v0.5 baseline automation

Confirmed successful manual Cloud Run execution:

```text
sentry-v-monthly-run-djn9t
```

Confirmed successful scheduler-triggered execution:

```text
sentry-v-monthly-run-hz6rr
```

### v0.7 climate driver automation

Confirmed successful Cloud Run execution:

```text
sentry-v-monthly-run-8mwpk
```

Execution details:

```text
1 task completed successfully
Elapsed time: 4m2.35s
Service account: sentry-v-runner@sentry-v.iam.gserviceaccount.com
```

The v0.7 execution confirmed:

```text
metric_records refreshed with 4 rows
fusion_summaries refreshed with 2 rows
run_logs refreshed with 4 rows
climate_driver_records refreshed with 8 rows
```

---

## 23. Current Automation Status

Sentry-V cloud automation is operational.

The scheduler is enabled and the next automatic production run is scheduled for:

```text
June 5, 2026 at 9:00 AM America/Detroit
```

The current cloud automation now includes:

```text
Sentinel-2 vegetation monitoring
NDVI
NDMI
Phenophase timing context
CHIRPS precipitation context
gridMET thermal context
gridMET atmospheric thirst / VPD context
gridMET reference evapotranspiration context
gridMET precipitation cross-check
BigQuery artifact loading
Dashboard-ready data tables
```

---

## 24. Version Milestone

This automation layer corresponds to:

```text
Sentry-V v0.7 — gridMET Climate Driver Automation
```

Version history:

```text
v0.1 → Vegetation Observatory Core
v0.2 → Vegetation Observatory + CHIRPS Precipitation Context
v0.3 → BigQuery Environmental Memory
v0.4 → BigQuery Dashboard Query Layer
v0.5 → Cloud Run Monthly Automation
v0.6 → Dashboard and Digital Observatory Blueprints
v0.7 → gridMET Climate Driver Automation
```

---

## 25. Operational Meaning

Sentry-V is now an automated cloud vegetation observatory with atmospheric demand context.

It can wake up monthly, process configured ecological sites, generate vegetation signals, add precipitation support, add phenophase timing context, add thermal and evaporative-demand context, refresh BigQuery, and support dashboard-ready monitoring outputs.

This is the first operational version of Sentry-V that can distinguish between:

```text
vegetation anomaly
rainfall-supported review cue
normal atmospheric moisture demand
elevated thermal context
routine seasonal condition
```

Sentry-V still preserves its core scientific boundary:

```text
Detection does not equal causation.
```

It detects unusual patterns, adds environmental driver context, suggests review cues, and leaves final interpretation to human review and field context.
