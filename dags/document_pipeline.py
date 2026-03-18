"""
DAG Airflow : Pipeline de validation de documents administratifs.
Fréquence : toutes les 5 minutes.
Tâches : ingest → ocr → validate → autofill
"""
import json
import logging
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger("airflow.document_pipeline")

BACKEND_URL = "http://backend:4000"
OCR_URL = "http://ocr-service:5001"
VALIDATION_URL = "http://validation-service:5002"
STORAGE_URL = "http://storage-api:5003"

default_args = {
    "owner": "docuflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def ingest_pending_documents(**context):
    """Récupère les documents en attente de traitement depuis le Data Lake."""
    try:
        resp = requests.get(f"{STORAGE_URL}/stats", timeout=10)
        resp.raise_for_status()
        stats = resp.json()
        logger.info("Stats Data Lake : %s", stats)

        # Récupérer les documents en pending depuis MongoDB via le backend
        resp = requests.get(
            f"{BACKEND_URL}/api/documents",
            params={"status": "uploaded"},
            timeout=15,
        )
        resp.raise_for_status()
        documents = resp.json().get("documents", [])

        logger.info("Documents en attente : %d", len(documents))
        context["ti"].xcom_push(key="pending_documents", value=documents)
        return len(documents)
    except requests.RequestException as e:
        logger.error("Erreur récupération documents : %s", e)
        return 0


def process_ocr(**context):
    """Envoie les documents au service OCR."""
    documents = context["ti"].xcom_pull(task_ids="ingest", key="pending_documents") or []
    if not documents:
        logger.info("Aucun document à traiter")
        return []

    results = []
    for doc in documents:
        doc_id = doc.get("document_id", doc.get("_id", ""))
        try:
            # Récupérer le fichier depuis MinIO via le storage
            resp = requests.get(f"{STORAGE_URL}/document/{doc_id}", timeout=10)
            if resp.status_code != 200:
                logger.warning("Document %s non trouvé dans le storage", doc_id)
                continue

            doc_data = resp.json()
            raw_url = doc_data.get("raw_url")
            if not raw_url:
                continue

            # Appeler le service OCR
            ocr_resp = requests.post(
                f"{OCR_URL}/api/ocr",
                json={"document_id": doc_id, "file_url": raw_url},
                timeout=60,
            )
            ocr_resp.raise_for_status()
            ocr_result = ocr_resp.json()
            ocr_result["document_id"] = doc_id

            results.append(ocr_result)
            logger.info("OCR traité : %s (type=%s, confiance=%.2f)",
                        doc_id, ocr_result.get("type"), ocr_result.get("confidence", 0))

        except requests.RequestException as e:
            logger.error("Erreur OCR document %s : %s", doc_id, e)

    context["ti"].xcom_push(key="ocr_results", value=results)
    return len(results)


def validate_documents(**context):
    """Envoie les résultats OCR au service de validation."""
    ocr_results = context["ti"].xcom_pull(task_ids="ocr_processing", key="ocr_results") or []
    if not ocr_results:
        logger.info("Aucun résultat OCR à valider")
        return []

    # Préparer le payload
    documents = []
    for result in ocr_results:
        documents.append({
            "document_id": result.get("document_id"),
            "type": result.get("type", "inconnu"),
            "entities": result.get("entities", {}),
        })

    try:
        resp = requests.post(
            f"{VALIDATION_URL}/api/validate",
            json={"documents": documents},
            timeout=30,
        )
        resp.raise_for_status()
        validation_result = resp.json()
        logger.info("Validation : statut=%s, anomalies=%s",
                     validation_result.get("status"),
                     validation_result.get("anomaly_count"))

        context["ti"].xcom_push(key="validation_result", value=validation_result)
        context["ti"].xcom_push(key="ocr_documents", value=documents)
        return validation_result
    except requests.RequestException as e:
        logger.error("Erreur validation : %s", e)
        return None


def autofill_and_finalize(**context):
    """Met à jour le backend avec les résultats et notifie le frontend."""
    validation = context["ti"].xcom_pull(task_ids="validation", key="validation_result")
    documents = context["ti"].xcom_pull(task_ids="validation", key="ocr_documents") or []

    if not documents:
        logger.info("Aucun document à finaliser")
        return

    for doc in documents:
        doc_id = doc.get("document_id")
        anomalies = []
        if validation:
            anomalies = [
                a for a in validation.get("anomalies", [])
                if doc_id in a.get("concerned_document_ids", [])
            ]

        try:
            # Mettre à jour le statut du document dans le backend
            status = "validated" if not anomalies else "anomaly_detected"
            resp = requests.post(
                f"{BACKEND_URL}/api/process/pipeline/complete",
                json={
                    "document_id": doc_id,
                    "status": status,
                    "entities": doc.get("entities", {}),
                    "anomalies": anomalies,
                    "type": doc.get("type"),
                },
                timeout=15,
            )
            resp.raise_for_status()
            logger.info("Document %s finalisé : statut=%s, anomalies=%d",
                        doc_id, status, len(anomalies))

            # Auto-remplissage fournisseur
            siret = doc.get("entities", {}).get("siret")
            if siret:
                supplier_data = {
                    "siret": siret,
                    "raison_sociale": doc.get("entities", {}).get("raison_sociale", ""),
                    "tva_intra": doc.get("entities", {}).get("tva_intra", ""),
                    "iban": doc.get("entities", {}).get("iban", ""),
                    "conformity_status": "conforme" if not anomalies else "non_conforme",
                }
                resp = requests.post(
                    f"{BACKEND_URL}/api/suppliers",
                    json=supplier_data,
                    timeout=10,
                )
                resp.raise_for_status()
                logger.info("Fournisseur SIRET=%s mis à jour", siret)

        except requests.RequestException as e:
            logger.error("Erreur finalisation document %s : %s", doc_id, e)


with DAG(
    dag_id="document_validation_pipeline",
    default_args=default_args,
    description="Pipeline de traitement et validation des documents administratifs",
    schedule_interval="*/5 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["docuflow", "documents", "validation"],
) as dag:

    t_ingest = PythonOperator(
        task_id="ingest",
        python_callable=ingest_pending_documents,
    )

    t_ocr = PythonOperator(
        task_id="ocr_processing",
        python_callable=process_ocr,
    )

    t_validate = PythonOperator(
        task_id="validation",
        python_callable=validate_documents,
    )

    t_autofill = PythonOperator(
        task_id="autofill_finalize",
        python_callable=autofill_and_finalize,
    )

    t_ingest >> t_ocr >> t_validate >> t_autofill
