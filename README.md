# DocuFlow

> Validation automatique de documents administratifs fournisseurs  
> Hackathon 2026

```
╔══════════════════════════════════════════════════════════════════╗
║                        DocuFlow                                  ║
║     Validation automatique de documents administratifs           ║
╚══════════════════════════════════════════════════════════════════╝
```

## 🚀 Démarrage rapide

### Prérequis

| Outil | Version minimum | Vérification |
|-------|-----------------|--------------|
| Docker Desktop | ≥ 24.0 | `docker --version` |
| Docker Compose | v2 | `docker compose version` |
| Git | ≥ 2.30 | `git --version` |

**Ressources recommandées :** 8 Go RAM, 20 Go disque

### Installation (Windows / Linux / macOS)

```bash
# 1. Cloner le projet
git clone https://github.com/votre-repo/hackaton2026.git
cd hackaton2026

# 2. Configurer l'environnement
cp .env.example .env

# 3. (Optionnel) Ajouter votre clé OpenAI pour le raffinement LLM
# Éditer .env et renseigner OPENAI_API_KEY=sk-...

# 4. Démarrer tous les services
docker compose up -d --build

# 5. Vérifier le statut
docker compose ps
```

> ⏱️ Le premier démarrage peut prendre 5-10 minutes (téléchargement des images Docker).

### URLs des services

| Service | URL | Identifiants |
|---------|-----|--------------|
| **🖥️ Frontend** | http://localhost:3000 | — |
| **⚙️ Backend API** | http://localhost:4000/api | — |
| **📝 OCR Service** | http://localhost:5001/api | — |
| **✅ Validation** | http://localhost:5002/api | — |
| **📦 MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **🔄 Airflow** | http://localhost:8080 | admin / admin |

---

## 📐 Architecture

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│   Frontend   │────▶│  Backend API  │────▶│   OCR Service    │
│  React/Vite  │     │  Express.js   │     │ Tesseract+EasyOCR│
│  :3000       │     │  :4000        │     │  :5001           │
└──────────────┘     └───────┬───────┘     └──────────────────┘
                             │
                     ┌───────┴───────┐     ┌──────────────────┐
                     │   MongoDB     │     │ Validation Svc   │
                     │   :27017      │     │ Rules + ML       │
                     └───────────────┘     │  :5002           │
                                           └──────────────────┘
┌──────────────┐     ┌───────────────┐
│    MinIO     │     │    Airflow    │
│  Data Lake   │     │  Orchestrator │
│  :9000/:9001 │     │  :8080        │
└──────────────┘     └───────────────┘
```

## Prérequis

- **Docker Desktop** ≥ 24.0 avec Docker Compose v2
- **Git**
- 8 Go RAM minimum recommandé

## Installation rapide

```bash
# 1. Cloner le projet
git clone <repo> && cd hackaton2026

# 2. Copier la configuration
cp .env.example .env

# 3. Déployer
chmod +x scripts/*.sh
./scripts/deploy.sh
```

## URLs des services

| Service            | URL                          | Identifiants       |
|--------------------|------------------------------|-------------------|
| **Frontend**       | http://localhost:3000         | —                 |
| **Backend API**    | http://localhost:4000/api     | —                 |
| **OCR Service**    | http://localhost:5001/api     | —                 |
| **Validation**     | http://localhost:5002/api     | —                 |
| **MinIO Console**  | http://localhost:9001         | minioadmin / minioadmin |
| **Airflow**        | http://localhost:8080         | admin / admin     |

## Structure du projet

```
hackaton2026/
├── dataset/               # Génération de documents synthétiques
│   ├── generators/        # 6 types de documents PDF
│   ├── config.py          # Configuration du dataset
│   ├── company_factory.py # Générateur d'entreprises fictives
│   ├── degrade.py         # Dégradation réaliste d'images
│   ├── generate.py        # Script principal de génération
│   └── evaluate_ocr.py    # Évaluation qualité OCR
│
├── services/
│   ├── ocr/               # Service OCR (Flask, Tesseract, EasyOCR)
│   └── validation/        # Service de validation (règles + IsolationForest)
│
├── frontend/              # Interface React (Vite, Recharts)
├── backend/               # API Node.js (Express, Mongoose, Socket.io)
├── storage/               # Data Lake (MinIO + MongoDB)
│
├── dags/                  # DAGs Airflow
│   ├── document_pipeline.py   # Pipeline principal (*/5 min)
│   └── monitoring_pipeline.py # Monitoring quotidien
│
├── utils/                 # Utilitaires partagés
├── scripts/               # Scripts de déploiement
│
├── docker-compose.yml     # Orchestration complète
├── .env.example           # Variables d'environnement
└── README.md
```

## Pipeline de traitement

```
Airflow DAG : document_validation_pipeline (toutes les 5 minutes)

  ┌─────────┐    ┌─────────────┐    ┌────────────┐    ┌───────────┐
  │ Ingest  │───▶│ OCR Process │───▶│  Validate  │───▶│ Autofill  │
  │         │    │             │    │            │    │ Finalize  │
  └─────────┘    └─────────────┘    └────────────┘    └───────────┘
    Récupère       Tesseract +        12 règles        Mise à jour
    documents      EasyOCR            + IsolationForest fournisseur
    pendants       extraction         détection         CRM auto
```

## Types de documents supportés

| Type                  | Règles appliquées                              |
|-----------------------|------------------------------------------------|
| **Facture**           | TVA, TTC, SIRET, IBAN, montant anormal         |
| **Devis**             | TVA, TTC, expiration validité                  |
| **Attestation URSSAF**| SIRET, date expiration                         |
| **Attestation SIRET** | Format SIRET, Luhn                             |
| **Kbis**              | Péremption 90 jours, raison sociale            |
| **RIB**               | Format IBAN, cohérence avec factures           |

## Génération du dataset

```bash
cd dataset
pip install -r requirements.txt
python generate.py --n 50 --output ../data --scenarios all
python evaluate_ocr.py --manifest ../data/dataset_manifest.json --output ../data/eval
```

## Tests

```bash
# Tests unitaires OCR
cd services/ocr && pytest tests/

# Tests unitaires Validation
cd services/validation && pytest tests/

# Tests end-to-end (services démarrés)
./scripts/test_e2e.sh
```

## Commandes utiles

```bash
# Démarrer
./scripts/deploy.sh

# Arrêter
./scripts/stop.sh

# Réinitialiser (supprime les données)
./scripts/reset.sh

# Voir les logs
docker compose logs -f backend
docker compose logs -f ocr-service
docker compose logs -f validation-service

# Reconstruire un service
docker compose build --no-cache ocr-service
docker compose up -d ocr-service
```

## Stack technique

| Composant | Technologies |
|-----------|--------------|
| Frontend | React 18, Vite, Recharts, Lucide, react-dropzone |
| Backend | Node.js 20, Express, Mongoose, Socket.io, OpenAI |
| OCR | Python 3.11, Tesseract, EasyOCR, spaCy, OpenCV |
| Validation | Python 3.11, scikit-learn (IsolationForest) |
| Data Lake | MinIO (S3-compatible), 4 zones |
| Base de données | MongoDB 7.0 |
| Orchestration | Apache Airflow 2.8.1, LocalExecutor |
| Conteneurs | Docker Compose, multi-stage builds |

---

## 🛠️ Commandes de gestion

### Démarrage et arrêt

```bash
# Démarrer tous les services
docker compose up -d

# Arrêter tous les services
docker compose down

# Arrêter et supprimer les volumes (reset complet)
docker compose down -v
```

### Logs et débogage

```bash
# Logs en temps réel (tous les services)
docker compose logs -f

# Logs d'un service spécifique
docker compose logs -f backend
docker compose logs -f ocr-service
docker compose logs -f validation-service

# Statut des conteneurs
docker compose ps
```

### Reconstruction

```bash
# Reconstruire un service après modification
docker compose build --no-cache backend
docker compose up -d backend

# Reconstruire tout le projet
docker compose build --no-cache
docker compose up -d
```

### Nettoyage des données

```bash
# Vider MongoDB
docker exec docuflow-mongodb mongosh -u admin -p admin --authenticationDatabase admin \
  --eval "db = db.getSiblingDB('docuflow'); db.documents.deleteMany({}); db.suppliers.deleteMany({});"

# Vider MinIO
docker exec docuflow-minio mc rm --recursive --force local/raw-zone/
docker exec docuflow-minio mc rm --recursive --force local/clean-zone/
docker exec docuflow-minio mc rm --recursive --force local/curated-zone/
```

---

## 🧪 Tests

```bash
# Tests unitaires OCR
cd services/ocr && pytest tests/ -v

# Tests unitaires Validation  
cd services/validation && pytest tests/ -v

# Vérifier les endpoints
curl http://localhost:4000/api/health
curl http://localhost:5001/api/health
curl http://localhost:5002/api/health
```

---

## 📁 Structure détaillée

Chaque sous-dossier contient son propre `README.md` avec la documentation spécifique :

| Dossier | Description | Documentation |
|---------|-------------|---------------|
| `backend/` | API Node.js Express | [README](backend/README.md) |
| `frontend/` | Interface React/Vite | [README](frontend/README.md) |
| `services/ocr/` | Service OCR Python | [README](services/ocr/README.md) |
| `services/validation/` | Service de validation | [README](services/validation/README.md) |
| `storage/` | Client Data Lake | [README](storage/README.md) |
| `dataset/` | Génération de documents | [README](dataset/README.md) |
| `dags/` | Pipelines Airflow | [README](dags/README.md) |
| `scripts/` | Scripts de déploiement | [README](scripts/README.md) |

---

## 🔧 Configuration

### Variables d'environnement (.env)

```env
# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=admin

# MinIO
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin

# OpenAI (optionnel, pour le raffinement LLM)
OPENAI_API_KEY=sk-...

# Airflow
AIRFLOW_UID=50000
```

### Ports utilisés

| Port | Service |
|------|---------|
| 3000 | Frontend (React) |
| 4000 | Backend API (Express) |
| 5001 | Service OCR |
| 5002 | Service Validation |
| 5003 | Storage API |
| 9000 | MinIO API |
| 9001 | MinIO Console |
| 8080 | Airflow |
| 27017 | MongoDB |

---

## 📜 Licence

Projet réalisé dans le cadre du Hackathon 2026.

---

## 👥 Équipe

Développé avec ❤️ pour le Hackathon 2026.

