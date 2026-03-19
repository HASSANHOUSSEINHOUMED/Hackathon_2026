# DocuFlow - Hackathon 2026

## 📌 Contexte
**Projet :** Validation automatique de documents administratifs fournisseurs avec orchestration Data Lake + Airflow.  
**Cadre :** Hackathon 2026.  
**Classe :** Mastère (M1 & M2).  
**Type :** Projet en équipe (6 personnes).  
**Stack :** React 18 + Node.js/Express + MongoDB + MinIO + OCR (Tesseract/EasyOCR) + Validation ML + Airflow.

Pipeline production-ready couvrant ingestion documentaire, extraction OCR, validation multi-règles, curation Data Lake, monitoring, et synchronisation CRM/conformité.

---

## 👥 Équipe & Contributions

| # | Rôle | Nom | Livrables clés | Technologies | Ports / Services |
|---|------|-----|----------------|--------------|------------------|
| 1 | Scénario Maker | Tahina | Dataset 50-100 docs, script génération, ground truth JSON, images dégradées | Faker, ReportLab, OpenCV, API INSEE, python-stdnum | Scripts locaux |
| 2 | Responsable OCR | Abdelmalek | Service OCR, extraction entités (regex + NER), classification, API Flask | Tesseract, EasyOCR, spaCy, OpenCV, Flask | `:5001` `/api/ocr` |
| 3 | Front-end & API | Yanis | Upload drag&drop, CRM auto-rempli, dashboard conformité, API Node.js | React 18, Node.js, Express, MongoDB, Socket.io | `:3000` front, `:4000` api |
| 4 | Chef BDD / Data Lake | Hassan | MinIO 3 zones, MongoDB schémas, client Python, scripts init & monitoring | MinIO, MongoDB, Docker, PyMongo, Flask | `:9000` MinIO, `:9001` console, `:27017` Mongo |
| 5 | Anomaly Detector | Wael | Moteur de règles (12 règles), détection statistique, API validation, tests | scikit-learn, IsolationForest, python-stdnum, Flask, pytest | `:5002` `/api/validate` |
| 6 | Pipeline Engineer | Korniti | Docker Compose global (9 services), DAG Airflow, `deploy.sh`, tests E2E | Airflow, Docker, PostgreSQL, bash, XCom | `:8080` Airflow, `:5432` Postgres |

---

## 🔄 Flux de Données Complet

```
Upload documents (Front)
        ↓
OCR Service (:5001)
        ↓
Validation Service (:5002)
        ↓
Data Lake (MinIO Raw/Clean/Curated + Mongo metadata)
        ↓
Backend API (:4000)
        ↓
Apps métier (CRM + Conformité)
        ↓
Orchestration & Monitoring (Airflow :8080)
```

---

## 🛠️ Stack Technique

### Frontend & API
- React 18, Vite
- Node.js, Express, Socket.io

### OCR & Validation
- Tesseract, EasyOCR, spaCy
- Flask, scikit-learn, IsolationForest, python-stdnum

### Data & Orchestration
- MongoDB
- MinIO (S3-compatible)
- Apache Airflow + PostgreSQL

### Infra
- Docker Compose
- Scripts `deploy.sh`, `test_e2e.sh`, `reset.sh`

---

## ⚙️ Configuration de l'environnement

Un fichier `.env.example` est fourni à la racine et contient toutes les variables nécessaires.  
**Ne jamais committer le fichier `.env` — il est exclu par `.gitignore`.**

```bash
cp .env.example .env
```

> **En prod :** Changer tous les mots de passe par défaut avant déploiement.

---

## 🚀 Lancement du Projet

```bash
# 1) Cloner
git clone https://github.com/HASSANHOUSSEINHOUMED/Hackathon_2026.git
cd Hackathon_2026

# 2) Configuration
cp .env.example .env
# Éditer .env si besoin (mots de passe, clés API)

# 3) Démarrage global
docker compose up -d --build

# 4) Vérification
docker compose ps
```

### Accès principaux
- Frontend : `http://localhost:3000`
- Backend API : `http://localhost:4000/api`
- Airflow : `http://localhost:8080`
- MinIO Console : `http://localhost:9001`

---

## 💡 Décisions Architecturales

### 1. Chaîne documentaire orientée fiabilité
- Upload -> OCR -> Validation -> Curation -> Sync métier.
- Séparation claire des responsabilités par service.

### 2. Data Lake 3 zones
- Raw : brut, traçabilité source.
- Clean : OCR normalisé.
- Curated : prêt métier.

### 3. Validation hybride
- Règles explicites + détection statistique pour réduire les faux négatifs.

### 4. Orchestration industrielle
- Airflow pour batch pipeline et monitoring périodique.

---

## 📈 Résultats & Impact

- Traitement automatique de documents administratifs fournisseurs de bout en bout.
- CRM auto-rempli et dashboard conformité connectés au pipeline.
- Monitoring opérationnel des services critiques.
- Architecture démontrable en hackathon avec découpage rôles/équipes clair.

---

## 🎓 Compétences Démontrées

- Architecture Data Lake appliquée à un cas documentaire réel.
- OCR + extraction d'entités + validation multi-règles.
- APIs micro-services, orchestration Docker/Airflow.
- Monitoring, fiabilisation et sécurisation applicative.
- Collaboration d'équipe multi-rôles (Mastère M1/M2).

---

## 📂 Fichiers Livrés (principaux)

- `README.md`
- `docker-compose.yml`
- `dags/document_pipeline.py`
- `dags/monitoring_pipeline.py`
- `backend/`
- `frontend/`
- `services/ocr/`
- `services/validation/`
- `dataset/`
- `storage/`

---

## 👤 Auteurs

Projet réalisé en équipe : **Tahina, Abdelmalek, Yanis, Hassan, Wael, Korniti**.

**Formation :** Mastère (M1 & M2) Big Data & IA - IPSSI Paris.


