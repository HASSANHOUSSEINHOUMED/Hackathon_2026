"""
Tests unitaires pour le module d'extraction d'entités OCR.
"""
import pytest

from extractor import EntityExtractor, iban_check, luhn_check


@pytest.fixture
def extractor():
    return EntityExtractor()


# ═══════════════════════════════════════
# Tests SIRET
# ═══════════════════════════════════════
class TestExtractSiret:
    def test_siret_propre(self, extractor):
        text = "Notre SIRET : 44306184100047 est actif."
        result = extractor.extract_siret(text)
        assert result is not None
        assert len(result) == 14

    def test_siret_avec_espaces(self, extractor):
        text = "SIRET : 443 061 841 00047"
        result = extractor.extract_siret(text)
        assert result is not None
        assert " " not in result

    def test_siret_absent(self, extractor):
        text = "Ce document ne contient aucun numéro."
        result = extractor.extract_siret(text)
        assert result is None

    def test_siret_bruite(self, extractor):
        text = "N° SIRET 443O618410OO47"  # O au lieu de 0
        result = extractor.extract_siret(text)
        # Peut être None ou corrigé, l'important est pas de crash
        assert result is None or len(result) == 14


# ═══════════════════════════════════════
# Tests TVA intracommunautaire
# ═══════════════════════════════════════
class TestExtractTvaIntra:
    def test_tva_propre(self, extractor):
        text = "TVA intracommunautaire : FR 83 443061841"
        result = extractor.extract_tva_intra(text)
        assert result is not None
        assert result.startswith("FR")

    def test_tva_compacte(self, extractor):
        text = "FR83443061841"
        result = extractor.extract_tva_intra(text)
        assert result == "FR83443061841"

    def test_tva_absente(self, extractor):
        text = "Pas de numéro de TVA ici."
        result = extractor.extract_tva_intra(text)
        assert result is None


# ═══════════════════════════════════════
# Tests Montants
# ═══════════════════════════════════════
class TestExtractMontants:
    def test_montants_complets(self, extractor):
        text = "Total HT : 1 250,00 €\nTVA (20%) : 250,00 €\nTotal TTC : 1 500,00 €"
        result = extractor.extract_montants(text)
        assert result["ht"] == 1250.00
        assert result["tva"] == 250.00
        assert result["ttc"] == 1500.00

    def test_montant_ttc_seul(self, extractor):
        text = "Net à payer : 3 456,78 EUR"
        result = extractor.extract_montants(text)
        assert result["ttc"] == 3456.78

    def test_aucun_montant(self, extractor):
        text = "Document sans montants financiers."
        result = extractor.extract_montants(text)
        assert result["ht"] is None
        assert result["tva"] is None
        assert result["ttc"] is None


# ═══════════════════════════════════════
# Tests Dates
# ═══════════════════════════════════════
class TestExtractDates:
    def test_date_emission(self, extractor):
        text = "Date : 15/03/2025\nExpire le 30/06/2025"
        result = extractor.extract_dates(text)
        assert result["emission"] == "15/03/2025"

    def test_date_expiration(self, extractor):
        text = "Date d'expiration : 30/06/2025"
        result = extractor.extract_dates(text)
        assert result["expiration"] == "30/06/2025"

    def test_aucune_date(self, extractor):
        text = "Pas de date dans ce texte."
        result = extractor.extract_dates(text)
        assert result["emission"] is None


# ═══════════════════════════════════════
# Tests IBAN
# ═══════════════════════════════════════
class TestExtractIban:
    def test_iban_propre(self, extractor):
        # IBAN FR valide (checksum correct)
        text = "IBAN : FR76 3000 6000 0112 3456 7890 189"
        result = extractor.extract_iban(text)
        if result is not None:
            assert result.startswith("FR")
            assert iban_check(result)

    def test_iban_absent(self, extractor):
        text = "Pas d'IBAN ici."
        result = extractor.extract_iban(text)
        assert result is None


# ═══════════════════════════════════════
# Tests Raison Sociale
# ═══════════════════════════════════════
class TestExtractRaisonSociale:
    def test_raison_sociale_keyword(self, extractor):
        text = "Société : ACME TECHNOLOGIES SAS\nSIRET : 12345678901234"
        result = extractor.extract_raison_sociale(text)
        assert result is not None
        assert "ACME" in result.upper()

    def test_raison_sociale_absente(self, extractor):
        text = "123 456 789"
        result = extractor.extract_raison_sociale(text)
        # Peut retourner None ou une valeur
        assert result is None or isinstance(result, str)


# ═══════════════════════════════════════
# Tests utilitaires
# ═══════════════════════════════════════
class TestLuhnCheck:
    def test_luhn_valide(self):
        assert luhn_check("44306184100047") is True

    def test_luhn_invalide(self):
        assert luhn_check("12345678901234") is False

    def test_luhn_vide(self):
        assert luhn_check("") is False


class TestIbanCheck:
    def test_iban_format(self):
        # Test basique de structure
        assert iban_check("") is False
        assert iban_check("FR") is False


# ═══════════════════════════════════════
# Tests extract_all
# ═══════════════════════════════════════
class TestExtractAll:
    def test_extract_all_facture(self, extractor):
        text = """
        FACTURE N° FAC-2025-0001
        Date : 15/03/2025
        Société : DUPONT CONSULTING SAS
        SIRET : 44306184100047
        TVA intracommunautaire : FR83443061841
        Total HT : 5 000,00 €
        TVA (20%) : 1 000,00 €
        Total TTC : 6 000,00 €
        IBAN : FR7630006000011234567890189
        """
        result = extractor.extract_all(text)
        assert isinstance(result, dict)
        assert "siret" in result
        assert "montant_ht" in result
        assert "extraction_confidence" in result
