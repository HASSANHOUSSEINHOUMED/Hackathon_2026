"""
Tests unitaires pour le moteur de règles de validation.
"""
import pytest
from datetime import date, timedelta

from rules_engine import RulesEngine


@pytest.fixture
def engine():
    return RulesEngine()


# ═══════════════════════════════════════
# SIRET_MISMATCH
# ═══════════════════════════════════════
class TestSiretMismatch:
    def test_detects_mismatch(self, engine):
        docs = [
            {"document_id": "FAC_001", "type": "facture", "entities": {"siret": "12345678901234"}},
            {"document_id": "URSSAF_001", "type": "urssaf", "entities": {"siret": "98765432109876"}},
        ]
        anomalies = engine.validate_batch(docs)
        mismatch = [a for a in anomalies if a["rule_id"] == "SIRET_MISMATCH"]
        assert len(mismatch) > 0

    def test_no_false_positive(self, engine):
        docs = [
            {"document_id": "FAC_001", "type": "facture", "entities": {"siret": "44306184100047"}},
            {"document_id": "URSSAF_001", "type": "urssaf", "entities": {"siret": "44306184100047"}},
        ]
        anomalies = engine.validate_batch(docs)
        mismatch = [a for a in anomalies if a["rule_id"] == "SIRET_MISMATCH"]
        assert len(mismatch) == 0


# ═══════════════════════════════════════
# TVA_CALCUL_ERROR
# ═══════════════════════════════════════
class TestTvaCalcul:
    def test_detects_bad_tva(self, engine):
        docs = [{"document_id": "FAC_002", "type": "facture", "entities": {
            "montant_ht": 1000.0, "tva": 500.0, "montant_ttc": 1500.0,
        }}]
        anomalies = engine.validate_batch(docs)
        tva_errors = [a for a in anomalies if a["rule_id"] == "TVA_CALCUL_ERROR"]
        assert len(tva_errors) > 0

    def test_valid_tva_20(self, engine):
        docs = [{"document_id": "FAC_003", "type": "facture", "entities": {
            "montant_ht": 1000.0, "tva": 200.0, "montant_ttc": 1200.0,
        }}]
        anomalies = engine.validate_batch(docs)
        tva_errors = [a for a in anomalies if a["rule_id"] == "TVA_CALCUL_ERROR"]
        assert len(tva_errors) == 0


# ═══════════════════════════════════════
# TTC_CALCUL_ERROR
# ═══════════════════════════════════════
class TestTtcCalcul:
    def test_detects_ttc_error(self, engine):
        docs = [{"document_id": "FAC_004", "type": "facture", "entities": {
            "montant_ht": 1000.0, "tva": 200.0, "montant_ttc": 1300.0,  # devrait être 1200
        }}]
        anomalies = engine.validate_batch(docs)
        ttc_errors = [a for a in anomalies if a["rule_id"] == "TTC_CALCUL_ERROR"]
        assert len(ttc_errors) > 0

    def test_valid_ttc(self, engine):
        docs = [{"document_id": "FAC_005", "type": "facture", "entities": {
            "montant_ht": 1000.0, "tva": 200.0, "montant_ttc": 1200.0,
        }}]
        anomalies = engine.validate_batch(docs)
        ttc_errors = [a for a in anomalies if a["rule_id"] == "TTC_CALCUL_ERROR"]
        assert len(ttc_errors) == 0


# ═══════════════════════════════════════
# ATTESTATION_EXPIREE
# ═══════════════════════════════════════
class TestAttestationExpiree:
    def test_detects_expired(self, engine):
        expired_date = (date.today() - timedelta(days=10)).strftime("%d/%m/%Y")
        docs = [{"document_id": "URSSAF_002", "type": "urssaf", "entities": {
            "date_expiration": expired_date,
        }}]
        anomalies = engine.validate_batch(docs)
        expired = [a for a in anomalies if a["rule_id"] == "ATTESTATION_EXPIREE"]
        assert len(expired) > 0
        assert expired[0]["severity"] == "ERROR"

    def test_not_expired(self, engine):
        future_date = (date.today() + timedelta(days=60)).strftime("%d/%m/%Y")
        docs = [{"document_id": "URSSAF_003", "type": "urssaf", "entities": {
            "date_expiration": future_date,
        }}]
        anomalies = engine.validate_batch(docs)
        expired = [a for a in anomalies if a["rule_id"] == "ATTESTATION_EXPIREE"]
        assert len(expired) == 0


# ═══════════════════════════════════════
# DEVIS_EXPIRE
# ═══════════════════════════════════════
class TestDevisExpire:
    def test_detects_expired_devis(self, engine):
        expired_date = (date.today() - timedelta(days=5)).strftime("%d/%m/%Y")
        docs = [{"document_id": "DEV_001", "type": "devis", "entities": {
            "date_validite": expired_date,
        }}]
        anomalies = engine.validate_batch(docs)
        expired = [a for a in anomalies if a["rule_id"] == "DEVIS_EXPIRE"]
        assert len(expired) > 0

    def test_valid_devis(self, engine):
        future = (date.today() + timedelta(days=30)).strftime("%d/%m/%Y")
        docs = [{"document_id": "DEV_002", "type": "devis", "entities": {
            "date_validite": future,
        }}]
        anomalies = engine.validate_batch(docs)
        expired = [a for a in anomalies if a["rule_id"] == "DEVIS_EXPIRE"]
        assert len(expired) == 0


# ═══════════════════════════════════════
# KBIS_PERIME
# ═══════════════════════════════════════
class TestKbisPerime:
    def test_detects_old_kbis(self, engine):
        old_date = (date.today() - timedelta(days=120)).strftime("%d/%m/%Y")
        docs = [{"document_id": "KBIS_001", "type": "kbis", "entities": {
            "date_emission": old_date,
        }}]
        anomalies = engine.validate_batch(docs)
        perime = [a for a in anomalies if a["rule_id"] == "KBIS_PERIME"]
        assert len(perime) > 0

    def test_recent_kbis(self, engine):
        recent = (date.today() - timedelta(days=10)).strftime("%d/%m/%Y")
        docs = [{"document_id": "KBIS_002", "type": "kbis", "entities": {
            "date_emission": recent,
        }}]
        anomalies = engine.validate_batch(docs)
        perime = [a for a in anomalies if a["rule_id"] == "KBIS_PERIME"]
        assert len(perime) == 0


# ═══════════════════════════════════════
# IBAN_MISMATCH
# ═══════════════════════════════════════
class TestIbanMismatch:
    def test_detects_iban_mismatch(self, engine):
        docs = [
            {"document_id": "RIB_001", "type": "rib", "entities": {"iban": "FR7630006000011234567890189"}},
            {"document_id": "FAC_006", "type": "facture", "entities": {"iban": "FR7630006000019876543210123"}},
        ]
        anomalies = engine.validate_batch(docs)
        mismatch = [a for a in anomalies if a["rule_id"] == "IBAN_MISMATCH"]
        assert len(mismatch) > 0

    def test_matching_iban(self, engine):
        docs = [
            {"document_id": "RIB_002", "type": "rib", "entities": {"iban": "FR7630006000011234567890189"}},
            {"document_id": "FAC_007", "type": "facture", "entities": {"iban": "FR7630006000011234567890189"}},
        ]
        anomalies = engine.validate_batch(docs)
        mismatch = [a for a in anomalies if a["rule_id"] == "IBAN_MISMATCH"]
        assert len(mismatch) == 0


# ═══════════════════════════════════════
# SIRET_FORMAT_INVALIDE
# ═══════════════════════════════════════
class TestSiretFormat:
    def test_invalid_siret(self, engine):
        docs = [{"document_id": "FAC_008", "type": "facture", "entities": {
            "siret": "12345678901234",  # Luhn invalide
        }}]
        anomalies = engine.validate_batch(docs)
        format_errors = [a for a in anomalies if a["rule_id"] == "SIRET_FORMAT_INVALIDE"]
        assert len(format_errors) > 0

    def test_valid_siret(self, engine):
        docs = [{"document_id": "FAC_009", "type": "facture", "entities": {
            "siret": "44306184100047",  # Luhn valide
        }}]
        anomalies = engine.validate_batch(docs)
        format_errors = [a for a in anomalies if a["rule_id"] == "SIRET_FORMAT_INVALIDE"]
        assert len(format_errors) == 0


# ═══════════════════════════════════════
# RAISON_SOCIALE_MISMATCH
# ═══════════════════════════════════════
class TestRaisonSociale:
    def test_detects_different_names(self, engine):
        docs = [
            {"document_id": "FAC_010", "type": "facture", "entities": {"raison_sociale": "ACME Technologies SAS"}},
            {"document_id": "KBIS_003", "type": "kbis", "entities": {"raison_sociale": "ZetaCorp Industries SARL"}},
        ]
        anomalies = engine.validate_batch(docs)
        mismatch = [a for a in anomalies if a["rule_id"] == "RAISON_SOCIALE_MISMATCH"]
        assert len(mismatch) > 0

    def test_same_name_different_case(self, engine):
        docs = [
            {"document_id": "FAC_011", "type": "facture", "entities": {"raison_sociale": "Dupont Conseil SAS"}},
            {"document_id": "KBIS_004", "type": "kbis", "entities": {"raison_sociale": "DUPONT CONSEIL SAS"}},
        ]
        anomalies = engine.validate_batch(docs)
        mismatch = [a for a in anomalies if a["rule_id"] == "RAISON_SOCIALE_MISMATCH"]
        assert len(mismatch) == 0
