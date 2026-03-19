# Dataset Generator - DocuFlow

Scripts de génération de documents administratifs synthétiques pour les tests et l'évaluation OCR.

## 📦 Technologies

- **Python 3.10+**
- **ReportLab** pour la génération de PDF
- **Faker** pour les données fictives
- **PIL/Pillow** pour le traitement d'images
- **PyMuPDF** pour la conversion PDF→image

## 🏗️ Structure

```
dataset/
├── generators/
│   ├── facture.py          # Générateur de factures
│   ├── devis.py            # Générateur de devis
│   ├── attestation_urssaf.py
│   ├── attestation_siret.py
│   ├── kbis.py
│   └── rib.py
├── company_factory.py      # Générateur d'entreprises fictives
├── config.py               # Configuration globale
├── degrade.py              # Dégradation réaliste (bruit, scan)
├── generate.py             # Script principal
├── generate_test_errors.py # Génération de documents avec erreurs
├── generate_demo_dataset.py # Génération dataset démo (40 docs, vrais SIRET)
├── generate_test_real_companies.py # Documents avec entreprises réelles
├── evaluate_ocr.py         # Évaluation de la qualité OCR
├── requirements.txt
└── output/                 # Dossier de sortie (ignoré par git)
```

## 🚀 Utilisation

### Générer un dataset complet

```bash
cd dataset
pip install -r requirements.txt

# 15 documents par type, tous les scénarios
python generate.py --n 15 --output ./output --scenarios all
```

### Générer des documents avec erreurs (tests)

```bash
python generate_test_errors.py --output ./output/test_errors
```

Ce script génère 12 documents ciblant chaque règle de validation :
- `FAC-ERR-TVA-001.pdf` → TVA_CALCUL_ERROR
- `FAC-ERR-TTC-001.pdf` → TTC_CALCUL_ERROR
- `URSSAF-ERR-EXP-001.pdf` → ATTESTATION_EXPIREE
- etc.

### Générer le dataset de démonstration

```bash
python generate_demo_dataset.py
```

Ce script génère **40 documents** répartis en 3 dossiers pour la démonstration :

| Dossier | Documents | Description |
|---------|-----------|-------------|
| `same_supplier/` | 7 | Un seul fournisseur (CARREFOUR), pas de MISMATCH |
| `multi_supplier/` | 21 | 7 fournisseurs, erreurs individuelles |
| `mismatch_test/` | 12 | Paires avec incohérences SIRET/IBAN/RS |

**Entreprises réelles utilisées :**
- CARREFOUR, TOTAL ENERGIES, ORANGE, SNCF, AIR FRANCE
- RENAULT, DANONE, BOUYGUES, ENGIE, SOCIETE GENERALE

### Générer avec entreprises réelles

```bash
python generate_test_real_companies.py
```

Génère des documents avec de vrais SIREN/SIRET d'entreprises françaises.

### Évaluer la qualité OCR

```bash
# D'abord, lancer le batch OCR
python run-ocr-batch.py

# Puis évaluer
python evaluate_ocr.py --ocr-dir ./output/ocr_results --labels-dir ./output/labels
```

## 📝 Types de documents

| Type | Préfixe | Champs générés |
|------|---------|----------------|
| Facture | FAC | siret, tva, iban, montants, prestations |
| Devis | DEV | siret, montants, validité |
| URSSAF | URSSAF | siret, dates émission/expiration |
| SIRET | SIRET | siret, siren, adresse, NAF |
| Kbis | KBIS | raison sociale, capital, dirigeant |
| RIB | RIB | iban, bic, titulaire |

## 🎭 Scénarios de génération

| Scénario | Probabilité | Description |
|----------|-------------|-------------|
| `coherent` | 30% | Document correct et cohérent |
| `mismatch` | 30% | Incohérences volontaires (SIRET, montants) |
| `expired` | 20% | Dates expirées |
| `noisy` | 20% | Dégradations visuelles (scan, bruit) |

## 🔧 Configuration (config.py)

```python
N_DOCS = 15              # Documents par type
SCENARIOS = {
    "coherent": 0.30,
    "mismatch": 0.30,
    "expired": 0.20,
    "noisy": 0.20,
}
TVA_RATES = [0.055, 0.10, 0.20]
```

## 🏭 Company Factory

Génère des entreprises fictives avec des identifiants **valides** :

- **SIREN/SIRET** : Algorithme de Luhn respecté
- **TVA intracommunautaire** : Formule officielle FR + clé
- **IBAN** : Checksum ISO 13616 correct
- **Adresses** : Via Faker(fr_FR)

```python
from company_factory import CompanyFactory

factory = CompanyFactory()
company = factory.generate()

print(company.siret)       # 12345678901234 (valide)
print(company.iban)        # FR7612345... (valide)
print(company.tva_intra)   # FR32123456789 (valide)
```

## 📊 Format de sortie

```
output/
├── raw/                    # PDFs bruts
│   ├── FAC_001.pdf
│   ├── DEV_001.pdf
│   └── ...
├── noisy/                  # Images dégradées (scénario noisy)
├── labels/                 # Ground truth JSON
│   ├── FAC_001.json
│   └── ...
├── ocr_results/            # Résultats OCR (après batch)
├── evaluation/             # Métriques d'évaluation
│   ├── metrics.json
│   └── graphs/
└── dataset_manifest.json   # Inventaire complet
```
