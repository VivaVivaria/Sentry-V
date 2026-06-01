import sys

from run_sentry import main as run_sentry_main
from climate.run_gridmet_artifacts import generate_gridmet_artifacts
from storage.load_artifacts import load_all_artifacts_to_bigquery


# IMPORTANT:
# These must match the current hardcoded target_year / target_month in run_sentry.py.
# Later, move this into a shared reporting-month utility.
TARGET_YEAR = 2026
TARGET_MONTH = 4


def main():
    print("\n========================================")
    print("   SENTRY-V CLOUD AUTOMATION RUN")
    print("========================================")

    try:
        print("\n[Step 1] Running Sentry-V vegetation monitoring engine...")
        run_sentry_main()

        print("\n[Step 2] Generating gridMET climate driver artifacts...")
        generate_gridmet_artifacts(
            target_year=TARGET_YEAR,
            target_month=TARGET_MONTH,
            ee_project="sentry-v",
        )

        print("\n[Step 3] Loading all artifacts into BigQuery...")
        load_all_artifacts_to_bigquery()

        print("\n[SUCCESS] Sentry-V cloud automation run complete.")

    except Exception as error:
        print(f"\n[ERROR] Pipeline failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()