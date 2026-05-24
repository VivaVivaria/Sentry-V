# Sentry-V Cloud Automation Blueprint

This document records the cloud automation setup for **Sentry-V v0.5**.

Sentry-V v0.5 runs as an automated monthly ecological monitoring job using **Google Cloud Run Jobs** and **Cloud Scheduler**.

---

## 1. Purpose

The purpose of the cloud automation layer is to make Sentry-V run without manual terminal execution.

Instead of manually running:

```bash
python run_sentry.py
python -m storage.load_artifacts
```

Sentry-V now runs through:

```text
Cloud Scheduler
→ Cloud Run Job
→ Sentry-V container
→ run_cloud.py
→ run_sentry.py
→ JSON artifacts
→ BigQuery loader
→ BigQuery tables
→ Dashboard-ready views
```

This turns Sentry-V from a local tool into an operational monthly environmental sentry.

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

Sentry-V summarizes the previous month. For example:

```text
June 5 run → summarizes May
July 5 run → summarizes June
```

This delay is intentional because:

- Sentinel-2 imagery may take time to process and appear in Earth Engine.
- End-of-month satellite scenes may not be available on the 1st.
- Michigan sites often need every usable cloud-free image for a reliable monthly composite.
- CHIRPS precipitation data may need time to populate for the final days of the previous month.
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
```

Commands used:

```bash
gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

gcloud projects add-iam-policy-binding sentry-v \
  --member="serviceAccount:sentry-v-runner@sentry-v.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## 6. Earth Engine Access

Sentry-V uses Google Earth Engine through the Python Earth Engine API.

The Cloud Run Job uses the service account:

```text
sentry-v-runner@sentry-v.iam.gserviceaccount.com
```

This service account must have access to Earth Engine.

The successful Cloud Run execution confirmed that the deployed container can run Sentry-V end-to-end from the cloud.

---

## 7. Cloud Entry Point

The cloud entry point is:

```text
run_cloud.py
```

It runs two steps:

```text
Step 1: run_sentry.py
Step 2: storage.load_artifacts
```

This keeps the cloud runtime simple:

```python
from run_sentry import main as run_sentry_main
from storage.load_artifacts import load_all_artifacts_to_bigquery
```

Sentry-V first generates local JSON artifacts inside the container, then refreshes BigQuery using the generated artifacts.

---

## 8. Docker Files

Sentry-V v0.5 includes:

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

## 9. Build and Push Container Image

From the Sentry-V project root:

```bash
docker buildx build \
  --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/sentry-v/sentry-v-containers/sentry-v:latest \
  --push .
```

This builds the correct image architecture and pushes it directly to Artifact Registry.

---

## 10. Update Cloud Run Job Image

After pushing a new image:

```bash
gcloud run jobs update sentry-v-monthly-run \
  --image=us-central1-docker.pkg.dev/sentry-v/sentry-v-containers/sentry-v:latest \
  --region=us-central1
```

---

## 11. Manually Execute the Cloud Run Job

To manually run Sentry-V in the cloud:

```bash
gcloud run jobs execute sentry-v-monthly-run \
  --region=us-central1 \
  --wait
```

Successful result should show:

```text
Execution completed successfully
1 task completed successfully
```

---

## 12. Create the Cloud Scheduler Job

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

## 13. Manually Trigger the Scheduler

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

## 14. Inspect Cloud Run Execution

To describe a specific execution:

```bash
gcloud run jobs executions describe EXECUTION_NAME \
  --region=us-central1
```

Example:

```bash
gcloud run jobs executions describe sentry-v-monthly-run-hz6rr \
  --region=us-central1
```

---

## 15. Cloud Run Logs

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
labels."run.googleapis.com/execution_name"="EXECUTION_NAME"' \
--limit=100 \
--format="value(textPayload)"
```

---

## 16. BigQuery Output

The Cloud Run Job refreshes:

```text
sentry-v.sentry_v.metric_records
sentry-v.sentry_v.fusion_summaries
sentry-v.sentry_v.run_logs
```

The dashboard-ready views are:

```text
sentry-v.sentry_v.v_site_monthly_summary
sentry-v.sentry_v.v_metric_history
sentry-v.sentry_v.v_reportable_signals
```

---

## 17. Verify BigQuery Tables

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

---

## 18. Known Troubleshooting Notes

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

---

## 19. Current Automation Status

Sentry-V cloud automation is operational.

Confirmed successful manual Cloud Run execution:

```text
sentry-v-monthly-run-djn9t
```

Confirmed successful scheduler-triggered execution:

```text
sentry-v-monthly-run-hz6rr
```

The scheduler is enabled and the next automatic production run is scheduled for:

```text
June 5, 2026 at 9:00 AM America/Detroit
```

---

## 20. Version Milestone

This automation layer corresponds to:

```text
Sentry-V v0.5 — Cloud Run Monthly Automation
```

Version history:

```text
v0.1 → Vegetation Observatory Core
v0.2 → Vegetation Observatory + CHIRPS Precipitation Context
v0.3 → BigQuery Environmental Memory
v0.4 → BigQuery Dashboard Query Layer
v0.5 → Cloud Run Monthly Automation
```

---

## 21. Operational Meaning

Sentry-V is now an automated cloud vegetation observatory.

It can wake up monthly, process configured ecological sites, generate vegetation and precipitation context, refresh BigQuery, and support dashboard-ready monitoring outputs.

This is the first operational form of the Sentry-V Digital Sentry.
