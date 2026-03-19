# DAGs Airflow - DocuFlow

Pipelines d'orchestration pour le traitement automatisé des documents.

## 📦 Technologies

- **Apache Airflow 2.8.1**
- **LocalExecutor** (pas besoin de Celery/Redis)
- **PostgreSQL** comme metadata database

## 🏗️ Structure

```
dags/
├── document_pipeline.py     # Pipeline principal
└── monitoring_pipeline.py   # Pipeline de monitoring
```

## 📋 DAGs disponibles

### 1. `document_validation_pipeline`

**Fréquence :** Toutes les 5 minutes (`*/5 * * * *`)

Pipeline d'industrialisation et d'orchestration métier :

```
┌───────────────────┐    ┌────────────────────┐    ┌───────────────────┐    ┌─────────────────────┐
│ ingest_candidates │───▶│ validate_batch_... │───▶│ curate_documents  │───▶│ sync_internal_apps  │
│ (validated docs)  │    │ (regex+mini-model) │    │ (curated-zone)    │    │ (CRM+conformité)    │
└───────────────────┘    └────────────────────┘    └───────────────────┘    └─────────────────────┘
```

**Tâches :**

| Tâche | Description |
|-------|-------------|
| `ingest_candidates` | Récupère les documents `validated` à industrialiser |
| `validate_batch_context` | Revalidation batch (regex/NER léger + mini-modèle + règles) |
| `curate_documents` | Persist `curated` via `/api/process/pipeline/complete` |
| `sync_internal_apps` | Auto-remplissage CRM et statut conformité fournisseur |

### 2. `monitoring_daily`

**Fréquence :** Toutes les 15 minutes (`*/15 * * * *`)

Pipeline de monitoring plateforme :

**Tâches :**

| Tâche | Description |
|-------|-------------|
| `health_check` | Vérifie OCR, validation, backend, storage-proxy |
| `compute_kpis` | Agrège docs total/validated/curated + anomalies |
| `report` | Log du rapport d'observabilité |

## ⚙️ Configuration

### Variables Airflow

```python
# Dans l'UI Airflow: Admin > Variables
{
    "docuflow_backend_url": "http://backend:4000",
    "docuflow_ocr_url": "http://ocr-service:5001",
    "docuflow_validation_url": "http://validation-service:5002",
    "docuflow_minio_endpoint": "minio:9000"
}
```

### Connexions Airflow

```python
# Admin > Connections
# mongodb_default
conn_id = "mongodb_default"
conn_type = "mongo"
host = "mongodb"
port = 27017
login = "admin"
password = "admin"

# minio_default
conn_id = "minio_default"
conn_type = "s3"
extra = {
    "endpoint_url": "http://minio:9000",
    "aws_access_key_id": "minioadmin",
    "aws_secret_access_key": "minioadmin"
}
```

## 🚀 Accès à l'interface

- **URL :** http://localhost:8080
- **Login :** admin
- **Password :** admin

## 🔧 Commandes utiles

```bash
# Voir les logs d'un DAG
docker compose logs -f airflow-scheduler

# Déclencher manuellement un DAG
docker exec docuflow-airflow-web airflow dags trigger document_validation_pipeline

# Lister les DAGs
docker exec docuflow-airflow-web airflow dags list

# Voir l'état d'une tâche
docker exec docuflow-airflow-web airflow tasks list document_validation_pipeline
```

## 📊 Monitoring

Les métriques sont disponibles dans :
- Interface Airflow (durée, succès/échec)
- Logs Docker (`docker compose logs airflow-scheduler`)
- MongoDB (collection `pipeline_runs`)
