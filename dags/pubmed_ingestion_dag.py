"""Airflow DAG: Fetch PubMed abstracts for Type 2 Diabetes and stage to JSONL."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

SEARCH_TERM = "Type 2 Diabetes"
OUTPUT_PATH = "/opt/airflow/data/pubmed_t2d_abstracts.jsonl"
MAX_RESULTS = 500

default_args = {
    "owner": "airflow",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}


def _fetch(**context) -> None:
    import sys

    sys.path.insert(0, "/opt/airflow/dags")
    from extraction.pubmed_fetcher import fetch_and_save

    count = fetch_and_save(SEARCH_TERM, OUTPUT_PATH, MAX_RESULTS)
    print(f"Saved {count} abstracts to {OUTPUT_PATH}")
    context["ti"].xcom_push(key="record_count", value=count)


with DAG(
    dag_id="pubmed_ingestion",
    description="Fetch PubMed abstracts for Type 2 Diabetes to JSONL staging file",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["ingestion", "pubmed"],
) as dag:
    fetch_task = PythonOperator(
        task_id="fetch_pubmed_abstracts",
        python_callable=_fetch,
    )
