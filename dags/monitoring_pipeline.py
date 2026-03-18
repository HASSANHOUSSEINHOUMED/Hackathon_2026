"""
DAG Airflow : Monitoring quotidien DocuFlow.
Fréquence : tous les jours à 08h00 UTC.
Tâches : health_check → cleanup_old → daily_report
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
    "storage-api": "http://storage-api:5003/health",
}

BACKEND_URL = "http://backend:4000"

default_args = {
    "owner": "docuflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def check_services_health(**context):
    """Vérifie l'état de santé de tous les services."""
    results = {}
    all_healthy = True

    for service_name, url in SERVICES.items():
        try:
            resp = requests.get(url, timeout=10)
            healthy = resp.status_code == 200
            results[service_name] = {
                "status": "healthy" if healthy else "degraded",
                "status_code": resp.status_code,
                "response": resp.json() if healthy else None,
            }
            if not healthy:
                all_healthy = False
        except requests.RequestException as e:
            results[service_name] = {
                "status": "down",
                "error": str(e),
            }
            all_healthy = False

    logger.info("Health check : %s", "ALL OK" if all_healthy else "ISSUES DETECTED")
    for svc, status in results.items():
        level = logging.INFO if status["status"] == "healthy" else logging.ERROR
        logger.log(level, "  %s: %s", svc, status["status"])

    context["ti"].xcom_push(key="health_results", value=results)
    return all_healthy


def cleanup_old_documents(**context):
    """Nettoie les documents traités de plus de 30 jours."""
    try:
        resp = requests.get(
            f"{BACKEND_URL}/api/documents",
            params={"status": "validated"},
            timeout=15,
        )
        resp.raise_for_status()
        documents = resp.json().get("documents", [])

        cutoff = datetime.utcnow() - timedelta(days=30)
        cleaned = 0

        for doc in documents:
            created = doc.get("created_at")
            if not created:
                continue
            try:
                doc_date = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if doc_date.replace(tzinfo=None) < cutoff:
                    cleaned += 1
                    logger.info("Document ancien identifié pour archivage : %s", doc.get("document_id"))
            except (ValueError, TypeError):
                continue

        logger.info("Nettoyage : %d documents anciens identifiés sur %d total", cleaned, len(documents))
        context["ti"].xcom_push(key="cleanup_count", value=cleaned)
        return cleaned

    except requests.RequestException as e:
        logger.error("Erreur lors du nettoyage : %s", e)
        return 0


def generate_daily_report(**context):
    """Génère un rapport quotidien."""
    health = context["ti"].xcom_pull(task_ids="health_check", key="health_results") or {}
    cleanup_count = context["ti"].xcom_pull(task_ids="cleanup_old", key="cleanup_count") or 0

    # Récupérer les statistiques
    try:
        resp = requests.get(f"{BACKEND_URL}/api/documents", timeout=15)
        resp.raise_for_status()
        docs = resp.json()
        total_docs = docs.get("total", 0)
    except requests.RequestException:
        total_docs = "N/A"

    try:
        resp = requests.get(f"{BACKEND_URL}/api/validation/results", timeout=15)
        resp.raise_for_status()
        validation = resp.json()
    except requests.RequestException:
        validation = {}

    report = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "services_health": {k: v["status"] for k, v in health.items()},
        "total_documents": total_docs,
        "anomaly_summary": validation.get("anomaly_count", {}),
        "documents_archived": cleanup_count,
    }

    logger.info("═" * 60)
    logger.info("RAPPORT QUOTIDIEN DOCUFLOW - %s", report["date"])
    logger.info("═" * 60)
    logger.info("Services: %s", json.dumps(report["services_health"], indent=2))
    logger.info("Documents totaux: %s", report["total_documents"])
    logger.info("Anomalies: %s", report["anomaly_summary"])
    logger.info("Documents archivés: %s", report["documents_archived"])
    logger.info("═" * 60)

    return report


with DAG(
    dag_id="monitoring_daily",
    default_args=default_args,
    description="Monitoring quotidien de la plateforme DocuFlow",
    schedule_interval="0 8 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["docuflow", "monitoring"],
) as dag:

    t_health = PythonOperator(
        task_id="health_check",
        python_callable=check_services_health,
    )

    t_cleanup = PythonOperator(
        task_id="cleanup_old",
        python_callable=cleanup_old_documents,
    )

    t_report = PythonOperator(
        task_id="daily_report",
        python_callable=generate_daily_report,
    )

    t_health >> t_cleanup >> t_report
