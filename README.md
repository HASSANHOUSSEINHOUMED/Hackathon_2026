# 🏆 Hackathon 2026 — Validation automatique de documents

---

## 📌 Contexte

**Projet** : Pipeline de traitement de documents comptables français  
**Type** : Projet en équipe (7 personnes)  
**Stack** : Python · EasyOCR · spaCy · MinIO · React · Airflow · Docker  

Plateforme complète d'upload, classification, extraction et validation
de documents administratifs (factures, Kbis, URSSAF, RIB…)
avec auto-remplissage de deux applications métiers.

---

## 👥 Équipe & Rôles

| # | Rôle | Dossier | Port(s) |
|---|------|---------|---------|
| 1 | Scénario Maker | `dataset/` | — |
| 2 | Responsable OCR | `services/ocr/` | `:5001` |
| 3 | Front-end & API | `frontend/` `backend/` | `:3000` `:4000` |
| 4 | Chef BDD / Data Lake | `storage/` | `:9000` `:9001` `:27017` |
| 5 | Anomaly Detector | `services/validation/` | `:5002` |
| 6 | Pipeline Engineer | `dags/` | `:8080` |

---

## 🏗️ Architecture
```
Upload (PDF / Image)
    ↓
[Gate 1] Format valide ?     → ✗ Rejet
[Gate 2] Qualité image ?     → ✗ Rejet
    ↓
OCR — EasyOCR + Tesseract
[Gate 3] Texte suffisant ?   → ✗ Rejet
    ↓
Extraction Regex + spaCy NER
    ↓
Data Lake MinIO
├── raw-zone      → documents bruts
├── clean-zone    → texte OCR (JSON)
└── curated-zone  → données structurées
    ↓
Détection anomalies
    ↓
CRM  ·  Outil conformité
```

---

## 🛠️ Stack technique

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![MongoDB](https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=mongodb&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-C72E49?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-017CEE?style=flat-square&logo=apache-airflow&logoColor=white)

---

## 🚀 Lancer le projet
```bash
# 1. Cloner
git clone https://github.com/TON_PSEUDO/hackathon-2026.git
cd hackathon-2026

# 2. Variables d'environnement
cp .env.example .env

# 3. Lancer tous les services
docker compose up --build
```

### URLs

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API Node | http://localhost:4000 |
| OCR API | http://localhost:5001 |
| Validation | http://localhost:5002 |
| MinIO console | http://localhost:9001 |
| Airflow | http://localhost:8080 |

---

## 🌿 Workflow Git
```bash
# Chaque membre travaille sur SA branche
git checkout -b feat/dataset
git checkout -b feat/ocr
git checkout -b feat/frontend
git checkout -b feat/storage
git checkout -b feat/validation
git checkout -b feat/pipeline

# Committer et pousser
git add .
git commit -m "feat(storage): description du changement"
git push origin feat/storage

# Puis ouvrir une Pull Request → main sur GitHub
```

> ⚠️ **Personne ne pousse directement sur `main`**

---

## 📂 Structure du repo
```
hackathon-2026/
├── docker-compose.yml     ← Rôle 6
├── .env.example
├── README.md
├── dataset/               ← Rôle 1
├── services/
│   ├── ocr/               ← Rôle 2
│   └── validation/        ← Rôle 5
├── backend/               ← Rôle 3
├── frontend/              ← Rôle 3
├── storage/               ← Rôle 4
└── dags/                  ← Rôle 6
```

---

## 🎓 Contexte académique

**Mastère — Big Data & IA · Hackathon 2026**

---

## ⚠️ Conventions

- Chaque membre touche **uniquement son dossier**
- Secrets dans `.env`, jamais dans le code
- Commentaires en **français** dans le code métier
- **Aucun push direct sur `main`** — Pull Request obligatoire
