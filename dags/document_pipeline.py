"""
DAG Airflow: Orchestration d'industrialisation DocuFlow.
Frequence: toutes les 5 minutes.
Etapes: ingestion candidates -> validation batch -> passage curated -> sync CRM/conformite.
"""
import logging
from datetime import datetime, timedelta

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

logger = logging.getLogger("airflow.document_pipeline")

BACKEND_URL = "http://backend:4000"
VALIDATION_URL = "http://validation-service:5002"

DEFAULT_ARGS = {
    "owner": "docuflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}


def _safe_get_json(url: str, **kwargs):
    response = requests.get(url, timeout=kwargs.pop("timeout", 20), **kwargs)
    response.raise_for_status()
    return response.json()


def _safe_post_json(url: str, payload: dict, timeout: int = 30):
    response = requests.post(url, json=payload, timeout=timeout)
    response.raise_for_status()
    return response.json()


def ingest_candidates(**context):
    """
    Recupere les documents valides non encore passes en curated.
    On cible 'validated' pour industrialiser la fin de pipeline.
    """
    data_validated = _safe_get_json(f"{BACKEND_URL}/api/documents", params={"status": "validated", "limit": 200})
    data_ocr_done = _safe_get_json(f"{BACKEND_URL}/api/documents", params={"status": "ocr_done", "limit": 200})
    docs = (data_validated.get("documents", []) or []) + (data_ocr_done.get("documents", []) or [])

    seen_ids = set()
    dedup_docs = []
    for d in docs:
        doc_id = d.get("document_id")
        if not doc_id or doc_id in seen_ids:
            continue
        seen_ids.add(doc_id)
        dedup_docs.append(d)

    candidates = []
    for d in dedup_docs:
        candidates.append({
            "document_id": d.get("document_id"),
            "type": d.get("doc_type", "inconnu"),
            "entities": d.get("entities", {}),
            "raw_text": d.get("raw_text", ""),
            "existing_anomalies": d.get("anomalies", []),
        })

    logger.info("Candidates industrialisation: %d", len(candidates))
    context["ti"].xcom_push(key="candidates", value=candidates)
    return len(candidates)


def validate_batch_context(**context):
    """
    Relance une validation batch (regex/NER leger + mini modele + regles inter-doc).
    """
    candidates = context["ti"].xcom_pull(task_ids="ingest_candidates", key="candidates") or []
    if not candidates:
        logger.info("Aucun candidat a valider")
        context["ti"].xcom_push(key="validation_map", value={})
        return 0

    payload_docs = [
        {
            "document_id": d["document_id"],
            "type": d["type"],
            "entities": d.get("entities", {}),
            "raw_text": d.get("raw_text", ""),
        }
        for d in candidates
        if d.get("document_id")
    ]

    validation = _safe_post_json(
        f"{VALIDATION_URL}/api/validate",
        {"documents": payload_docs},
        timeout=60,
    )

    anomalies = validation.get("anomalies", [])
    validation_map = {d["document_id"]: [] for d in payload_docs}

    for anomaly in anomalies:
        for doc_id in anomaly.get("concerned_document_ids", []):
            if doc_id in validation_map:
                validation_map[doc_id].append({
                    "rule": anomaly.get("rule_id", "UNKNOWN"),
                    "severity": anomaly.get("severity", "INFO"),
                    "message": anomaly.get("message", ""),
                })

    context["ti"].xcom_push(key="validation_map", value=validation_map)
    logger.info(
        "Validation batch: docs=%d, anomalies=%d",
        len(payload_docs),
        len(anomalies),
    )
    return len(payload_docs)


def curate_documents(**context):
    """
    Finalise en curated-zone via endpoint backend pipeline complete.
    """
    candidates = context["ti"].xcom_pull(task_ids="ingest_candidates", key="candidates") or []
    validation_map = context["ti"].xcom_pull(task_ids="validate_batch_context", key="validation_map") or {}

    if not candidates:
        logger.info("Aucun document a passer en curated")
        return 0

    documents_payload = []
    all_anomalies = []

    for d in candidates:
        doc_id = d.get("document_id")
        doc_anomalies = validation_map.get(doc_id, d.get("existing_anomalies", []))

        documents_payload.append({
            "document_id": doc_id,
            "type": d.get("type", "inconnu"),
            "entities": d.get("entities", {}),
            "anomalies": doc_anomalies,
        })

        all_anomalies.extend(doc_anomalies)

    _safe_post_json(
        f"{BACKEND_URL}/api/process/pipeline/complete",
        {
            "documents": documents_payload,
            "anomalies": all_anomalies,
        },
        timeout=60,
    )

    context["ti"].xcom_push(key="curated_documents", value=documents_payload)
    logger.info("Passage curated termine pour %d documents", len(documents_payload))
    return len(documents_payload)


def sync_internal_apps(**context):
    """
    Auto-remplit les applications metiers internes:
    - CRM (fiche fournisseur)
    - Outil conformite (statut fournisseur)
    """
    docs = context["ti"].xcom_pull(task_ids="curate_documents", key="curated_documents") or []
    if not docs:
        logger.info("Aucune synchronisation CRM/conformite necessaire")
        return 0

    synced = 0
    for doc in docs:
        entities = doc.get("entities", {}) or {}
        siret = entities.get("siret")
        if not siret:
            continue

        anomalies = doc.get("anomalies", []) or []
        severity = {a.get("severity") for a in anomalies}
        if "ERROR" in severity:
            conformity = "error"
        elif "WARNING" in severity:
            conformity = "warning"
        else:
            conformity = "ok"

        payload = {
            "siret": siret,
            "raison_sociale": entities.get("raison_sociale") or f"Fournisseur {siret}",
            "tva_intra": entities.get("tva_intra") or "",
            "iban": entities.get("iban") or "",
            "conformity_status": conformity,
            "last_check": datetime.utcnow().isoformat(),
        }

        try:
            _safe_post_json(f"{BACKEND_URL}/api/suppliers", payload, timeout=20)
            synced += 1
        except requests.RequestException as exc:
            logger.error("Sync fournisseur echec (%s): %s", siret, exc)

    logger.info("Synchronisation metiers terminee: %d fournisseurs", synced)
    return synced


with DAG(
    dag_id="document_validation_pipeline",
    default_args=DEFAULT_ARGS,
    description="Pipeline ingestion, validation intelligente, curated et sync metiers",
    schedule_interval="*/5 * * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["docuflow", "industrialisation", "ingestion", "crm", "conformite"],
) as dag:

    t_ingest = PythonOperator(
        task_id="ingest_candidates",
        python_callable=ingest_candidates,
    )

    t_validate = PythonOperator(
        task_id="validate_batch_context",
        python_callable=validate_batch_context,
    )

    t_curate = PythonOperator(
        task_id="curate_documents",
        python_callable=curate_documents,
    )

    t_sync = PythonOperator(
        task_id="sync_internal_apps",
        python_callable=sync_internal_apps,
    )

    t_ingest >> t_validate >> t_curate >> t_sync
