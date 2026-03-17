# CLAUDE.md — Hackathon 2026 · Rôle 2 : Responsable OCR & Extraction

---

## CONTEXTE DU PROJET

**Nom :** Validation automatique de documents administratifs  
**Objectif global :** Automatiser la réception, la lecture et la vérification de documents
fournisseurs (factures, devis, attestations URSSAF/SIRET, Kbis, RIB) via un pipeline IA complet.

**Architecture en 6 rôles :**

| Rôle | Responsabilité | Port |
|------|---------------|------|
| Rôle 1 | Génération du dataset de test (PDFs + images + ground truth JSON) | — |
| **Rôle 2 (MOI)** | **OCR & Extraction → JSON structuré** | **5001** |
| Rôle 3 | Front-end React + API Node.js (MERN) | 3000 / 4000 |
| Rôle 4 | Data Lake MinIO + MongoDB | 9000 / 27017 |
| Rôle 5 | Détection d'anomalies inter-documents | 5002 |
| Rôle 6 | Orchestration Airflow + Docker global | 8080 |

---

## MA SITUATION (Rôle 2)

Je travaille **en isolation** sur `services/ocr/`.  
Je n'ai pas accès au code des autres rôles, mais les **interfaces sont standardisées**.

### Ce que je reçois

Un fichier (PDF ou image JPG/PNG) envoyé en `multipart/form-data` via :
```
POST http://localhost:5001/api/ocr
field: "document"
```

### Ce que je produis

Un JSON structuré retourné en réponse HTTP et compatible avec les rôles 4 et 5 :

```json
{
  "document_id": "a1b2c3d4",
  "type": "facture",
  "type_confidence": 0.92,
  "ocr_engine_used": "tesseract",
  "ocr_confidence": 0.87,
  "raw_text": "...",
  "entities": {
    "siret": "12345678901234",
    "tva_intra": "FR12345678901",
    "montant_ht": 1250.00,
    "tva": 250.00,
    "montant_ttc": 1500.00,
    "date_emission": "10/03/2025",
    "date_expiration": null,
    "raison_sociale": "Dupont & Fils SAS",
    "iban": "FR7630006000011234567890189",
    "bic": "BNPAFRPP"
  },
  "extraction_confidence": 0.83,
  "processing_time_ms": 1240
}
```

### Types de documents reconnus

`facture` | `devis` | `kbis` | `urssaf` | `siret` | `rib` | `inconnu`

---

## STRUCTURE DES FICHIERS À CRÉER

```
services/ocr/
├── requirements.txt
├── Dockerfile
├── app.py              ← Flask, port 5001, routes /api/ocr /api/ocr/batch /api/health
├── preprocess.py       ← class ImagePreprocessor
├── ocr_engine.py       ← class OCREngine (Tesseract + EasyOCR hybride)
├── extractor.py        ← class EntityExtractor (regex + spaCy)
├── classifier.py       ← class DocumentClassifier (mots-clés pondérés)
└── tests/
    └── test_extractor.py
```

---

## PHASES DE DÉVELOPPEMENT

### PHASE 1 — Setup & Infrastructure
**Fichiers :** `requirements.txt`, `Dockerfile`  
**Objectif :** Environnement fonctionnel avec Tesseract, EasyOCR, spaCy installés.

**requirements.txt à inclure :**
```
flask, pytesseract, easyocr, opencv-python-headless, pillow,
numpy, spacy, pdf2image, PyMuPDF, python-magic, editdistance, gunicorn
```

**Dockerfile :**
- Base : `python:3.11-slim`
- Installer : `tesseract-ocr tesseract-ocr-fra libgl1 poppler-utils`
- `RUN python -m spacy download fr_core_news_md`
- CMD : `gunicorn -w 2 -b 0.0.0.0:5001 app:app`

**Validation de la phase :**
```bash
docker build -t ocr-service .
docker run -p 5001:5001 ocr-service
curl http://localhost:5001/api/health
# Attendu : {"status": "ok", "tesseract_version": "...", "models_loaded": true}
```

---

### PHASE 2 — Prétraitement image (`preprocess.py`)
**Classe :** `ImagePreprocessor`

**Méthode `preprocess(image_path: str) -> np.ndarray` — pipeline en 8 étapes :**
1. Charger l'image (OpenCV)
2. Convertir en niveaux de gris
3. Débruitage : `cv2.fastNlMeansDenoising(h=10)`
4. Correction luminosité : CLAHE (`cv2.createCLAHE`)
5. Deskew : détecter angle via transformée de Hough probabiliste → rotation corrective si `|angle| > 0.5°`
6. Binarisation adaptative : `cv2.adaptiveThreshold` avec `ADAPTIVE_THRESH_GAUSSIAN_C`
7. Rogner les bordures noires (5px chaque côté)
8. Upscale ×2 si résolution < 200 DPI

**Méthode `pdf_to_images(pdf_path: str) -> list[np.ndarray]` :**
- Utiliser `pdf2image.convert_from_path()` avec `dpi=300`
- Retourner une liste d'images (une par page)

**Validation de la phase :**
```bash
python -c "from preprocess import ImagePreprocessor; p = ImagePreprocessor(); img = p.preprocess('test.jpg'); print(img.shape)"
```

---

### PHASE 3 — Moteur OCR (`ocr_engine.py`)
**Classe :** `OCREngine`

**`__init__` :**
- Tesseract config : `'--oem 3 --psm 6 -l fra'`
- EasyOCR : `reader(['fr', 'en'], gpu=False)`

**`extract_text_tesseract(image) -> dict` :**
- Retourne `{"text": str, "confidence": float, "boxes": list}`
- Utiliser `pytesseract.image_to_data()` pour calculer la confiance moyenne par mot

**`extract_text_easyocr(image) -> dict` :**
- Filtrer les résultats avec `confidence < 0.4`
- Retourne `{"text": str, "confidence": float, "boxes": list}`

**`extract_text(image) -> dict` — stratégie hybride :**
1. Essayer Tesseract (plus rapide)
2. Si confiance moyenne < 0.6 **OU** texte < 50 chars → fallback EasyOCR
3. Si les deux sont mauvais → retourner le meilleur des deux
4. Logger le moteur utilisé et la confiance

**Validation de la phase :**
```bash
python -c "
from preprocess import ImagePreprocessor
from ocr_engine import OCREngine
p = ImagePreprocessor()
e = OCREngine()
img = p.preprocess('test.jpg')
result = e.extract_text(img)
print(result['ocr_engine_used'], result['confidence'])
"
```

---

### PHASE 4 — Extraction d'entités (`extractor.py`)
**Classe :** `EntityExtractor`

> **Important :** toutes les regex doivent gérer les espaces insécables (`\xa0`), les erreurs OCR fréquentes (`0↔O`, `1↔l`), et les formats avec ou sans séparateurs.

**`extract_siret(text) -> str | None` :**
- Pattern : 14 chiffres (espaces tolérés tous les 3)
- Valider via algorithme de Luhn (implémenter `luhn_check`)
- Chercher aussi après : `"SIRET"`, `"N° SIRET"`, `"Siret :"`

**`extract_tva_intra(text) -> str | None` :**
- Pattern : `FR` + 2 chiffres + 9 chiffres (SIREN)

**`extract_montants(text) -> dict` :**
- Retourner `{"ht": float, "tva": float, "ttc": float}`
- Chercher les patterns : `XX XXX,XX €` ou `XX XXX.XX EUR`
- Associer aux labels : `"HT"`, `"TVA"`, `"TTC"`, `"Net à payer"`

**`extract_dates(text) -> dict` :**
- Retourner `{"emission": str, "expiration": str, "validite": str}`
- Formats : `DD/MM/YYYY`, `DD-MM-YYYY`, `DD.MM.YYYY`, `"le XX mois YYYY"`
- Associer aux labels : `"émis le"`, `"valable jusqu'au"`, `"date d'expiration"`

**`extract_iban(text) -> str | None` :**
- Pattern IBAN FR : `FR` + 2 chiffres + 23 chiffres/lettres
- Valider le checksum ISO 13616
- Chercher après : `"IBAN"`, `"RIB"`, `"Domiciliation"`

**`extract_raison_sociale(text) -> str | None` :**
1. Chercher après les mots-clés : `"Société :"`, `"Dénomination :"`
2. Utiliser spaCy NER : entités de type `ORG`
3. Heuristique : lignes en MAJUSCULES de 3 à 50 chars avant le SIRET

**`extract_all(text: str) -> dict` :**
- Appelle toutes les méthodes
- Ajoute `"extraction_confidence"` = ratio champs trouvés / total attendu

**Validation de la phase :**
```bash
python -c "
from extractor import EntityExtractor
e = EntityExtractor()
text = 'SIRET : 123 456 789 01234 IBAN FR76 3000 6000 0112 3456 7890 189 Montant HT : 1 250,00 EUR TVA : 250,00 EUR TTC : 1 500,00 EUR'
print(e.extract_all(text))
"
```

---

### PHASE 5 — Classification (`classifier.py`)
**Classe :** `DocumentClassifier`

**`classify(text: str) -> dict` — approche mots-clés pondérés :**

```python
KEYWORDS = {
  "facture":  [("facture", 3), ("invoice", 3), ("montant ttc", 2), ("net à payer", 2), ("n° facture", 2)],
  "devis":    [("devis", 3), ("quotation", 3), ("offre de prix", 2), ("bon pour accord", 2), ("validité", 1)],
  "kbis":     [("extrait kbis", 4), ("greffe", 2), ("rcs", 2), ("immatriculation", 2), ("tribunal de commerce", 2)],
  "urssaf":   [("urssaf", 4), ("attestation de vigilance", 4), ("cotisations sociales", 2)],
  "siret":    [("avis de situation", 3), ("répertoire sirene", 3), ("insee", 2), ("code ape", 2)],
  "rib":      [("relevé d'identité bancaire", 4), ("rib", 3), ("iban", 2), ("bic", 2)]
}
```

- Score = somme des poids des mots-clés trouvés (texte en minuscule)
- Retourner : `{"type": str, "confidence": float, "scores": dict}`
- Si score max = 0 → type = `"inconnu"`

**Validation de la phase :**
```bash
python -c "
from classifier import DocumentClassifier
c = DocumentClassifier()
print(c.classify('URSSAF attestation de vigilance cotisations sociales'))
# Attendu : {'type': 'urssaf', 'confidence': ..., 'scores': {...}}
"
```

---

### PHASE 6 — API Flask (`app.py`)
**Port :** 5001

**`POST /api/ocr`**
- Body : `multipart/form-data`, champ `"document"` (PDF ou image)
- Traitement :
  1. Sauvegarder temporairement dans `/tmp/`
  2. Si PDF → `pdf_to_images()` (une image par page, traiter toutes)
  3. `preprocess()` sur chaque image
  4. `extract_text()` (moteur hybride)
  5. `classify()` sur le texte brut
  6. `extract_all()` sur le texte brut
  7. Construire et retourner le JSON de sortie standardisé
  8. Nettoyer `/tmp/`
- Timeout suggéré : 30s max par document

**`POST /api/ocr/batch`**
- Body JSON : `{"document_ids": ["id1", "id2"]}` (IDs MinIO, prévu pour Rôle 6)
- Traiter en parallèle avec `ThreadPoolExecutor(max_workers=4)`

**`GET /api/health`**
- Retourner : `{"status": "ok", "tesseract_version": "...", "models_loaded": true}`

**Middleware :** Logger chaque requête avec timestamp, document_id, durée, moteur OCR utilisé.

**Validation de la phase :**
```bash
python app.py
# Dans un autre terminal :
curl -X POST http://localhost:5001/api/ocr \
  -F "document=@/chemin/vers/facture_test.pdf"
curl http://localhost:5001/api/health
```

---

### PHASE 7 — Tests unitaires (`tests/test_extractor.py`)
**Framework :** pytest

**Tests à écrire pour chaque méthode `extract_*` :**
- `test_{champ}_texte_propre()` : cas nominal, champ présent et bien formaté
- `test_{champ}_texte_bruite()` : simulation d'erreurs OCR (`O` au lieu de `0`, espaces parasites)
- `test_{champ}_absent()` : le champ n'est pas dans le texte → retourner `None`

**Tests de classification :**
- `test_classify_facture()`, `test_classify_urssaf()`, etc.
- `test_classify_inconnu()` : texte sans mots-clés reconnus

**Test du CER (Character Error Rate) :**
```python
import editdistance

def compute_cer(predicted: str, ground_truth: str) -> float:
    distance = editdistance.eval(predicted, ground_truth)
    return round(distance / max(len(ground_truth), 1) * 100, 2)

# Objectifs :
# CER < 5% sur documents propres (scénario A du Rôle 1)
# CER < 20% sur documents bruités (scénario D du Rôle 1)
```

**Validation de la phase :**
```bash
cd services/ocr
pytest tests/ -v
```

---

## INTERFACES AVEC LES AUTRES RÔLES

### Avec Rôle 1 (dataset)
- Ses fichiers de test sont dans `dataset/raw/` (PDFs propres) et `dataset/noisy/` (images dégradées)
- Ses ground truth JSON dans `dataset/labels/` servent à calculer le CER
- Format ground truth attendu (pour les tests) :
```json
{
  "document_id": "FAC_001",
  "expected_fields": {
    "siret": "12345678901234",
    "montant_ht": 1250.00,
    "tva": 250.00,
    "ttc": 1500.00,
    "date_emission": "10/03/2025"
  }
}
```

### Avec Rôle 4 (Data Lake)
- Le Rôle 4 expose `POST /api/storage/upload` pour sauvegarder en MinIO
- Si le Rôle 4 n'est pas disponible en dev, simuler avec un dossier local `output/`
- Mon JSON de sortie est stocké dans `clean-zone/` (texte brut) et `curated-zone/` (données structurées)

### Avec Rôle 5 (Validation)
- Le Rôle 5 consomme directement mon JSON de sortie via le champ `entities`
- Les champs **critiques** pour lui : `siret`, `montant_ht`, `tva`, `montant_ttc`, `date_expiration`, `raison_sociale`, `iban`
- S'assurer que ces champs sont toujours présents dans le JSON (valeur `null` si non trouvé)

### Avec Rôle 6 (Airflow / Pipeline)
- Le DAG Airflow appelle `POST /api/ocr` avec le contenu du fichier depuis MinIO
- Il appelle aussi `POST /api/ocr/batch` avec une liste de document_ids
- Mon service doit répondre dans le port **5001** sans exception

---

## CONVENTIONS DE CODE

- Python 3.11+, PEP8, type hints sur toutes les fonctions publiques
- Logs en JSON structuré : `{"timestamp": "...", "service": "ocr-service", "level": "INFO", "message": "...", "document_id": "...", "duration_ms": 0}`
- Variables sensibles dans `.env` (ex: `MINIO_ENDPOINT`, `MONGO_URI`)
- Commentaires en français dans le code métier
- Jamais de `# TODO` laissé vide dans le code livré

---

## CHECKLIST FINALE (avant de considérer le rôle terminé)

- [ ] `docker build` sans erreur
- [ ] `GET /api/health` retourne `200 OK` avec versions des moteurs
- [ ] `POST /api/ocr` traite un PDF propre → JSON correct avec entités extraites
- [ ] `POST /api/ocr` traite une image dégradée (JPG bruité) → fallback EasyOCR si nécessaire
- [ ] SIRET extrait et validé via Luhn
- [ ] IBAN extrait et validé via ISO 13616
- [ ] Montants HT / TVA / TTC extraits correctement
- [ ] Dates extraites et associées aux bons labels
- [ ] Classification correcte sur les 6 types de documents
- [ ] `pytest tests/ -v` → tous les tests passent
- [ ] CER documenté : < 5% sur documents propres, < 20% sur documents bruités
