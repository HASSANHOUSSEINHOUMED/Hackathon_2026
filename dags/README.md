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

Pipeline principal de traitement des documents :

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Ingest    │───▶│     OCR     │───▶│  Validate   │───▶│  Finalize   │
│  (pending)  │    │  (extract)  │    │  (rules)    │    │  (update)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**Tâches :**

| Tâche | Description |
|-------|-------------|
| `ingest_documents` | Récupère les documents en `pending-zone` |
| `process_ocr` | Appelle le service OCR |
| `validate_documents` | Applique les règles de validation |
| `update_suppliers` | Met à jour le CRM automatiquement |
| `move_to_curated` | Archive en `curated-zone` |

### 2. `monitoring_pipeline`

**Fréquence :** Tous les jours à 2h (`0 2 * * *`)

Pipeline de monitoring et maintenance :

**Tâches :**

| Tâche | Description |
|-------|-------------|
| `compute_daily_stats` | Calcule les KPIs du jour |
| `check_expiring_docs` | Vérifie les documents expirant bientôt |
| `cleanup_old_raw` | Nettoie les fichiers > 30 jours |
| `send_report` | Envoie le rapport (optionnel) |

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
