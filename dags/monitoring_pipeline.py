"""
DAG Airflow: Monitoring et observabilite DocuFlow.
Frequence: toutes les 15 minutes.
"""
import json
import logging
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger("airflow.monitoring")

SERVICES = {
    "ocr-service": "http://ocr-service:5001/api/health",
    "validation-service": "http://validation-service:5002/api/health",
    "backend": "http://backend:4000/api/health",
    "storage-api-proxy": "http://backend:4000/api/storage/health",
}

BACKEND_URL = "http://backend:4000"

DEFAULT_ARGS = {
    "owner": "docuflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def check_services_health(**context):
    results = {}
    all_healthy = True

    for name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=10)
            healthy = resp.status_code == 200
            results[name] = {
                "status": "healthy" if healthy else "degraded",
                "status_code": resp.status_code,
            }
            if not healthy:
                all_healthy = False
        except requests.RequestException as exc:
            results[name] = {"status": "down", "error": str(exc)}
            all_healthy = False

    context["ti"].xcom_push(key="health_results", value=results)
    logger.info("Health check global: %s", "OK" if all_healthy else "ISSUES")
    return all_healthy


def compute_platform_kpis(**context):
    kpis = {
        "documents_total": 0,
        "documents_validated": 0,
        "documents_curated": 0,
        "anomalies_total": 0,
        "anomalies_error": 0,
        "anomalies_warning": 0,
    }

    docs_data = requests.get(f"{BACKEND_URL}/api/documents", timeout=20).json()
    docs = docs_data.get("documents", [])
    kpis["documents_total"] = docs_data.get("total", len(docs))

    for d in docs:
        status = d.get("pipeline_status")
        if status == "validated":
            kpis["documents_validated"] += 1
        if status == "curated":
            kpis["documents_curated"] += 1

    validation = requests.get(f"{BACKEND_URL}/api/validation/results", timeout=20).json()
    anomalies = validation.get("anomalies", [])
    kpis["anomalies_total"] = len(anomalies)
    kpis["anomalies_error"] = sum(1 for a in anomalies if a.get("severity") == "ERROR")
    kpis["anomalies_warning"] = sum(1 for a in anomalies if a.get("severity") == "WARNING")

    context["ti"].xcom_push(key="kpis", value=kpis)
    logger.info("KPIs platforme: %s", kpis)
    return kpis


def emit_monitoring_report(**context):
    health = context["ti"].xcom_pull(task_ids="health_check", key="health_results") or {}
    kpis = context["ti"].xcom_pull(task_ids="compute_kpis", key="kpis") or {}

    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "services": health,
        "kpis": kpis,
    }

    logger.info("=" * 72)
    logger.info("MONITORING REPORT DOCUFLOW")
    logger.info(json.dumps(report, ensure_ascii=True, indent=2))
    logger.info("=" * 72)

    return report


with DAG(
    dag_id="monitoring_daily",
    default_args=DEFAULT_ARGS,
    description="Monitoring de la plateforme et KPIs d'industrialisation",
    schedule_interval="*/15 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["docuflow", "monitoring", "industrialisation"],
) as dag:
    t_health = PythonOperator(task_id="health_check", python_callable=check_services_health)
    t_kpis = PythonOperator(task_id="compute_kpis", python_callable=compute_platform_kpis)
    t_report = PythonOperator(task_id="report", python_callable=emit_monitoring_report)

    t_health >> t_kpis >> t_report
