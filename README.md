# DocuFlow

> **Validation automatique de documents administratifs fournisseurs**  
> Hackathon 2026

---

## 🚀 Démarrage rapide

### Prérequis

- **Docker Desktop** ≥ 24.0 avec Docker Compose v2
- **8 Go RAM** minimum
- **Git**

### Installation

```bash
# 1. Cloner le projet
git clone https://github.com/HASSANHOUSSEINHOUMED/Hackathon_2026.git
cd Hackathon_2026

# 2. Configurer l'environnement
cp .env.example .env

# 3. (Optionnel) Ajouter votre clé OpenAI pour le raffinement LLM
# Éditer .env et renseigner OPENAI_API_KEY=sk-...

# 4. Démarrer tous les services
docker compose up -d --build

# 5. Vérifier le statut
docker compose ps
```

> ⏱️ Le premier démarrage prend 5-10 minutes (téléchargement des images Docker).

### Accès aux services

| Service | URL | Identifiants |
|---------|-----|--------------|
| **Frontend** | http://localhost:3000 | — |
| **Backend API** | http://localhost:4000/api | — |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin |
| **Airflow** | http://localhost:8080 | admin / admin |

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
                     │   :27017      │     │ Règles + ML      │
                     └───────────────┘     │  :5002           │
                                           └──────────────────┘
┌──────────────┐     ┌───────────────┐
│    MinIO     │     │    Airflow    │
│  Data Lake   │     │  Orchestrator │
│  :9000/:9001 │     │  :8080        │
└──────────────┘     └───────────────┘
```

---

## 📁 Structure du projet

```
hackaton2026/
├── backend/           # API Node.js (Express, Mongoose, Socket.io)
├── frontend/          # Interface React (Vite, Tailwind, Recharts)
├── services/
│   ├── ocr/           # Service OCR (Tesseract + EasyOCR)
│   └── validation/    # Règles métier + IsolationForest
├── storage/           # Client Data Lake (MinIO + MongoDB)
├── dataset/           # Génération de documents synthétiques
├── dags/              # Pipelines Airflow
├── scripts/           # Scripts de déploiement
├── docker-compose.yml
└── .env.example
```

> Chaque dossier contient son propre `README.md` avec la documentation détaillée.

---

## 📄 Types de documents supportés

| Type | Description | Règles de validation |
|------|-------------|---------------------|
| **Facture** | Factures fournisseurs | TVA, TTC, SIRET, IBAN, montants anormaux |
| **Devis** | Propositions commerciales | TVA, TTC, date de validité |
| **Attestation URSSAF** | Vigilance sociale | SIRET, date d'expiration |
| **Kbis** | Extrait registre commerce | Péremption 90 jours |
| **Attestation SIRET** | Inscription INSEE | Format SIRET (Luhn) |
| **RIB** | Identité bancaire | Format IBAN, cohérence |

---

## 🔄 Pipeline de traitement

```
Upload     ──▶    OCR       ──▶   Validation   ──▶   CRM Auto
(PDF/IMG)       (Tesseract)      (11 règles)        (Fournisseur)
                (EasyOCR)        (IsolationForest)  (MinIO)
```

**Fonctionnalités :**
- Upload drag & drop multi-fichiers
- OCR double moteur (Tesseract + EasyOCR)
- 11 règles de validation métier
- Détection d'anomalies statistiques (ML)
- Raffinement LLM optionnel (GPT-4o-mini)
- Création automatique des fournisseurs
- Stockage Data Lake (MinIO 4 zones)

---

## 🛠️ Commandes utiles

```bash
# Démarrer
docker compose up -d

# Arrêter
docker compose down

# Logs en temps réel
docker compose logs -f backend

# Reset complet (supprime les données)
docker compose down -v

# Reconstruire un service
docker compose build --no-cache backend
docker compose up -d backend
```

---

## 🧪 Tests

```bash
# Tests OCR
docker exec docuflow-ocr pytest tests/ -v

# Tests Validation
docker exec docuflow-validation pytest tests/ -v

# Health checks
curl http://localhost:4000/api/health
curl http://localhost:5001/api/health
curl http://localhost:5002/api/health
```

---

## 📊 Génération du dataset

```bash
cd dataset
pip install -r requirements.txt

# Générer 15 documents par type
python generate.py --n 15 --output ./output

# Générer des documents avec erreurs (tests)
python generate_test_errors.py
```

---

## ⚙️ Stack technique

| Composant | Technologies |
|-----------|--------------|
| **Frontend** | React 18, Vite, Tailwind CSS, Recharts |
| **Backend** | Node.js 20, Express, Mongoose, Socket.io |
| **OCR** | Python 3.11, Tesseract, EasyOCR, OpenCV |
| **Validation** | Python 3.11, scikit-learn (IsolationForest) |
| **LLM** | OpenAI GPT-4o-mini (optionnel) |
| **Data Lake** | MinIO (S3-compatible) |
| **Base de données** | MongoDB 7.0 |
| **Orchestration** | Apache Airflow 2.8.1 |
| **Conteneurs** | Docker Compose |

---

## 👥 Équipe

Projet réalisé dans le cadre du **Hackathon 2026**.

---

## 📜 Licence

MIT

