import sys

from run_sentry import main as run_sentry_main
from storage.load_artifacts import load_all_artifacts_to_bigquery


def main():
    print("\n========================================")
    print("   SENTRY-V CLOUD AUTOMATION RUN")
    print("========================================")

    try:
        print("\n[Step 1] Running Sentry-V monitoring engine...")
        run_sentry_main()

        print("\n[Step 2] Loading artifacts into BigQuery...")
        load_all_artifacts_to_bigquery()

        print("\n[SUCCESS] Sentry-V cloud automation run complete.")

    except Exception as error:
        print(f"\n[ERROR] Pipeline failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
