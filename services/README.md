# Services - DocuFlow

Microservices Python pour le traitement des documents.

## 📦 Services disponibles

| Service | Port | Description | Documentation |
|---------|------|-------------|---------------|
| **OCR** | 5001 | Extraction de texte et entités | [README](ocr/README.md) |
| **Validation** | 5002 | Règles métier et détection ML | [README](validation/README.md) |

## 🏗️ Architecture

```
┌──────────────────┐    ┌──────────────────┐
│   OCR Service    │    │ Validation Svc   │
│   Flask/Gunicorn │    │ Flask/Gunicorn   │
│   :5001          │    │ :5002            │
├──────────────────┤    ├──────────────────┤
│ • Tesseract OCR  │    │ • 11 règles      │
│ • EasyOCR        │    │ • IsolationForest│
│ • OpenCV         │    │ • Luhn/IBAN check│
│ • Classification │    │ • Cross-doc      │
└──────────────────┘    └──────────────────┘
```

## 🚀 Démarrage

```bash
# Avec Docker (recommandé)
docker compose up -d ocr-service validation-service

# Vérifier le statut
docker compose ps | grep -E "ocr|validation"
```

## 🔌 Health checks

```bash
curl http://localhost:5001/api/health
curl http://localhost:5002/api/health
```

## 🧪 Tests

```bash
# Tests OCR
docker exec docuflow-ocr pytest tests/ -v

# Tests Validation
docker exec docuflow-validation pytest tests/ -v
```

## 📊 Logs

```bash
docker compose logs -f ocr-service
docker compose logs -f validation-service
```
