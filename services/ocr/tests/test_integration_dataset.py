"""
tests/test_integration_dataset.py — Tests d'intégration OCR ↔ Dataset (Rôle 1)

Vérifie que EntityExtractor et DocumentClassifier produisent des résultats
cohérents avec les ground truth du dataset généré par Rôle 1.

Fonctionnement :
- Extrait le texte des PDFs via PyMuPDF (sans OCR, texte embarqué)
- Exécute les composants du service OCR sur ce texte
- Compare les résultats aux labels dataset/labels/*.json

Prérequis :
- PyMuPDF : pip install PyMuPDF
- Le dossier dataset/ doit exister au même niveau que services/
  (hackathon-administration-docs/dataset/)

Usage :
    cd services/ocr
    pytest tests/test_integration_dataset.py -v
"""

import json
import sys
import os
from pathlib import Path

import pytest

# Chemin vers les composants du service OCR
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extractor import EntityExtractor
from classifier import DocumentClassifier

# dataset/ est 3 niveaux au-dessus de tests/
# tests/ → ocr/ → services/ → hackathon-administration-docs/ → dataset/
DATASET_DIR = Path(__file__).parents[3] / "dataset"
LABELS_DIR = DATASET_DIR / "labels"
RAW_DIR = DATASET_DIR / "raw"

# Skip tout le module si le dataset est absent
if not DATASET_DIR.exists():
    pytest.skip(
        f"Dataset introuvable : {DATASET_DIR} — lancez d'abord generate.py (Rôle 1)",
        allow_module_level=True,
    )

fitz = pytest.importorskip("fitz", reason="PyMuPDF (fitz) requis : pip install PyMuPDF")


# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

def extract_text_pdf(pdf_path: Path) -> str:
    """Extrait le texte embarqué d'un PDF via PyMuPDF (pas d'OCR)."""
    doc = fitz.open(str(pdf_path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text.strip()


def iso_to_fr(date_iso: str) -> str:
    """Convertit YYYY-MM-DD → DD/MM/YYYY (format de sortie de l'extractor)."""
    y, m, d = date_iso.split("-")
    return f"{d}/{m}/{y}"


def load_cases() -> list[tuple]:
    """Charge tous les couples (doc_id, pdf_path, label_path) disponibles."""
    cases = []
    if not LABELS_DIR.exists():
        return cases
    for label_path in sorted(LABELS_DIR.glob("*.json")):
        pdf_path = RAW_DIR / f"{label_path.stem}.pdf"
        if pdf_path.exists():
            cases.append((label_path.stem, pdf_path, label_path))
    return cases


CASES = load_cases()

if not CASES:
    pytest.skip("Aucun PDF trouvé dans dataset/raw/", allow_module_level=True)


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="module")
def extractor():
    return EntityExtractor()


@pytest.fixture(scope="module")
def classifier():
    return DocumentClassifier()


# ------------------------------------------------------------------
# Classification
# ------------------------------------------------------------------

class TestClassifierOnDataset:
    """Vérifie que le classifier produit le bon type pour chaque document."""

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", CASES)
    def test_classifier_type(self, doc_id, pdf_path, label_path, classifier):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        text = extract_text_pdf(pdf_path)
        result = classifier.classify(text)
        expected_type = label["type"]

        assert result["type"] == expected_type, (
            f"{doc_id}: type attendu={expected_type!r}, obtenu={result['type']!r} "
            f"(scores={result['scores']})"
        )


# ------------------------------------------------------------------
# Extraction SIRET
# ------------------------------------------------------------------

class TestExtractorSiretOnDataset:
    """Vérifie que les SIRET des PDFs sont extraits et valident le Luhn."""

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", CASES)
    def test_siret_extrait(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        fields = label["expected_fields"]
        # Le SIRET peut se trouver sous différentes clés selon le type de document
        expected_siret = (
            fields.get("siret")
            or fields.get("siret_emetteur")
            or fields.get("siret_associe")
        )
        if not expected_siret:
            pytest.skip(f"{doc_id}: pas de SIRET attendu dans le label")

        text = extract_text_pdf(pdf_path)
        result = extractor.extract_siret(text)

        assert result is not None, (
            f"{doc_id}: SIRET non extrait (attendu={expected_siret})"
        )
        assert result == expected_siret, (
            f"{doc_id}: SIRET attendu={expected_siret!r}, obtenu={result!r}"
        )


# ------------------------------------------------------------------
# Extraction de dates
# ------------------------------------------------------------------

class TestExtractorDatesOnDataset:
    """Vérifie que les dates ISO des PDFs sont extraites et converties en DD/MM/YYYY."""

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("FACTURE")
    ])
    def test_facture_date_emission(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        expected_iso = label["expected_fields"].get("date_emission")
        if not expected_iso:
            pytest.skip(f"{doc_id}: pas de date_emission dans le label")

        text = extract_text_pdf(pdf_path)
        dates = extractor.extract_dates(text)

        assert dates["emission"] == iso_to_fr(expected_iso), (
            f"{doc_id}: date_emission attendue={iso_to_fr(expected_iso)!r}, "
            f"obtenue={dates['emission']!r}"
        )

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("DEVIS")
    ])
    def test_devis_date_emission(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        expected_iso = label["expected_fields"].get("date_devis")
        if not expected_iso:
            pytest.skip(f"{doc_id}: pas de date_devis dans le label")

        text = extract_text_pdf(pdf_path)
        dates = extractor.extract_dates(text)

        assert dates["emission"] == iso_to_fr(expected_iso), (
            f"{doc_id}: date_devis attendue={iso_to_fr(expected_iso)!r}, "
            f"obtenue={dates['emission']!r}"
        )

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("ATTESTATION_SIRET")
    ])
    def test_siret_date_expiration(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        expected_iso = label["expected_fields"].get("date_expiration")
        if not expected_iso:
            pytest.skip(f"{doc_id}: pas de date_expiration dans le label")

        text = extract_text_pdf(pdf_path)
        dates = extractor.extract_dates(text)

        assert dates["expiration"] == iso_to_fr(expected_iso), (
            f"{doc_id}: date_expiration attendue={iso_to_fr(expected_iso)!r}, "
            f"obtenue={dates['expiration']!r}"
        )

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("ATTESTATION_URSSAF")
    ])
    def test_urssaf_date_fin_validite(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        expected_iso = label["expected_fields"].get("date_fin_validite")
        if not expected_iso:
            pytest.skip(f"{doc_id}: pas de date_fin_validite dans le label")

        text = extract_text_pdf(pdf_path)
        dates = extractor.extract_dates(text)

        assert dates["expiration"] == iso_to_fr(expected_iso), (
            f"{doc_id}: date_fin_validite attendue={iso_to_fr(expected_iso)!r}, "
            f"obtenue={dates['expiration']!r}"
        )


# ------------------------------------------------------------------
# Extraction montants (FACTURE / DEVIS)
# ------------------------------------------------------------------

class TestExtractorMontantsOnDataset:
    """Vérifie que les montants HT/TTC des PDFs sont correctement extraits."""

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("FACTURE")
    ])
    def test_facture_montants(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        fields = label["expected_fields"]
        text = extract_text_pdf(pdf_path)
        montants = extractor.extract_montants(text)

        expected_ht = fields.get("montant_ht")
        expected_ttc = fields.get("ttc")

        if expected_ht is not None:
            assert montants["ht"] is not None, f"{doc_id}: montant_ht non extrait"
            assert abs(montants["ht"] - expected_ht) < 0.02, (
                f"{doc_id}: montant_ht attendu={expected_ht}, obtenu={montants['ht']}"
            )
        if expected_ttc is not None:
            assert montants["ttc"] is not None, f"{doc_id}: montant_ttc non extrait"
            assert abs(montants["ttc"] - expected_ttc) < 0.02, (
                f"{doc_id}: montant_ttc attendu={expected_ttc}, obtenu={montants['ttc']}"
            )

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("DEVIS")
    ])
    def test_devis_montants(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        fields = label["expected_fields"]
        text = extract_text_pdf(pdf_path)
        montants = extractor.extract_montants(text)

        expected_ht = fields.get("total_ht")
        expected_ttc = fields.get("ttc")

        if expected_ht is not None:
            assert montants["ht"] is not None, f"{doc_id}: montant HT non extrait"
            assert abs(montants["ht"] - expected_ht) < 0.02, (
                f"{doc_id}: montant HT attendu={expected_ht}, obtenu={montants['ht']}"
            )
        if expected_ttc is not None:
            assert montants["ttc"] is not None, f"{doc_id}: montant TTC non extrait"
            assert abs(montants["ttc"] - expected_ttc) < 0.02, (
                f"{doc_id}: montant TTC attendu={expected_ttc}, obtenu={montants['ttc']}"
            )


# ------------------------------------------------------------------
# IBAN (RIB)
# ------------------------------------------------------------------

class TestExtractorIbanOnDataset:
    """Vérifie que les IBAN des documents RIB sont extraits et validés."""

    @pytest.mark.parametrize("doc_id,pdf_path,label_path", [
        c for c in CASES if c[0].startswith("RIB")
    ])
    def test_rib_iban(self, doc_id, pdf_path, label_path, extractor):
        with open(label_path, encoding="utf-8") as f:
            label = json.load(f)

        expected_iban = label["expected_fields"].get("iban")
        if not expected_iban:
            pytest.skip(f"{doc_id}: pas d'IBAN dans le label")

        text = extract_text_pdf(pdf_path)
        result = extractor.extract_iban(text)

        assert result is not None, (
            f"{doc_id}: IBAN non extrait (attendu={expected_iban})"
        )
        assert result == expected_iban, (
            f"{doc_id}: IBAN attendu={expected_iban!r}, obtenu={result!r}"
        )
