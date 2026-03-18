# Service OCR - DocuFlow

Microservice Python pour l'extraction de texte et d'entités depuis des documents administratifs.

## 📦 Technologies

- **Python 3.11**
- **Flask** comme framework web
- **Gunicorn** comme serveur WSGI
- **Tesseract OCR** pour la reconnaissance de texte
- **EasyOCR** comme OCR secondaire
- **OpenCV** pour le prétraitement d'images
- **spaCy** pour le NLP (optionnel)
- **pdf2image** pour la conversion PDF→image

## 🏗️ Structure

```
services/ocr/
├── app.py              # API Flask
├── ocr_engine.py       # Moteur OCR (Tesseract + EasyOCR)
├── classifier.py       # Classification du type de document
├── extractor.py        # Extraction des entités (regex + patterns)
├── preprocess.py       # Prétraitement des images
├── tests/
│   ├── test_ocr.py
│   └── test_entities.py
├── Dockerfile
└── requirements.txt
```

## 🔌 API

### POST `/api/ocr`

Traite un document (PDF ou image) et extrait les entités.

**Request:**
```
Content-Type: multipart/form-data
Body: document=<fichier>
```

**Response:**
```json
{
  "document_id": "abc123",
  "type": "facture",
  "type_confidence": 0.85,
  "ocr_confidence": 0.78,
  "entities": {
    "siret": "12345678901234",
    "montant_ht": 1000.00,
    "montant_ttc": 1200.00,
    "tva": 200.00,
    "raison_sociale": "Entreprise SARL",
    "iban": "FR7612345678901234567890123",
    "date_emission": "15/03/2026"
  },
  "raw_text": "FACTURE N° FAC-2026-001...",
  "extraction_confidence": 0.72,
  "processing_time_ms": 2500
}
```

### GET `/api/health`

Health check du service.

## 🎯 Types de documents détectés

| Type | Mots-clés |
|------|-----------|
| `facture` | FACTURE, INVOICE, TOTAL TTC |
| `devis` | DEVIS, QUOTE, PROPOSITION |
| `kbis` | KBIS, EXTRAIT, GREFFE, TRIBUNAL |
| `urssaf` | URSSAF, ATTESTATION, VIGILANCE |
| `siret` | ATTESTATION SIRET, INSEE |
| `rib` | RIB, IBAN, BIC, IDENTITÉ BANCAIRE |

## 🔧 Entités extraites

| Entité | Format | Validation |
|--------|--------|------------|
| `siret` | 14 chiffres | Algorithme de Luhn |
| `siren` | 9 chiffres | Dérivé du SIRET |
| `tva_intra` | FR + 2 + 9 chiffres | Regex |
| `iban` | FR76 + 23 car. | Checksum ISO 13616 |
| `bic` | 8 ou 11 car. | Regex |
| `montant_ht` | Nombre | Parsing décimal |
| `montant_ttc` | Nombre | Parsing décimal |
| `tva` | Nombre | Parsing décimal |
| `date_*` | JJ/MM/AAAA | Regex multi-format |

## ⚙️ Configuration

```env
TESSERACT_LANG=fra+eng
OCR_CONFIDENCE_THRESHOLD=0.5
MAX_IMAGE_SIZE=4096
```

## 🚀 Développement local

```bash
# Avec Docker (recommandé)
docker compose up -d ocr-service

# Sans Docker
pip install -r requirements.txt
python -m pytest tests/ -v
gunicorn -w 2 -b 0.0.0.0:5001 app:app
```

## 🧪 Tests

```bash
cd services/ocr
pytest tests/ -v
pytest tests/ --benchmark-only  # Tests de performance
```

## 📊 Pipeline de traitement

```
┌─────────┐    ┌─────────────┐    ┌────────────┐    ┌───────────┐
│  PDF/   │───▶│ Preprocess  │───▶│    OCR     │───▶│  Extract  │
│  Image  │    │ (OpenCV)    │    │ (Tesseract)│    │ (Regex)   │
└─────────┘    └─────────────┘    └────────────┘    └───────────┘
                     │                   │                │
                     ▼                   ▼                ▼
               Binarisation         Texte brut        Entités
               Débruitage           Confiance         structurées
               Redressement
```
