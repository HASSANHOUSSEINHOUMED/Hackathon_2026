# Storage — Data Lake & Métadonnées

Client Python pour le stockage MinIO et MongoDB.

## Architecture de stockage

```
┌──────────────────────────────────────────────────────┐
│                    MinIO (S3)                        │
│ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌────────┐ │
│ │ pending  │ │ raw-zone  │ │clean-zone │ │curated │ │
│ │  -zone   │ │ (PDF,IMG) │ │  (JSON)   │ │ -zone  │ │
│ │ attente  │ │ 90 jours  │ │ 180 jours │ │ perman │ │
│ └──────────┘ └───────────┘ └───────────┘ └────────┘ │
└──────────────────────────────────────────────────────┘
          │                        │
          ▼                        ▼
┌──────────────────────────────────────────────────────┐
│                MongoDB (métadonnées)                  │
│  ┌──────────────┐  ┌───────────────┐                 │
│  │  documents   │  │   suppliers   │                 │
│  │  (tracking)  │  │  (CRM data)   │                 │
│  └──────────────┘  └───────────────┘                 │
└──────────────────────────────────────────────────────┘
```

## 📁 Structure

```
storage/
├── storage_client.py    # Client MinIO (upload/download)
├── mongo_client.py      # Client MongoDB (métadonnées)
├── storage_api.py       # API Flask de monitoring
├── init_storage.py      # Script d'initialisation
├── requirements.txt
└── Dockerfile.api
```

## 🗂️ Zones MinIO

| Zone | Contenu | Rétention |
|------|---------|-----------|
| `pending-zone` | Documents en attente de traitement | Court terme |
| `raw-zone` | PDFs/images bruts archivés | 90 jours |
| `clean-zone` | Résultats OCR (JSON) | 180 jours |
| `curated-zone` | Données validées et enrichies | Permanent |

## 🚀 Démarrage

```bash
# Via Docker Compose principal (recommandé)
docker compose up -d minio mongodb storage-api

# Accès MinIO Console
# URL: http://localhost:9001
# Login: minioadmin / minioadmin
```

## 🔌 API Storage (port 5003)

L'API peut être protégée par clé partagée via `STORAGE_API_KEY`.
Si cette variable est définie, les appels doivent inclure l'en-tête `X-API-Key`.

| Endpoint | Description |
|----------|-------------|
| `GET /api/storage/health` | Health check |
| `GET /api/storage/stats` | Statistiques MinIO + MongoDB |
| `GET /api/storage/document/:id` | Localisation d'un document |
| `DELETE /api/storage/document/:id` | Suppression RGPD |

## Commandes de vérification

```bash
# Tester MinIO
python -c "from storage_client import DataLakeClient; c = DataLakeClient(); print(c.get_stats())"

# Tester MongoDB
python -c "from mongo_client import MetadataDB; db = MetadataDB(); print(db.get_db_stats())"

# API de monitoring
python storage_api.py  # port 5003
curl http://localhost:5003/api/storage/health
```
