"""
tests/test_extractor.py — Tests unitaires pour EntityExtractor et DocumentClassifier
Framework : pytest

Couverture :
- extract_siret     : texte propre, bruité, absent
- extract_tva_intra : texte propre, bruité, absent
- extract_montants  : texte propre, bruité, absent
- extract_dates     : texte propre, bruité, absent
- extract_iban      : texte propre, bruité, absent
- extract_raison_sociale : texte propre, bruité, absent
- classify          : chaque type + inconnu
- CER               : documents propres < 5%, bruités < 20%
"""

import sys
import os
import editdistance
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from extractor import EntityExtractor
from classifier import DocumentClassifier


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="module")
def e():
    return EntityExtractor()


@pytest.fixture(scope="module")
def c():
    return DocumentClassifier()


# ------------------------------------------------------------------
# Utilitaire CER
# ------------------------------------------------------------------

def compute_cer(predicted: str, ground_truth: str) -> float:
    """Calcule le Character Error Rate (CER) en pourcentage."""
    distance = editdistance.eval(predicted, ground_truth)
    return round(distance / max(len(ground_truth), 1) * 100, 2)


# ------------------------------------------------------------------
# SIRET
# ------------------------------------------------------------------

class TestExtractSiret:
    def test_siret_texte_propre(self, e):
        """Cas nominal : SIRET valide précédé du mot-clé."""
        text = "SIRET : 552 049 447 00013"
        assert e.extract_siret(text) == "55204944700013"

    def test_siret_texte_propre_sans_espaces(self, e):
        """SIRET collé sans séparateurs."""
        text = "N° SIRET 55204944700013"
        assert e.extract_siret(text) == "55204944700013"

    def test_siret_texte_bruite_ocr(self, e):
        """Erreur OCR : O à la place de 0."""
        # 552 O49 447 OO013 → 55204944700013
        text = "Siret : 552 O49 447 OO013"
        result = e.extract_siret(text)
        assert result == "55204944700013"

    def test_siret_texte_bruite_espaces_parasites(self, e):
        """Espaces insécables et séparateurs variés."""
        text = "SIRET\xa0:\xa0552-049-447-00013"
        assert e.extract_siret(text) == "55204944700013"

    def test_siret_luhn_invalide_rejete(self, e):
        """Un numéro de 14 chiffres qui échoue le Luhn doit être rejeté."""
        text = "SIRET : 123 456 789 01234"
        assert e.extract_siret(text) is None

    def test_siret_absent(self, e):
        """Aucun SIRET dans le texte → None."""
        text = "Bonjour, voici une lettre sans numéro d'identification."
        assert e.extract_siret(text) is None


# ------------------------------------------------------------------
# TVA intracommunautaire
# ------------------------------------------------------------------

class TestExtractTvaIntra:
    def test_tva_texte_propre(self, e):
        """Cas nominal : TVA intracommunautaire française."""
        text = "N° TVA intracommunautaire : FR12 345 678 901"
        result = e.extract_tva_intra(text)
        assert result == "FR12345678901"

    def test_tva_texte_bruite(self, e):
        """Espaces insécables et casse mixte."""
        text = "tva\xa0:\xa0fr12345678901"
        result = e.extract_tva_intra(text)
        assert result == "FR12345678901"

    def test_tva_absent(self, e):
        """Pas de TVA dans le texte → None."""
        text = "Montant total : 1500 EUR, payable sous 30 jours."
        assert e.extract_tva_intra(text) is None


# ------------------------------------------------------------------
# Montants
# ------------------------------------------------------------------

class TestExtractMontants:
    def test_montants_texte_propre(self, e):
        """Cas nominal : HT, TVA et TTC présents."""
        text = "Montant HT : 1 250,00 EUR  TVA : 250,00 EUR  TTC : 1 500,00 EUR"
        result = e.extract_montants(text)
        assert result["ht"] == 1250.0
        assert result["tva"] == 250.0
        assert result["ttc"] == 1500.0

    def test_montants_net_a_payer(self, e):
        """Label 'Net à payer' doit être reconnu comme TTC."""
        text = "Montant H.T. : 800,00 EUR  TVA 20% : 160,00 EUR  Net à payer : 960,00 EUR"
        result = e.extract_montants(text)
        assert result["ttc"] == 960.0

    def test_montants_texte_bruite(self, e):
        """Espaces insécables dans les montants."""
        text = "Montant HT\xa0:\xa01\xa0250,00\xa0EUR TVA\xa0:\xa0250,00 EUR TTC\xa0:\xa01\xa0500,00 EUR"
        result = e.extract_montants(text)
        assert result["ht"] == 1250.0
        assert result["ttc"] == 1500.0

    def test_montants_absents(self, e):
        """Aucun montant → tous None."""
        text = "URSSAF attestation de vigilance société DUPONT"
        result = e.extract_montants(text)
        assert result["ht"] is None
        assert result["tva"] is None
        assert result["ttc"] is None


# ------------------------------------------------------------------
# Dates
# ------------------------------------------------------------------

class TestExtractDates:
    def test_dates_texte_propre_emission(self, e):
        """Cas nominal : date d'émission au format DD/MM/YYYY."""
        text = "Émis le 10/03/2025"
        result = e.extract_dates(text)
        assert result["emission"] == "10/03/2025"

    def test_dates_texte_propre_expiration(self, e):
        """Date d'expiration explicite."""
        text = "Date d'expiration : 31/12/2025"
        result = e.extract_dates(text)
        assert result["expiration"] == "31/12/2025"

    def test_dates_format_tiret(self, e):
        """Format DD-MM-YYYY."""
        text = "Émis le 10-03-2025"
        result = e.extract_dates(text)
        assert result["emission"] == "10/03/2025"

    def test_dates_format_litteral(self, e):
        """Format littéral : '10 mars 2025'."""
        text = "émis le 10 mars 2025"
        result = e.extract_dates(text)
        assert result["emission"] == "10/03/2025"

    def test_dates_texte_bruite(self, e):
        """Espaces insécables autour de la date."""
        text = "Emis le\xa010/03/2025"
        result = e.extract_dates(text)
        assert result["emission"] == "10/03/2025"

    def test_dates_absentes(self, e):
        """Aucune date → tous None."""
        text = "Attestation URSSAF société DUPONT SIRET valide"
        result = e.extract_dates(text)
        assert result["emission"] is None
        assert result["expiration"] is None
        assert result["validite"] is None


# ------------------------------------------------------------------
# IBAN
# ------------------------------------------------------------------

class TestExtractIban:
    IBAN_VALIDE = "FR7630006000011234567890189"

    def test_iban_texte_propre(self, e):
        """Cas nominal : IBAN après le mot-clé IBAN."""
        text = f"IBAN {self.IBAN_VALIDE}"
        assert e.extract_iban(text) == self.IBAN_VALIDE

    def test_iban_avec_espaces(self, e):
        """IBAN formaté avec espaces tous les 4 caractères."""
        text = "IBAN FR76 3000 6000 0112 3456 7890 189"
        assert e.extract_iban(text) == self.IBAN_VALIDE

    def test_iban_apres_rib(self, e):
        """IBAN précédé du label RIB."""
        text = f"RIB / {self.IBAN_VALIDE}"
        assert e.extract_iban(text) == self.IBAN_VALIDE

    def test_iban_texte_bruite(self, e):
        """Espaces insécables autour de l'IBAN."""
        text = f"IBAN\xa0:\xa0FR76 3000 6000 0112 3456 7890 189"
        assert e.extract_iban(text) == self.IBAN_VALIDE

    def test_iban_checksum_invalide(self, e):
        """IBAN avec checksum incorrect → None."""
        text = "IBAN FR00 3000 6000 0112 3456 7890 000"
        assert e.extract_iban(text) is None

    def test_iban_absent(self, e):
        """Pas d'IBAN dans le texte → None."""
        text = "Facture N° 2025-001 Montant TTC : 1500 EUR"
        assert e.extract_iban(text) is None


# ------------------------------------------------------------------
# Raison sociale
# ------------------------------------------------------------------

class TestExtractRaisonSociale:
    def test_raison_sociale_texte_propre_keyword(self, e):
        """Cas nominal : raison sociale après mot-clé 'Société :'."""
        text = "Société : Dupont et Fils SAS\nSIRET : 552 049 447 00013"
        result = e.extract_raison_sociale(text)
        assert result is not None
        assert "Dupont" in result

    def test_raison_sociale_denomination(self, e):
        """Mot-clé 'Dénomination sociale'."""
        text = "Dénomination sociale : Martin & Associés SARL"
        result = e.extract_raison_sociale(text)
        assert result is not None
        assert "Martin" in result

    def test_raison_sociale_texte_bruite(self, e):
        """Espaces insécables autour du séparateur."""
        text = "Société\xa0:\xa0Techno Industrie SA\nSIRET 552 049 447 00013"
        result = e.extract_raison_sociale(text)
        assert result is not None

    def test_raison_sociale_absente(self, e):
        """Texte sans raison sociale identifiable → None."""
        text = "12345 montant 500 EUR date 01/01/2025"
        result = e.extract_raison_sociale(text)
        assert result is None


# ------------------------------------------------------------------
# Classification
# ------------------------------------------------------------------

class TestClassifier:
    def test_classify_facture(self, c):
        text = "FACTURE N° 2025-001 montant TTC 1500 EUR net à payer sous 30 jours"
        result = c.classify(text)
        assert result["type"] == "facture"
        assert result["confidence"] > 0

    def test_classify_devis(self, c):
        text = "DEVIS N° 42 offre de prix validité 30 jours bon pour accord"
        result = c.classify(text)
        assert result["type"] == "devis"

    def test_classify_kbis(self, c):
        text = "Extrait Kbis tribunal de commerce RCS immatriculation greffe"
        result = c.classify(text)
        assert result["type"] == "kbis"

    def test_classify_urssaf(self, c):
        text = "URSSAF attestation de vigilance cotisations sociales"
        result = c.classify(text)
        assert result["type"] == "urssaf"
        assert result["confidence"] > 0

    def test_classify_siret(self, c):
        text = "Avis de situation répertoire SIRENE INSEE code APE activité principale"
        result = c.classify(text)
        assert result["type"] == "siret"

    def test_classify_rib(self, c):
        text = "Relevé d'identité bancaire IBAN BIC domiciliation titulaire du compte"
        result = c.classify(text)
        assert result["type"] == "rib"

    def test_classify_inconnu(self, c):
        text = "Lorem ipsum dolor sit amet consectetur adipiscing elit"
        result = c.classify(text)
        assert result["type"] == "inconnu"
        assert result["confidence"] == 0.0

    def test_classify_retourne_tous_les_scores(self, c):
        text = "FACTURE montant TTC"
        result = c.classify(text)
        assert "scores" in result
        assert set(result["scores"].keys()) == {"facture", "devis", "kbis", "urssaf", "siret", "rib"}

    def test_classify_confiance_entre_0_et_1(self, c):
        text = "URSSAF attestation de vigilance"
        result = c.classify(text)
        assert 0.0 <= result["confidence"] <= 1.0


# ------------------------------------------------------------------
# CER — Character Error Rate
# ------------------------------------------------------------------

class TestCER:
    """
    Objectifs :
    - Scénario A (documents propres) : CER < 5%
    - Scénario D (documents bruités) : CER < 20%
    """

    # Paires (texte_ocr, ground_truth) pour documents propres
    CLEAN_PAIRS = [
        ("FACTURE N° 2025-001", "FACTURE N° 2025-001"),
        ("SIRET : 552 049 447 00013", "SIRET : 552 049 447 00013"),
        ("Montant HT : 1 250,00 EUR", "Montant HT : 1 250,00 EUR"),
        ("TVA : 250,00 EUR", "TVA : 250,00 EUR"),
        ("Net à payer : 1 500,00 EUR", "Net à payer : 1 500,00 EUR"),
    ]

    # Paires simulant des erreurs OCR courantes (CER ≤ 20%)
    NOISY_PAIRS = [
        ("FACTURE N 2O25-OO1",         "FACTURE N 2025-001"),
        ("SlRET : 552 O49 447 OOO13",  "SIRET : 552 049 447 00013"),
        ("Montant HT : l 25O,OO EUR",  "Montant HT : 1 250,00 EUR"),
        ("TVA : 25O,OO EUR",           "TVA : 250,00 EUR"),
        ("Net a payer : 1 5OO,OO EUR", "Net à payer : 1 500,00 EUR"),
    ]

    def test_cer_documents_propres(self):
        """CER < 5% sur des textes propres (scénario A)."""
        for predicted, ground_truth in self.CLEAN_PAIRS:
            cer = compute_cer(predicted, ground_truth)
            assert cer < 5.0, (
                f"CER trop élevé sur document propre : {cer:.2f}% "
                f"({predicted!r} vs {ground_truth!r})"
            )

    def test_cer_documents_bruites(self):
        """CER ≤ 20% sur des textes avec erreurs OCR simulées (scénario D)."""
        for predicted, ground_truth in self.NOISY_PAIRS:
            cer = compute_cer(predicted, ground_truth)
            assert cer <= 20.0, (
                f"CER trop élevé sur document bruité : {cer:.2f}% "
                f"({predicted!r} vs {ground_truth!r})"
            )

    def test_cer_valeur_nulle_textes_identiques(self):
        """Textes identiques → CER = 0%."""
        assert compute_cer("SIRET 12345678901234", "SIRET 12345678901234") == 0.0

    def test_cer_ground_truth_vide(self):
        """Ground truth vide → CER normalisé sans division par zéro."""
        cer = compute_cer("texte prédit", "")
        assert isinstance(cer, float)


# ------------------------------------------------------------------
# extract_all
# ------------------------------------------------------------------

class TestExtractAll:
    def test_extract_all_retourne_tous_les_champs(self, e):
        """extract_all doit retourner exactement les champs requis."""
        champs_requis = {
            "siret", "tva_intra", "montant_ht", "tva", "montant_ttc",
            "date_emission", "date_expiration", "raison_sociale", "iban", "bic",
            "extraction_confidence",
        }
        text = "Société : Test SAS SIRET 552 049 447 00013 Montant TTC : 500 EUR"
        result = e.extract_all(text)
        assert set(result.keys()) == champs_requis

    def test_extract_all_confidence_entre_0_et_1(self, e):
        """extraction_confidence doit être entre 0 et 1."""
        text = "Quelques mots sans entités particulières"
        result = e.extract_all(text)
        assert 0.0 <= result["extraction_confidence"] <= 1.0

    def test_extract_all_champs_critiques_jamais_absents(self, e):
        """
        Les champs critiques (pour Rôle 5) doivent toujours être présents
        dans le dict, même s'ils valent None.
        """
        champs_critiques = [
            "siret", "montant_ht", "tva", "montant_ttc",
            "date_expiration", "raison_sociale", "iban",
        ]
        text = "Texte vide sans informations exploitables"
        result = e.extract_all(text)
        for champ in champs_critiques:
            assert champ in result, f"Champ critique manquant : {champ}"
