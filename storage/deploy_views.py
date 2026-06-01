from pathlib import Path

from google.cloud import bigquery

from storage.bigquery_client import PROJECT_ID


VIEW_FILES = [
    # Existing operator/dashboard query layer
    Path("sql/views/v_site_monthly_summary.sql"),
    Path("sql/views/v_metric_history.sql"),
    Path("sql/views/v_reportable_signals.sql"),

    # Phase 11D client dashboard semantic views
    Path("sql/views/v_client_signal_feed.sql"),
    Path("sql/views/v_client_site_review_cards.sql"),
    Path("sql/views/v_historical_context_explorer.sql"),
    Path("sql/views/v_driver_evidence_matrix.sql"),
]


def deploy_view(client, sql_path):
    """
    Deploy a single BigQuery view from a SQL file.
    """
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL view file not found: {sql_path}")

    query = sql_path.read_text(encoding="utf-8")

    print(f"\n[Deploying] {sql_path}")

    job = client.query(query)
    job.result()

    print(f"[SUCCESS] Deployed view from {sql_path}")


def deploy_all_views():
    """
    Deploy all Sentry-V dashboard/query views to BigQuery.
    """
    print("\n========================================")
    print("   SENTRY-V BIGQUERY VIEW DEPLOYMENT")
    print("========================================")

    client = bigquery.Client(project=PROJECT_ID)

    for sql_path in VIEW_FILES:
        deploy_view(client, sql_path)

    print("\n[SUCCESS] All BigQuery views deployed.")


if __name__ == "__main__":
    deploy_all_views()
