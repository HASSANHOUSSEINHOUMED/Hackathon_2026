# Service Validation - DocuFlow

Microservice Python pour la validation des documents et la détection d'anomalies.

## 📦 Technologies

- **Python 3.11**
- **Flask** comme framework web
- **Gunicorn** comme serveur WSGI
- **scikit-learn** pour la détection d'anomalies (IsolationForest)

## 🏗️ Structure

```
services/validation/
├── app.py                  # API Flask
├── rules_catalog.py        # Définition des 12 règles
├── rules_engine.py         # Moteur d'exécution des règles
├── statistical_detector.py # Détection ML (IsolationForest)
├── tests/
│   ├── test_validation.py
│   └── test_rules.py
├── Dockerfile
└── requirements.txt
```

## 🔌 API

### POST `/api/validate`

Valide un ou plusieurs documents.

**Request:**
```json
{
  "documents": [
    {
      "document_id": "abc123",
      "type": "facture",
      "entities": {
        "siret": "12345678901234",
        "montant_ht": 1000.00,
        "montant_ttc": 1200.00,
        "tva": 200.00
      }
    }
  ]
}
```

**Response:**
```json
{
  "anomalies": [
    {
      "document_id": "abc123",
      "rule_id": "TVA_CALCUL_ERROR",
      "severity": "ERROR",
      "message": "Le montant de TVA (200€) ne correspond pas au calcul attendu (240€ à 20%)"
    }
  ],
  "summary": {
    "total_documents": 1,
    "documents_with_errors": 1,
    "total_anomalies": 1
  }
}
```

### GET `/api/rules`

Liste toutes les règles de validation disponibles.

### GET `/api/health`

Health check du service.

## 📋 Catalogue des règles

| ID | Nom | Sévérité | Documents |
|----|-----|----------|-----------|
| `SIRET_FORMAT_INVALIDE` | Format SIRET invalide | ERROR | Tous |
| `SIRET_MISMATCH` | Incohérence SIRET inter-documents | ERROR | Tous |
| `TVA_CALCUL_ERROR` | Erreur de calcul TVA | ERROR | facture, devis |
| `TTC_CALCUL_ERROR` | Erreur de calcul TTC | ERROR | facture, devis |
| `ATTESTATION_EXPIREE` | Attestation URSSAF expirée | ERROR | urssaf |
| `KBIS_PERIME` | Kbis > 90 jours | WARNING | kbis |
| `DEVIS_EXPIRE` | Devis expiré | WARNING | devis |
| `IBAN_FORMAT_INVALIDE` | Format IBAN invalide | ERROR | facture, rib |
| `IBAN_MISMATCH` | Incohérence IBAN inter-documents | WARNING | facture, rib |
| `TVA_INTRA_INVALIDE` | TVA intracommunautaire invalide | WARNING | facture, kbis |
| `RAISON_SOCIALE_MISMATCH` | Incohérence raison sociale | WARNING | Tous |
| `MONTANT_ANORMAL` | Montant statistiquement anormal (ML) | INFO | facture |

### Règles inter-documents (mode batch)

Les règles `*_MISMATCH` comparent les entités entre tous les documents d'un même lot :
- **SIRET_MISMATCH** : Détecte si les SIRET diffèrent entre documents
- **IBAN_MISMATCH** : Détecte si les IBAN diffèrent entre documents
- **RAISON_SOCIALE_MISMATCH** : Détecte les variations de nom d'entreprise

## 🔧 Validations techniques

### Algorithme de Luhn (SIRET/SIREN)
```python
def luhn_checksum(number: str) -> bool:
    digits = [int(d) for d in number]
    odd_sum = sum(digits[-1::-2])
    even_sum = sum(sum(divmod(d * 2, 10)) for d in digits[-2::-2])
    return (odd_sum + even_sum) % 10 == 0
```

### Checksum IBAN (ISO 13616)
```python
def validate_iban(iban: str) -> bool:
    iban_num = iban[4:] + iban[:4]
    num_str = ''.join(str(int(c, 36)) for c in iban_num)
    return int(num_str) % 97 == 1
```

## 📊 Détection statistique

Le service utilise **IsolationForest** pour détecter les montants anormaux :

```python
from sklearn.ensemble import IsolationForest

# Auto-entraînement avec données synthétiques (500 échantillons log-normal)
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(training_data)  # Distribution réaliste des montants
prediction = model.predict([[new_amount]])  # -1 = anomalie
```

**Caractéristiques :**
- Entraînement automatique au démarrage (500 échantillons synthétiques)
- Distribution log-normale centrée sur 5000€ (réaliste pour factures)
- Score d'anomalie normalisé (0-100)
- Seuil de contamination : 5%

## 🚀 Développement local

```bash
# Avec Docker (recommandé)
docker compose up -d validation-service

# Sans Docker
pip install -r requirements.txt
python -m pytest tests/ -v
gunicorn -w 2 -b 0.0.0.0:5002 app:app
```

## 🧪 Tests

```bash
cd services/validation
pytest tests/ -v
pytest tests/ --benchmark-only
```
