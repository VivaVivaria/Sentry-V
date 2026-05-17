from google.cloud import bigquery

from storage.schemas import (
    METRIC_RECORDS_SCHEMA,
    FUSION_SUMMARIES_SCHEMA,
    RUN_LOGS_SCHEMA,
)


PROJECT_ID = "sentry-v"
DATASET_ID = "sentry_v"
LOCATION = "US"


TABLES = {
    "metric_records": METRIC_RECORDS_SCHEMA,
    "fusion_summaries": FUSION_SUMMARIES_SCHEMA,
    "run_logs": RUN_LOGS_SCHEMA,
}


def get_bigquery_client():
    """
    Create and return an authenticated BigQuery client.
    """
    return bigquery.Client(project=PROJECT_ID)


def create_dataset_if_missing(client):
    """
    Create the sentry_v dataset if it does not already exist.
    """
    dataset_ref = bigquery.Dataset(f"{PROJECT_ID}.{DATASET_ID}")
    dataset_ref.location = LOCATION

    dataset = client.create_dataset(dataset_ref, exists_ok=True)

    print(f"[OK] Dataset ready: {dataset.full_dataset_id}")

    return dataset


def create_table_if_missing(client, table_name, schema):
    """
    Create a BigQuery table if it does not already exist.
    """
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    table = bigquery.Table(table_id, schema=schema)

    created_table = client.create_table(table, exists_ok=True)

    print(f"[OK] Table ready: {created_table.full_table_id}")

    return created_table


def initialize_bigquery_storage():
    """
    Initialize the BigQuery storage layer for Sentry-V.

    Creates:
    - sentry_v.metric_records
    - sentry_v.fusion_summaries
    - sentry_v.run_logs
    """
    print("\n========================================")
    print("   SENTRY-V BIGQUERY STORAGE SETUP")
    print("========================================\n")

    client = get_bigquery_client()

    create_dataset_if_missing(client)

    for table_name, schema in TABLES.items():
        create_table_if_missing(
            client=client,
            table_name=table_name,
            schema=schema,
        )

    print("\n[SUCCESS] BigQuery storage initialized.")
    print(f"Dataset: {PROJECT_ID}.{DATASET_ID}")
    print("Tables:")
    for table_name in TABLES:
        print(f"- {PROJECT_ID}.{DATASET_ID}.{table_name}")


if __name__ == "__main__":
    initialize_bigquery_storage()