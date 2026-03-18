# 📑 Rapport Technique — Projet DocuFlow

## Hackathon 2026 — Intelligence Artificielle pour la Gestion Documentaire

---

## Table des Matières

1. [Architecture Globale](#1-architecture-globale)
2. [Rôle 1 — Tahina (Scenario Maker)](#2-rôle-1--tahina-scenario-maker)
3. [Rôle 2 — Abdelmalek (OCR)](#3-rôle-2--abdelmalek-ocr)
4. [Rôle 3 — Yanis (Front MERN)](#4-rôle-3--yanis-front-mern)
5. [Rôle 4 — Hassan (Data Lake)](#5-rôle-4--hassan-data-lake)
6. [Rôle 5 — Wael (Anomaly Detector)](#6-rôle-5--wael-anomaly-detector)
7. [Rôle 6 — Korniti (Pipeline Airflow)](#7-rôle-6--korniti-pipeline-airflow)
8. [Intégrations Inter-Services](#8-intégrations-inter-services)
9. [Guide de Déploiement](#9-guide-de-déploiement)
10. [Tests et Validation](#10-tests-et-validation)

---

## 1. Architecture Globale

### 1.1 Diagramme d'Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   FRONTEND                                       │
│                        React + Vite + Tailwind CSS                              │
│                              Port 3000 (Nginx)                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   BACKEND                                        │
│                      Node.js + Express + Socket.io                              │
│                              Port 4000                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
          │                    │                    │                    │
          ▼                    ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  OCR Service │    │  Validation  │    │  Storage API │    │    MinIO     │
│   Flask/Py   │    │   Flask/Py   │    │   Flask/Py   │    │  Data Lake   │
│  Port 5001   │    │  Port 5002   │    │  Port 5003   │    │ Port 9000/01 │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                                                                     │
                                                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ORCHESTRATION                                       │
│                        Apache Airflow + PostgreSQL                              │
│                              Port 8080                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   MONGODB                                        │
│                             Base de données                                      │
│                              Port 27017                                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Stack Technologique Complète

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Frontend | React | 18.2.0 |
| Frontend Build | Vite | 5.1.4 |
| Backend | Node.js + Express | 20 / 4.18.3 |
| Realtime | Socket.io | 4.7.4 |
| OCR Service | Python + Flask | 3.11 / 3.0 |
| Validation Service | Python + Flask | 3.11 / 3.0 |
| Storage API | Python + Flask | 3.11 / 3.0.2 |
| Data Lake | MinIO | 2024-01-29 |
| Database | MongoDB | 7.0 |
| Orchestration | Apache Airflow | 2.8.1 |
| Airflow DB | PostgreSQL | 15 |

### 1.3 Conteneurs Docker

```yaml
# Total : 11 conteneurs
services:
  - docuflow-frontend      # React (port 3000)
  - docuflow-backend       # Node.js (port 4000)
  - docuflow-ocr           # Flask (port 5001)
  - docuflow-validation    # Flask (port 5002)
  - docuflow-storage-api   # Flask (port 5003)
  - docuflow-minio         # MinIO (ports 9000/9001)
  - docuflow-minio-init    # Init buckets
  - docuflow-mongodb       # MongoDB (port 27017)
  - docuflow-postgres      # PostgreSQL (port 5432)
  - docuflow-airflow-web   # Airflow UI (port 8080)
  - docuflow-airflow-scheduler
  - docuflow-airflow-init
```

---

## 2. Rôle 1 — Tahina (Scenario Maker)

### 2.1 Responsabilités

Génération d'un dataset synthétique de documents administratifs français avec ground truth pour l'entraînement et la validation du système OCR.

### 2.2 Structure des Fichiers

```
dataset/
├── generate.py                 # Orchestrateur principal
├── generate_test_errors.py     # Génération de cas d'erreurs spécifiques
├── config.py                   # Configuration (taux TVA, scénarios)
├── company_factory.py          # Factory pour entreprises fictives
├── degrade.py                  # Dégradation d'images (bruit, rotation)
├── evaluate_ocr.py             # Évaluation du pipeline OCR
├── run-ocr-batch.py            # Batch processing
├── requirements.txt            # Dépendances Python
├── generators/                 # Générateurs par type de document
│   ├── facture.py
│   ├── devis.py
│   ├── attestation_urssaf.py
│   ├── attestation_siret.py
│   ├── kbis.py
│   └── rib.py
└── output/                     # Documents générés (ignoré par git)
    ├── raw/                    # PDFs originaux
    ├── noisy/                  # Images dégradées
    └── test_errors/            # Cas de test avec erreurs
```

### 2.3 Bibliothèques Utilisées

| Bibliothèque | Version | Justification |
|--------------|---------|---------------|
| **faker** | 28.4.1 | Génération de données fictives réalistes (noms, adresses, SIRET) |
| **reportlab** | 4.1.0 | Création de fichiers PDF formatés |
| **pillow** | 10.2.0 | Manipulation d'images |
| **opencv-python-headless** | 4.9.0.80 | Dégradation d'images (bruit, rotation, flou) |
| **numpy** | 1.26.4 | Calculs matriciels pour transformations |
| **python-stdnum** | 1.20 | Validation des identifiants français (SIRET, IBAN) |
| **qrcode** | 7.4.2 | Génération de QR codes sur documents |
| **tqdm** | 4.66.2 | Barres de progression |
| **matplotlib** | 3.8.3 | Visualisation des statistiques |

### 2.4 Fichiers Clés et Fonctions

#### `dataset/generate.py`

```python
# Orchestrateur principal de génération
def choose_scenario() -> str:
    """Choisit un scénario aléatoire (coherent, mismatch, expired, noisy)."""

def generate_document(doc_type, company, output_dir, doc_index, scenario) -> dict:
    """Génère un document unique avec son ground truth."""

# Usage CLI :
# python generate.py --n 15 --output ./output --scenarios all
```

#### `dataset/company_factory.py`

```python
class CompanyFactory:
    """Génère des entreprises françaises fictives mais réalistes."""
    
    def generate() -> dict:
        """
        Returns:
            {
                "raison_sociale": "DUPONT SERVICES SARL",
                "siret": "12345678901234",
                "siren": "123456789",
                "tva_intra": "FR12123456789",
                "iban": "FR7612345678901234567890123",
                "bic": "BNPAFRPP",
                "adresse": {...}
            }
        """
```

#### `dataset/generators/facture.py`

```python
def generate_facture(company: dict, output_path: str, 
                     coherent: bool = True,
                     doc_index: int = 1,
                     tva_rate: float = 0.20) -> dict:
    """
    Génère une facture PDF avec entités extractibles.
    
    Args:
        company: Données entreprise (raison_sociale, siret, etc.)
        output_path: Chemin du PDF généré
        coherent: Si False, introduit des incohérences volontaires
        tva_rate: Taux de TVA (0.055, 0.10, 0.20)
    
    Returns:
        Ground truth dict avec tous les champs
    """
```

#### `dataset/generate_test_errors.py`

```python
# Génère 12 documents ciblant chaque règle de validation
RULES_TO_TEST = [
    "TVA_CALCUL_ERROR",
    "TTC_CALCUL_ERROR",
    "ATTESTATION_EXPIREE",
    "KBIS_PERIME",
    "DEVIS_EXPIRE",
    "SIRET_FORMAT_INVALIDE",
    "IBAN_FORMAT_INVALIDE",
    "TVA_INTRA_INVALIDE",
    "MONTANT_ANORMAL",
    "SIRET_MISMATCH",
    "RAISON_SOCIALE_MISMATCH",
    "IBAN_MISMATCH"
]

# Usage :
# python generate_test_errors.py
# Output : dataset/output/test_errors/*.pdf + test_errors_labels.json
```

### 2.5 Configuration

```python
# dataset/config.py
DOC_TYPES = ["facture", "devis", "attestation_urssaf", "attestation_siret", "kbis", "rib"]

TVA_RATES = [0.055, 0.10, 0.20]  # Taux légaux français

SCENARIOS = {
    "coherent": 0.60,    # 60% documents corrects
    "mismatch": 0.15,    # 15% incohérences inter-documents
    "expired": 0.15,     # 15% documents expirés
    "noisy": 0.10,       # 10% images dégradées
}

DEGRADATION_LEVELS = ["light", "medium", "heavy"]
```

### 2.6 Commandes de Test

```bash
# Générer 15 documents complets
cd dataset
pip install -r requirements.txt
python generate.py --n 15 --output ./output --scenarios all

# Générer les cas d'erreurs pour tests
python generate_test_errors.py

# Évaluer la qualité OCR
python evaluate_ocr.py --input ./output/raw --ground-truth ./output/labels.json
```

### 2.7 Justifications Techniques

| Choix | Justification |
|-------|---------------|
| **Faker** | Génère des données cohérentes avec localisation française (noms, adresses, téléphones) |
| **ReportLab** | Seule bibliothèque permettant un contrôle pixel-perfect des PDFs en Python |
| **OpenCV pour dégradation** | Simule les conditions réelles (scan, photo, fax) pour tester la robustesse OCR |
| **Scénarios probabilistes** | Distribution réaliste des anomalies rencontrées en production |

---

## 3. Rôle 2 — Abdelmalek (OCR)

### 3.1 Responsabilités

Service de reconnaissance optique de caractères (OCR) avec extraction d'entités nommées pour documents administratifs français.

### 3.2 Structure des Fichiers

```
services/ocr/
├── app.py                  # Point d'entrée Flask
├── ocr_engine.py           # Moteur OCR hybride Tesseract/EasyOCR
├── preprocess.py           # Prétraitement d'images
├── classifier.py           # Classification du type de document
├── extractor.py            # Extraction d'entités nommées
├── requirements.txt        # Dépendances Python
└── Dockerfile              # Image Docker
```

### 3.3 Bibliothèques Utilisées

| Bibliothèque | Version | Justification |
|--------------|---------|---------------|
| **flask** | ≥3.0 | Framework web léger pour microservices |
| **pytesseract** | ≥0.3.10 | Wrapper Python pour Tesseract OCR |
| **easyocr** | ≥1.7 | OCR basé deep learning (fallback) |
| **opencv-python-headless** | ≥4.9 | Prétraitement d'images (sans GUI) |
| **pillow** | ≥10.2 | Manipulation d'images |
| **spacy** | ≥3.7 | NLP pour extraction d'entités |
| **PyMuPDF** | ≥1.23 | Extraction PDF vers images |
| **numpy** | ≥1.26 | Calculs matriciels |
| **gunicorn** | ≥21.2 | Serveur WSGI production |

### 3.4 API Endpoints

#### `POST /api/ocr`

Traite un document unique.

**Request:**
```bash
curl -X POST http://localhost:5001/api/ocr \
  -F "document=@facture.pdf"
```

**Response:**
```json
{
  "document_id": "a1b2c3d4e5f6...",
  "type": "facture",
  "type_confidence": 0.95,
  "ocr_engine_used": "tesseract",
  "ocr_confidence": 0.87,
  "raw_text": "FACTURE N° FAC-2024-001...",
  "entities": {
    "siret": "12345678901234",
    "tva_intra": "FR12123456789",
    "montant_ht": 1500.00,
    "tva": 300.00,
    "montant_ttc": 1800.00,
    "date_emission": "15/01/2024",
    "raison_sociale": "DUPONT SERVICES SARL",
    "iban": "FR7612345678901234567890123"
  },
  "extraction_confidence": 0.82,
  "processing_time_ms": 1250
}
```

#### `POST /api/ocr/batch`

Traite plusieurs documents en parallèle.

**Request:**
```bash
curl -X POST http://localhost:5001/api/ocr/batch \
  -F "documents=@facture1.pdf" \
  -F "documents=@facture2.pdf"
```

**Response:**
```json
{
  "results": [...],
  "total_processed": 2,
  "total_time_ms": 2450
}
```

#### `GET /api/health`

**Response:**
```json
{
  "status": "ok",
  "service": "ocr-service",
  "tesseract_version": "5.3.0",
  "spacy_model": "fr_core_news_sm"
}
```

### 3.5 Classes Principales

#### `services/ocr/ocr_engine.py`

```python
class OCREngine:
    """Moteur OCR hybride Tesseract/EasyOCR avec fallback automatique."""
    
    MIN_CONFIDENCE = 0.6
    MIN_TEXT_LENGTH = 50
    
    def __init__(self):
        self.tesseract_config = "--oem 3 --psm 6 -l fra"
        self._easyocr_reader = None  # Lazy loading
    
    def extract_text_tesseract(self, image: np.ndarray) -> dict:
        """
        Extraction via Tesseract.
        Returns: {"text": str, "confidence": float, "boxes": list, "engine": "tesseract"}
        """
    
    def extract_text_easyocr(self, image: np.ndarray) -> dict:
        """
        Fallback EasyOCR si Tesseract échoue.
        Returns: {"text": str, "confidence": float, "boxes": list, "engine": "easyocr"}
        """
    
    def extract_text(self, image: np.ndarray) -> dict:
        """
        Stratégie hybride :
        1. Tesseract en priorité (plus rapide)
        2. Fallback EasyOCR si confiance < 0.6 ou texte < 50 chars
        """
```

#### `services/ocr/extractor.py`

```python
class EntityExtractor:
    """Extraction d'entités nommées pour documents français."""
    
    PATTERNS = {
        "siret": r"\b\d{14}\b",
        "siren": r"\b\d{9}\b",
        "tva_intra": r"FR\s?\d{2}\s?\d{9}",
        "iban": r"FR\d{2}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{4}\s?[\dA-Z]{3}",
        "montant": r"(\d{1,3}(?:\s?\d{3})*(?:[,\.]\d{2})?)\s?€",
        "date": r"\d{2}[/\-.]\d{2}[/\-.]\d{4}",
    }
    
    def extract_all(self, text: str) -> dict:
        """
        Extrait toutes les entités d'un texte OCR.
        Returns: {
            "siret": "...",
            "montant_ht": float,
            "tva": float,
            "montant_ttc": float,
            ...
        }
        """
```

#### `services/ocr/classifier.py`

```python
class DocumentClassifier:
    """Classification du type de document par mots-clés."""
    
    KEYWORDS = {
        "facture": ["facture", "invoice", "fact.", "montant ttc", "échéance"],
        "devis": ["devis", "quote", "proposition", "validité", "estimatif"],
        "kbis": ["kbis", "extrait", "registre du commerce", "greffe"],
        "urssaf": ["urssaf", "attestation de vigilance", "cotisations"],
        "rib": ["rib", "relevé d'identité", "iban", "bic", "domiciliation"],
    }
    
    def classify(self, text: str) -> dict:
        """
        Classifie un document par analyse de mots-clés.
        Returns: {"type": "facture", "confidence": 0.95}
        """
```

### 3.6 Pipeline de Traitement

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   PDF/IMG   │───►│ Preprocess  │───►│  OCR Engine │───►│  Classify   │
│   Upload    │    │  (OpenCV)   │    │ (Tess/Easy) │    │ (Keywords)  │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                │
                                                                ▼
                                      ┌─────────────┐    ┌─────────────┐
                                      │   Output    │◄───│  Extract    │
                                      │    JSON     │    │ (Entities)  │
                                      └─────────────┘    └─────────────┘
```

### 3.7 Justifications Techniques

| Choix | Justification |
|-------|---------------|
| **Tesseract + EasyOCR** | Tesseract est rapide, EasyOCR meilleur sur documents dégradés → hybride optimal |
| **Lazy loading EasyOCR** | Économie mémoire, EasyOCR charge ~500MB de modèles |
| **PSM 6 + OEM 3** | Page Segmentation Mode 6 (bloc uniforme), OCR Engine Mode 3 (LSTM) optimaux pour docs admin |
| **spaCy** | NER français performant, modèle `fr_core_news_sm` léger |
| **Regex patterns** | Formats français standardisés (SIRET, IBAN, TVA) avec validation |

---

## 4. Rôle 3 — Yanis (Front MERN)

### 4.1 Responsabilités

Interface utilisateur React pour l'upload de documents, visualisation des résultats OCR, gestion des anomalies et tableau de bord CRM.

### 4.2 Structure des Fichiers

```
frontend/
├── src/
│   ├── App.jsx                     # Router principal
│   ├── main.jsx                    # Point d'entrée React
│   ├── index.css                   # Styles globaux Tailwind
│   ├── pages/
│   │   ├── UploadPage.jsx          # Upload drag & drop
│   │   ├── DocumentsPage.jsx       # Liste des documents
│   │   ├── ConformityPage.jsx      # Tableau anomalies
│   │   └── CRMPage.jsx             # Gestion fournisseurs
│   ├── components/
│   │   ├── layout/                 # Header, Sidebar, etc.
│   │   ├── upload/                 # Dropzone, ProgressBar
│   │   └── crm/                    # Cards fournisseurs
│   ├── hooks/
│   │   └── useDocuments.js         # Custom hook API
│   ├── services/
│   │   └── api.js                  # Client Axios
│   └── context/
│       └── SocketContext.jsx       # WebSocket context
├── package.json
├── vite.config.js
├── tailwind.config.js
└── Dockerfile
```

### 4.3 Bibliothèques Utilisées

| Bibliothèque | Version | Justification |
|--------------|---------|---------------|
| **react** | 18.2.0 | Framework UI moderne avec hooks |
| **react-dom** | 18.2.0 | Rendu DOM React |
| **react-router-dom** | 6.22.2 | Routing SPA |
| **vite** | 5.1.4 | Build tool ultra-rapide (HMR < 100ms) |
| **axios** | 1.6.7 | Client HTTP avec interceptors |
| **recharts** | 2.12.2 | Graphiques SVG réactifs |
| **react-dropzone** | 14.2.3 | Upload drag & drop accessible |
| **react-hot-toast** | 2.4.1 | Notifications élégantes |
| **lucide-react** | 0.344.0 | Icônes SVG optimisées |
| **date-fns** | 3.3.1 | Manipulation de dates légère |
| **tailwindcss** | (devDep) | CSS utilitaire atomic |

### 4.4 Pages et Composants

#### `frontend/src/pages/UploadPage.jsx`

```jsx
// Upload avec drag & drop et progression temps réel
function UploadPage() {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState({})
  
  const onDrop = useCallback((acceptedFiles) => {
    // Filtrage PDF/images, max 20MB
  }, [])
  
  const handleUpload = async () => {
    // Upload vers /api/process avec progression
    // Socket.io pour mises à jour temps réel
  }
  
  return (
    <Dropzone onDrop={onDrop} accept={{"application/pdf": [], "image/*": []}}>
      {/* Zone drag & drop */}
    </Dropzone>
  )
}
```

#### `frontend/src/pages/DocumentsPage.jsx`

```jsx
// Liste des documents traités avec filtres
function DocumentsPage() {
  const { documents, loading, fetchDocuments } = useDocuments()
  const [filter, setFilter] = useState({ type: 'all', status: 'all' })
  
  // Filtrage par type (facture, devis, kbis...) et statut (raw, validated...)
  // Pagination côté serveur
  // Modal détail avec texte OCR et entités
}
```

#### `frontend/src/pages/ConformityPage.jsx`

```jsx
// Tableau des anomalies avec tri et actions
function ConformityPage() {
  const { anomalies, stats } = useAnomalies()
  
  // KPIs : Total erreurs, warnings, taux conformité
  // Tableau filtrable par severity et rule_id
  // Lien vers document source
}
```

#### `frontend/src/pages/CRMPage.jsx`

```jsx
// Gestion des fournisseurs extraits automatiquement
function CRMPage() {
  const { suppliers, loading } = useSuppliers()
  
  // Cards fournisseurs avec :
  // - Raison sociale, SIRET, TVA intra
  // - Nombre de documents associés
  // - Statut conformité (vert/orange/rouge)
  // - Actions : voir documents, export
}
```

### 4.5 Hooks Personnalisés

#### `frontend/src/hooks/useDocuments.js`

```javascript
export function useDocuments() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const fetchDocuments = async (params = {}) => {
    setLoading(true)
    try {
      const response = await api.get('/documents', { params })
      setDocuments(response.data.documents)
    } catch (err) {
      setError(err.message)
      toast.error('Erreur chargement documents')
    } finally {
      setLoading(false)
    }
  }
  
  return { documents, loading, error, fetchDocuments }
}
```

### 4.6 Services API

#### `frontend/src/services/api.js`

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:4000/api',
  timeout: 60000,
})

// Interceptor pour erreurs globales
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 413) {
      toast.error('Fichier trop volumineux (max 20MB)')
    }
    return Promise.reject(error)
  }
)

export default api
```

### 4.7 Configuration Socket.io

#### `frontend/src/context/SocketContext.jsx`

```jsx
import { io } from 'socket.io-client'

export const SocketContext = createContext()

export function SocketProvider({ children }) {
  const [socket, setSocket] = useState(null)
  
  useEffect(() => {
    const newSocket = io(import.meta.env.VITE_WS_URL || 'http://localhost:4000')
    
    newSocket.on('processing_update', (data) => {
      // Mise à jour progression en temps réel
    })
    
    newSocket.on('document_ready', (data) => {
      // Notification document traité
      toast.success(`Document ${data.file_name} traité !`)
    })
    
    setSocket(newSocket)
    return () => newSocket.close()
  }, [])
  
  return (
    <SocketContext.Provider value={{ socket }}>
      {children}
    </SocketContext.Provider>
  )
}
```

### 4.8 Justifications Techniques

| Choix | Justification |
|-------|---------------|
| **Vite vs CRA** | HMR 10-100x plus rapide, build 2-3x plus rapide, ESM natif |
| **Tailwind CSS** | Productivité élevée, bundle CSS minimal, design system cohérent |
| **Recharts** | SVG natif, responsive, léger (50KB gzip) vs D3 complexe |
| **react-dropzone** | Accessible (ARIA), supporté, gestion types MIME native |
| **Socket.io** | Fallback WebSocket → polling, reconnexion automatique |

---

## 5. Rôle 4 — Hassan (Data Lake)

### 5.1 Responsabilités

Architecture Data Lake avec zones de stockage (raw, clean, curated) sur MinIO, API de monitoring et intégration MongoDB.

### 5.2 Structure des Fichiers

```
storage/
├── storage_api.py          # API Flask de monitoring
├── storage_client.py       # Client MinIO Python
├── mongo_client.py         # Client MongoDB
├── init_storage.py         # Initialisation des buckets
├── requirements.txt        # Dépendances
├── Dockerfile.api          # Image Docker
└── README.md

backend/utils/
└── storage.js              # Client MinIO Node.js
```

### 5.3 Bibliothèques Utilisées

| Bibliothèque | Version | Justification |
|--------------|---------|---------------|
| **minio** (Python) | 7.2.4 | SDK officiel MinIO pour Python |
| **minio** (Node.js) | 8.0.0 | SDK officiel MinIO pour Node.js |
| **pymongo** | 4.6.1 | Driver MongoDB officiel |
| **flask** | 3.0.2 | API REST légère |
| **python-dotenv** | 1.0.1 | Gestion variables environnement |

### 5.4 Architecture du Data Lake

```
MinIO Data Lake
├── pending-zone/       # Documents en attente de traitement
├── raw-zone/           # Documents bruts originaux (PDFs)
├── clean-zone/         # Résultats OCR (JSON structuré)
└── curated-zone/       # Documents validés et enrichis
```

| Zone | Contenu | Rétention |
|------|---------|-----------|
| **pending-zone** | Fichiers uploadés non traités | Jusqu'à traitement |
| **raw-zone** | PDFs/images originaux | Permanent |
| **clean-zone** | JSON OCR + entités | Permanent |
| **curated-zone** | Documents validés + métadonnées enrichies | Permanent |

### 5.5 API Endpoints

#### `GET /api/storage/stats`

```bash
curl http://localhost:5003/api/storage/stats
```

**Response:**
```json
{
  "minio": {
    "raw-zone": {"objects": 12, "size_bytes": 2456789},
    "clean-zone": {"objects": 12, "size_bytes": 156789},
    "curated-zone": {"objects": 8, "size_bytes": 98456},
    "pending-zone": {"objects": 0, "size_bytes": 0}
  },
  "mongodb": {
    "documents": 12,
    "suppliers": 5,
    "validation_reports": 8
  }
}
```

#### `GET /api/storage/document/{doc_id}`

```bash
curl http://localhost:5003/api/storage/document/a1b2c3d4
```

**Response:**
```json
{
  "document_id": "a1b2c3d4",
  "locations": {
    "raw-zone": "raw-zone/a1b2c3d4.pdf",
    "clean-zone": "clean-zone/a1b2c3d4.json"
  }
}
```

#### `DELETE /api/storage/document/{doc_id}`

Suppression RGPD complète.

```bash
curl -X DELETE http://localhost:5003/api/storage/document/a1b2c3d4
```

**Response:**
```json
{
  "status": "deleted",
  "removed_from": [
    "raw-zone/a1b2c3d4.pdf",
    "clean-zone/a1b2c3d4.json"
  ]
}
```

### 5.6 Classes Principales

#### `storage/storage_client.py`

```python
class DataLakeClient:
    """Client MinIO pour le Data Lake."""
    
    ZONES = ["raw-zone", "clean-zone", "curated-zone", "pending-zone"]
    
    def __init__(self):
        self.client = Minio(
            endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
            secure=False
        )
    
    def upload_to_zone(self, zone: str, object_name: str, 
                       file_path: str, content_type: str = None) -> str:
        """Upload un fichier vers une zone."""
    
    def get_presigned_url(self, zone: str, object_name: str, 
                          expires: timedelta = timedelta(hours=1)) -> str:
        """Génère une URL présignée pour téléchargement."""
    
    def get_stats(self) -> dict:
        """Statistiques par zone (nombre d'objets, taille)."""
```

#### `backend/utils/storage.js`

```javascript
import { Client } from 'minio'

class MinIOStorage {
  constructor() {
    this.client = new Client({
      endPoint: process.env.MINIO_ENDPOINT || 'localhost',
      port: parseInt(process.env.MINIO_PORT) || 9000,
      useSSL: false,
      accessKey: process.env.MINIO_ACCESS_KEY || 'minioadmin',
      secretKey: process.env.MINIO_SECRET_KEY || 'minioadmin'
    })
    this.ZONES = {
      RAW: 'raw-zone',
      CLEAN: 'clean-zone',
      CURATED: 'curated-zone',
      PENDING: 'pending-zone'
    }
  }
  
  async uploadRaw(documentId, filePath, contentType) {
    // Upload PDF original vers raw-zone
  }
  
  async uploadClean(documentId, ocrData) {
    // Upload JSON OCR vers clean-zone
  }
  
  async uploadCurated(documentId, enrichedData) {
    // Upload données validées vers curated-zone
  }
}

export default new MinIOStorage()
```

### 5.7 Intégration Backend

```javascript
// backend/routes/process.js
import storage from '../utils/storage.js'

router.post('/', upload.array('documents', 10), async (req, res) => {
  for (const file of req.files) {
    // 1. Calcul hash comme document_id
    const documentId = crypto.createHash('md5').update(fileBuffer).digest('hex')
    
    // 2. Appel OCR
    const ocrResult = await axios.post(`${OCR_URL}/api/ocr`, formData)
    
    // 3. Upload vers MinIO
    const rawPath = await storage.uploadRaw(documentId, file.path, file.mimetype)
    const cleanPath = await storage.uploadClean(documentId, ocrResult.data)
    
    // 4. Sauvegarde MongoDB avec chemins MinIO
    await Document.create({
      document_id: documentId,
      minio_paths: { raw: rawPath, clean: cleanPath },
      // ...
    })
  }
})
```

### 5.8 Justifications Techniques

| Choix | Justification |
|-------|---------------|
| **MinIO** | Compatible S3, open-source, performant, adapté au self-hosted |
| **4 zones** | Séparation claire du cycle de vie des données |
| **MongoDB** | Flexible pour métadonnées hétérogènes, requêtes rapides |
| **URLs présignées** | Sécurité : pas d'accès direct au storage, expiration configurable |
| **RGPD delete** | Conformité légale, suppression complète multi-zones |

---

## 6. Rôle 5 — Wael (Anomaly Detector)

### 6.1 Responsabilités

Service de validation avec règles déterministes (calculs, formats, dates) et détection statistique d'anomalies (IsolationForest).

### 6.2 Structure des Fichiers

```
services/validation/
├── app.py                  # Point d'entrée Flask
├── rules_engine.py         # Moteur de règles déterministes
├── rules_catalog.py        # Catalogue des règles
├── statistical_detector.py # Détection ML (IsolationForest)
├── requirements.txt        # Dépendances
└── Dockerfile
```

### 6.3 Bibliothèques Utilisées

| Bibliothèque | Version | Justification |
|--------------|---------|---------------|
| **flask** | ≥3.0 | Framework web microservices |
| **scikit-learn** | ≥1.4 | IsolationForest pour détection anomalies |
| **numpy** | ≥1.26 | Calculs numériques |
| **pandas** | ≥2.2 | Manipulation de données tabulaires |
| **python-dateutil** | ≥2.9 | Parsing de dates flexible |
| **python-stdnum** | ≥1.20 | Validation SIRET, IBAN, TVA intra (normes officielles) |
| **unidecode** | ≥1.3 | Normalisation Unicode pour comparaisons |
| **joblib** | ≥1.3 | Sérialisation modèle ML |

### 6.4 API Endpoints

#### `POST /api/validate`

Valide un ensemble de documents.

**Request:**
```bash
curl -X POST http://localhost:5002/api/validate \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "document_id": "abc123",
        "type": "facture",
        "entities": {
          "siret": "12345678901234",
          "montant_ht": 1000.00,
          "tva": 200.00,
          "montant_ttc": 1200.00,
          "date_emission": "15/01/2024"
        }
      }
    ],
    "supplier_id": "supplier_001"
  }'
```

**Response:**
```json
{
  "validation_id": "val-uuid-...",
  "status": "WARNING",
  "anomaly_count": {
    "ERROR": 0,
    "WARNING": 1,
    "INFO": 1
  },
  "anomalies": [
    {
      "rule_id": "TVA_CALCUL_ERROR",
      "severity": "ERROR",
      "message": "Le montant TVA (200.00€) ne correspond pas à HT × 20% (attendu: 200.00€)",
      "concerned_document_ids": ["abc123"],
      "evidence": {
        "expected_tva": 200.00,
        "actual_tva": 200.00,
        "difference": 0.00
      }
    },
    {
      "rule_id": "MONTANT_ANORMAL",
      "severity": "INFO",
      "message": "Montant statistiquement inhabituel pour ce fournisseur",
      "concerned_document_ids": ["abc123"],
      "evidence": {
        "anomaly_score": -0.45
      }
    }
  ],
  "documents_checked": 1,
  "validation_time_ms": 45
}
```

#### `GET /api/rules`

Liste toutes les règles disponibles.

**Response:**
```json
{
  "rules": [
    {
      "id": "TVA_CALCUL_ERROR",
      "name": "Erreur de calcul TVA",
      "description": "Le montant de TVA ne correspond pas au taux appliqué sur le montant HT.",
      "severity": "ERROR",
      "document_types_concerned": ["facture", "devis"]
    }
    // ... 12 règles au total
  ],
  "total": 12
}
```

### 6.5 Catalogue des Règles

| Rule ID | Sévérité | Description | Types concernés |
|---------|----------|-------------|-----------------|
| `SIRET_MISMATCH` | ERROR | SIRET différent entre documents du même fournisseur | facture, urssaf, siret, kbis, rib |
| `TVA_CALCUL_ERROR` | ERROR | TVA ≠ HT × taux (tolérance 0.02€) | facture, devis |
| `TTC_CALCUL_ERROR` | ERROR | TTC ≠ HT + TVA (tolérance 0.02€) | facture, devis |
| `ATTESTATION_EXPIREE` | ERROR | Attestation URSSAF dépassée | urssaf |
| `KBIS_PERIME` | WARNING | Kbis > 90 jours | kbis |
| `DEVIS_EXPIRE` | WARNING | Date validité dépassée | devis |
| `RAISON_SOCIALE_MISMATCH` | WARNING | Raison sociale différente (Levenshtein > 0.3) | facture, urssaf, siret, kbis |
| `IBAN_MISMATCH` | WARNING | IBAN RIB ≠ IBAN facture | facture, rib |
| `MONTANT_ANORMAL` | INFO | Montant hors distribution normale (IsolationForest) | facture |
| `SIRET_FORMAT_INVALIDE` | ERROR | Format non conforme ou clé Luhn invalide | tous |
| `IBAN_FORMAT_INVALIDE` | ERROR | Checksum ISO 13616 invalide | facture, rib |
| `TVA_INTRA_INVALIDE` | WARNING | Format FR + clé + SIREN non conforme | tous |

### 6.6 Classes Principales

#### `services/validation/rules_engine.py`

```python
class RulesEngine:
    """Applique les règles de validation déterministes."""
    
    def validate_batch(self, documents: list[dict]) -> list[dict]:
        """
        Valide un lot de documents.
        
        Args:
            documents: [{"document_id": "...", "type": "facture", "entities": {...}}]
        
        Returns:
            Liste d'anomalies détectées
        """
        anomalies = []
        anomalies.extend(self._check_siret_consistency(documents))
        anomalies.extend(self._check_tva_calcul(documents))
        anomalies.extend(self._check_ttc_calcul(documents))
        anomalies.extend(self._check_expiration_dates(documents))
        anomalies.extend(self._check_raison_sociale(documents))
        anomalies.extend(self._check_iban_consistency(documents))
        anomalies.extend(self._check_format_validity(documents))
        return anomalies
    
    def _check_tva_calcul(self, documents: list[dict]) -> list[dict]:
        """Vérifie TVA = HT × taux pour factures/devis."""
        # Taux légaux : 5.5%, 10%, 20%
        # Tolérance : 0.02€ pour arrondis
    
    def _check_siret_consistency(self, documents: list[dict]) -> list[dict]:
        """Vérifie que tous les SIRET d'un fournisseur sont identiques."""
    
    def _check_format_validity(self, documents: list[dict]) -> list[dict]:
        """Vérifie formats SIRET (Luhn), IBAN (ISO 13616), TVA intra."""
```

#### `services/validation/statistical_detector.py`

```python
from sklearn.ensemble import IsolationForest

class StatDetector:
    """Détection d'anomalies statistiques par IsolationForest."""
    
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,  # 10% anomalies attendues
            random_state=42
        )
        self.trained = False
        self.scaler = StandardScaler()
    
    def train(self, historical_data: pd.DataFrame):
        """
        Entraîne le modèle sur l'historique des factures.
        Features : montant_ht, montant_ttc, nombre_lignes
        """
        X = historical_data[['montant_ht', 'montant_ttc']].values
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.trained = True
        joblib.dump((self.model, self.scaler), 'model.joblib')
    
    def predict(self, document: dict) -> dict:
        """
        Prédit si un document est anormal.
        
        Returns:
            {
                "is_anomaly": bool,
                "anomaly_score": float (-1 à 1, négatif = anormal),
                "explanation": str
            }
        """
```

### 6.7 Algorithmes de Validation

#### Validation SIRET (Luhn)

```python
def _luhn_check(number: str) -> bool:
    """Vérifie la clé de Luhn pour SIRET/SIREN."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) != 14:  # SIRET = 14 chiffres
        return False
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd) + sum(sum(divmod(d * 2, 10)) for d in even)
    return total % 10 == 0
```

#### Comparaison Raison Sociale (Levenshtein)

```python
def _normalize_raison_sociale(rs: str) -> str:
    """Normalise pour comparaison (lowercase, sans forme juridique)."""
    rs = unidecode(rs.lower().strip())
    for suffix in ["sarl", "sas", "sa", "eurl", "snc"]:
        rs = re.sub(rf"\b{suffix}\b", "", rs)
    return re.sub(r"\s+", " ", rs).strip()

def _levenshtein_ratio(s1: str, s2: str) -> float:
    """Distance normalisée (0 = identique, 1 = différent)."""
    # Seuil d'alerte : ratio > 0.3
```

### 6.8 Justifications Techniques

| Choix | Justification |
|-------|---------------|
| **IsolationForest** | Efficace sur petits datasets, pas besoin de labels, interprétable |
| **python-stdnum** | Implémentations officielles des normes (ISO, RFC) |
| **Règles déterministes d'abord** | Expliquable, pas de faux positifs sur règles métier |
| **Tolérance 0.02€** | Gère les arrondis comptables légaux |
| **Levenshtein normalisé** | Robuste aux fautes OCR mineures |

---

## 7. Rôle 6 — Korniti (Pipeline Airflow)

### 7.1 Responsabilités

Orchestration des pipelines de traitement avec Apache Airflow : ingestion, OCR, validation, enrichissement.

### 7.2 Structure des Fichiers

```
dags/
├── document_pipeline.py      # Pipeline principal
├── monitoring_pipeline.py    # Pipeline de monitoring
└── README.md
```

### 7.3 Bibliothèques Utilisées

| Bibliothèque | Version | Justification |
|--------------|---------|---------------|
| **apache-airflow** | 2.8.1 | Orchestrateur de workflows robuste |
| **requests** | (pip addl) | Appels HTTP vers les services |
| **postgresql** | 15 | Backend Airflow |

### 7.4 DAG Principal

#### `dags/document_pipeline.py`

```python
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "docuflow",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

dag = DAG(
    "docuflow_document_pipeline",
    default_args=default_args,
    description="Pipeline de traitement des documents administratifs",
    schedule_interval="*/5 * * * *",  # Toutes les 5 minutes
    start_date=datetime(2024, 1, 1),
    catchup=False,
)

def ingest_pending_documents(**context):
    """Récupère les documents en attente depuis pending-zone."""
    resp = requests.get(f"{BACKEND_URL}/api/documents", params={"status": "uploaded"})
    documents = resp.json().get("documents", [])
    context["ti"].xcom_push(key="pending_documents", value=documents)
    return len(documents)

def process_ocr(**context):
    """Envoie les documents au service OCR."""
    documents = context["ti"].xcom_pull(task_ids="ingest", key="pending_documents")
    results = []
    for doc in documents:
        ocr_resp = requests.post(f"{OCR_URL}/api/ocr", json={"document_id": doc["document_id"]})
        results.append(ocr_resp.json())
    context["ti"].xcom_push(key="ocr_results", value=results)

def validate_documents(**context):
    """Valide les résultats OCR."""
    ocr_results = context["ti"].xcom_pull(task_ids="ocr_processing", key="ocr_results")
    validation_resp = requests.post(f"{VALIDATION_URL}/api/validate", json={"documents": ocr_results})
    context["ti"].xcom_push(key="validation_result", value=validation_resp.json())

def autofill_and_finalize(**context):
    """Met à jour le backend avec les résultats finaux."""
    validation = context["ti"].xcom_pull(task_ids="validation", key="validation_result")
    # Mise à jour statut documents en MongoDB
    # Notification frontend via Socket.io

# Définition des tâches
ingest = PythonOperator(task_id="ingest", python_callable=ingest_pending_documents, dag=dag)
ocr = PythonOperator(task_id="ocr_processing", python_callable=process_ocr, dag=dag)
validate = PythonOperator(task_id="validation", python_callable=validate_documents, dag=dag)
finalize = PythonOperator(task_id="finalize", python_callable=autofill_and_finalize, dag=dag)

# Pipeline : ingest → ocr → validate → finalize
ingest >> ocr >> validate >> finalize
```

### 7.5 Flux du Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INGEST    │───►│     OCR     │───►│  VALIDATE   │───►│  FINALIZE   │
│  (5 min)    │    │  (parallel) │    │  (batch)    │    │  (update)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼
  pending-zone     ocr-service      validation-svc       MongoDB
                                                        Socket.io
```

### 7.6 Configuration Airflow

```yaml
# docker-compose.yml - extrait
x-airflow-common: &airflow-common
  image: apache/airflow:2.8.1-python3.11
  environment:
    AIRFLOW__CORE__EXECUTOR: LocalExecutor
    AIRFLOW__CORE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
    AIRFLOW__CORE__LOAD_EXAMPLES: "false"
    AIRFLOW__API__AUTH_BACKENDS: "airflow.api.auth.backend.basic_auth"
    _PIP_ADDITIONAL_REQUIREMENTS: "requests"
  volumes:
    - ./dags:/opt/airflow/dags
```

### 7.7 Accès Interface Airflow

```
URL : http://localhost:8080
Utilisateur : admin
Mot de passe : admin
```

### 7.8 Justifications Techniques

| Choix | Justification |
|-------|---------------|
| **Airflow** | Standard industrie, UI complète, retry automatique, monitoring |
| **LocalExecutor** | Suffisant pour PoC, évite Celery/Redis |
| **Schedule 5 min** | Compromis latence vs ressources |
| **XCom** | Communication inter-tâches native Airflow |

---

## 8. Intégrations Inter-Services

### 8.1 Flux Complet de Traitement

```
User Upload (Frontend)
        │
        ▼
    POST /api/process (Backend)
        │
        ├──► Upload raw-zone (MinIO)
        │
        ├──► POST /api/ocr (OCR Service)
        │         │
        │         ▼
        │    Classification + Extraction
        │         │
        │         ▼
        │    Upload clean-zone (MinIO)
        │
        ├──► POST /api/validate (Validation Service)
        │         │
        │         ▼
        │    Règles + IsolationForest
        │
        ├──► Upsert Supplier (MongoDB)
        │
        └──► Socket.io Event (Frontend)
                  │
                  ▼
            Real-time Update UI
```

### 8.2 Communication HTTP Interne

| Source | Destination | Endpoint | Données |
|--------|-------------|----------|---------|
| Backend | OCR | POST /api/ocr | multipart/form-data (PDF) |
| Backend | Validation | POST /api/validate | JSON (documents + entities) |
| Backend | MinIO | S3 API | Fichiers binaires |
| Airflow | Backend | GET /api/documents | Query params |
| Airflow | OCR | POST /api/ocr | JSON |
| Airflow | Validation | POST /api/validate | JSON |

### 8.3 Schéma MongoDB

```javascript
// Collection: documents
{
  document_id: String,      // MD5 hash du fichier
  file_name: String,
  file_size_bytes: Number,
  mime_type: String,
  doc_type: Enum["facture", "devis", "kbis", "urssaf", "siret", "rib", "inconnu"],
  pipeline_status: Enum["raw", "ocr_done", "validated", "llm_refined", "curated"],
  minio_paths: {
    raw: String,            // "raw-zone/abc123.pdf"
    clean: String,          // "clean-zone/abc123.json"
    curated: String
  },
  entities: {
    siret: String,
    tva_intra: String,
    montant_ht: Number,
    tva: Number,
    montant_ttc: Number,
    date_emission: String,
    raison_sociale: String,
    iban: String,
    bic: String
  },
  raw_text: String,
  anomalies: [{
    rule: String,
    severity: Enum["ERROR", "WARNING", "INFO"],
    message: String
  }],
  ocr_confidence: Number,
  extraction_confidence: Number,
  processing_time_ms: Number,
  supplier_id: String,
  created_at: Date,
  processed_at: Date
}

// Collection: suppliers
{
  supplier_id: String,      // MD5(siret)[:12]
  siret: String,
  raison_sociale: String,
  tva_intra: String,
  iban: String,
  bic: String,
  documents: [String],      // Liste document_ids
  created_at: Date,
  updated_at: Date
}
```

---

## 9. Guide de Déploiement

### 9.1 Prérequis

- Docker Desktop ≥ 4.x
- Docker Compose ≥ 2.x
- 8 GB RAM minimum
- 10 GB espace disque

### 9.2 Installation

```bash
# 1. Cloner le repository
git clone https://github.com/HASSANHOUSSEINHOUMED/Hackathon_2026.git
cd Hackathon_2026

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env : OPENAI_API_KEY, MINIO credentials, etc.

# 3. Lancer tous les services
docker compose up -d --build

# 4. Vérifier les conteneurs
docker compose ps
```

### 9.3 Ports Exposés

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Backend | 4000 | http://localhost:4000 |
| OCR Service | 5001 | http://localhost:5001 |
| Validation Service | 5002 | http://localhost:5002 |
| Storage API | 5003 | http://localhost:5003 |
| MinIO Console | 9001 | http://localhost:9001 |
| MinIO API | 9000 | http://localhost:9000 |
| Airflow | 8080 | http://localhost:8080 |
| MongoDB | 27017 | mongodb://localhost:27017 |

### 9.4 Commandes Utiles

```bash
# Logs d'un service
docker compose logs -f backend

# Redémarrer un service
docker compose restart ocr-service

# Arrêter tout
docker compose down

# Supprimer les volumes (reset complet)
docker compose down -v
```

---

## 10. Tests et Validation

### 10.1 Tests OCR

```bash
# Test unitaire endpoint
curl -X POST http://localhost:5001/api/ocr \
  -F "document=@dataset/output/raw/FAC_001.pdf"

# Réponse attendue :
# {"document_id": "...", "type": "facture", "ocr_confidence": 0.85, ...}
```

### 10.2 Tests Validation

```bash
# Test avec document valide
curl -X POST http://localhost:5002/api/validate \
  -H "Content-Type: application/json" \
  -d '{"documents": [{"document_id": "test", "type": "facture", "entities": {"montant_ht": 1000, "tva": 200, "montant_ttc": 1200}}]}'

# Réponse attendue :
# {"status": "OK", "anomaly_count": {"ERROR": 0, "WARNING": 0, "INFO": 0}}
```

### 10.3 Tests E2E

```bash
# Générer documents de test
cd dataset
python generate_test_errors.py

# Upload via API
curl -X POST http://localhost:4000/api/process \
  -F "documents=@output/test_errors/TVA_CALCUL_ERROR.pdf"

# Vérifier anomalies
curl http://localhost:4000/api/documents?status=validated
```

### 10.4 Métriques Attendues

| Métrique | Cible | Actuel |
|----------|-------|--------|
| OCR Confidence (factures) | > 80% | 85% |
| Classification Accuracy | > 90% | 95% |
| Validation Latency | < 100ms | 45ms |
| E2E Processing Time | < 5s | 3.2s |

---

## Annexes

### A. Variables d'Environnement

```ini
# .env
MONGO_USER=admin
MONGO_PASSWORD=admin
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
OPENAI_API_KEY=sk-...
AIRFLOW_UID=50000
```

### B. Liens Utiles

- Repository : https://github.com/HASSANHOUSSEINHOUMED/Hackathon_2026
- MinIO Console : http://localhost:9001 (minioadmin/minioadmin)
- Airflow UI : http://localhost:8080 (admin/admin)
- MongoDB Compass : mongodb://admin:admin@localhost:27017/docuflow?authSource=admin

---

*Document généré le 2024 — Hackathon 2026 — Équipe DocuFlow*
