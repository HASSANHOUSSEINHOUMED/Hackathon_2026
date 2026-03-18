"""
Générateur de documents de test avec erreurs spécifiques.
Chaque document cible une règle de validation particulière pour tester le système.

Usage:
    python generate_test_errors.py --output ./output/test_errors
"""
import argparse
import json
import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from company_factory import CompanyFactory
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ═══════════════════════════════════════════════════════════════════════════
# Utilitaires
# ═══════════════════════════════════════════════════════════════════════════

def draw_header(c, company, height, title="DOCUMENT"):
    """En-tête commun."""
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(0, height - 30 * mm, A4[0], 30 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, height - 20 * mm, title)
    c.setFont("Helvetica", 10)
    if company:
        c.drawString(100 * mm, height - 15 * mm, company.raison_sociale)
        c.drawString(100 * mm, height - 22 * mm, f"SIRET: {company.siret}")


def create_invalid_siret() -> str:
    """Génère un SIRET invalide (ne passe pas Luhn)."""
    # SIRET de 14 chiffres mais checksum incorrect
    return "12345678901234"  # Ne passe pas Luhn


def create_invalid_iban() -> str:
    """Génère un IBAN invalide (checksum incorrect)."""
    return "FR00 1234 5678 9012 3456 7890 123"  # Checksum 00 invalide


def create_invalid_tva_intra() -> str:
    """Génère un numéro TVA intra invalide."""
    return "FR99123456789"  # Clé invalide


# ═══════════════════════════════════════════════════════════════════════════
# Générateurs de documents avec erreurs
# ═══════════════════════════════════════════════════════════════════════════

def generate_tva_calcul_error(output_path: str, company) -> dict:
    """
    Génère une facture avec erreur de calcul TVA.
    Règle: TVA_CALCUL_ERROR
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    draw_header(c, company, height, "FACTURE")
    
    num_facture = f"FAC-ERR-TVA-001"
    date_emission = date.today() - timedelta(days=5)
    
    # Montants avec erreur de TVA
    montant_ht = 1000.00
    taux_tva = 0.20
    montant_tva_correct = 200.00
    montant_tva_affiche = 150.00  # ERREUR : devrait être 200€
    montant_ttc = montant_ht + montant_tva_affiche  # 1150 au lieu de 1200
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, f"Facture N° {num_facture}")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 10 * mm, f"Date : {date_emission.strftime('%d/%m/%Y')}")
    
    # Tableau
    y -= 30 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Désignation")
    c.drawString(140 * mm, y, "Montant")
    
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, "Prestation de service")
    c.drawString(140 * mm, y, f"{montant_ht:.2f} €")
    
    # Totaux avec erreur
    y -= 20 * mm
    c.drawString(100 * mm, y, f"Total HT :")
    c.drawString(150 * mm, y, f"{montant_ht:.2f} €")
    y -= 8 * mm
    c.drawString(100 * mm, y, f"TVA (20%) :")
    c.drawString(150 * mm, y, f"{montant_tva_affiche:.2f} €")  # ERREUR ICI
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100 * mm, y, f"Total TTC :")
    c.drawString(150 * mm, y, f"{montant_ttc:.2f} €")
    
    # Mentions légales
    y -= 30 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, f"SIRET : {company.siret}   TVA : {company.tva_intra}")
    c.drawString(20 * mm, y - 5 * mm, f"IBAN : {company.iban}")
    
    c.save()
    
    return {
        "document_id": "FAC-ERR-TVA-001",
        "doc_type": "facture",
        "expected_errors": ["TVA_CALCUL_ERROR"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "montant_ht": montant_ht,
            "montant_tva": montant_tva_affiche,
            "montant_ttc": montant_ttc,
            "taux_tva": 0.20,
            "iban": company.iban,
        },
    }


def generate_ttc_calcul_error(output_path: str, company) -> dict:
    """
    Génère une facture avec erreur de calcul TTC.
    Règle: TTC_CALCUL_ERROR
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    draw_header(c, company, height, "FACTURE")
    
    num_facture = f"FAC-ERR-TTC-001"
    date_emission = date.today() - timedelta(days=3)
    
    # Montants avec erreur de TTC
    montant_ht = 500.00
    montant_tva = 100.00  # Correct pour 20%
    montant_ttc = 650.00  # ERREUR : devrait être 600€
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, f"Facture N° {num_facture}")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 10 * mm, f"Date : {date_emission.strftime('%d/%m/%Y')}")
    
    y -= 40 * mm
    c.drawString(20 * mm, y, "Conseil en informatique")
    c.drawString(140 * mm, y, f"{montant_ht:.2f} €")
    
    y -= 20 * mm
    c.drawString(100 * mm, y, f"Total HT : {montant_ht:.2f} €")
    y -= 8 * mm
    c.drawString(100 * mm, y, f"TVA (20%) : {montant_tva:.2f} €")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:.2f} €")  # ERREUR
    
    y -= 30 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    
    c.save()
    
    return {
        "document_id": "FAC-ERR-TTC-001",
        "doc_type": "facture",
        "expected_errors": ["TTC_CALCUL_ERROR"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "montant_ht": montant_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
        },
    }


def generate_attestation_expiree(output_path: str, company) -> dict:
    """
    Génère une attestation URSSAF expirée.
    Règle: ATTESTATION_EXPIREE
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # En-tête URSSAF
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(0, height - 40 * mm, width, 40 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, height - 20 * mm, "URSSAF")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 32 * mm, "Union de Recouvrement des Cotisations")
    
    # Dates - attestation expirée
    date_emission = date.today() - timedelta(days=120)
    date_expiration = date.today() - timedelta(days=30)  # EXPIREE il y a 30 jours
    
    y = height - 60 * mm
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, y, "Attestation de Vigilance")
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(30 * mm, y, f"Raison Sociale : {company.raison_sociale}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"SIRET : {company.siret}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"SIREN : {company.siren}")
    
    y -= 20 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#E53E3E"))  # Rouge pour l'expiration
    c.drawString(30 * mm, y, f"Date d'émission : {date_emission.strftime('%d/%m/%Y')}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"Date d'expiration : {date_expiration.strftime('%d/%m/%Y')}")
    
    y -= 20 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(30 * mm, y, "Cette attestation certifie que l'entreprise est à jour")
    c.drawString(30 * mm, y - 5 * mm, "de ses obligations déclaratives et de paiement.")
    
    c.save()
    
    return {
        "document_id": "URSSAF-ERR-EXP-001",
        "doc_type": "attestation_urssaf",
        "expected_errors": ["ATTESTATION_EXPIREE"],
        "entities": {
            "siret": company.siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "date_emission": date_emission.isoformat(),
            "date_expiration": date_expiration.isoformat(),
        },
    }


def generate_kbis_perime(output_path: str, company) -> dict:
    """
    Génère un Kbis périmé (> 90 jours).
    Règle: KBIS_PERIME
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # En-tête officiel
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(0, height - 35 * mm, width, 35 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 18 * mm, "EXTRAIT K-BIS")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 28 * mm, "Greffe du Tribunal de Commerce")
    
    # Date de délivrance > 90 jours
    date_delivrance = date.today() - timedelta(days=120)  # PERIME
    
    y = height - 55 * mm
    c.setFillColor(colors.HexColor("#2D3748"))
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "IDENTIFICATION DE LA PERSONNE MORALE")
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, f"Dénomination : {company.raison_sociale}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIREN : {company.siren}")
    y -= 8 * mm  
    c.drawString(20 * mm, y, f"SIRET du siège : {company.siret}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Forme juridique : {company.forme_juridique}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Capital : {company.capital_social:,} €")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Adresse : {company.adresse_rue}, {company.adresse_cp} {company.adresse_ville}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Code NAF : {company.code_naf} - {company.libelle_naf}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Date de création : {company.date_creation.strftime('%d/%m/%Y')}")
    
    y -= 20 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#E53E3E"))
    c.drawString(20 * mm, y, f"Date de délivrance : {date_delivrance.strftime('%d/%m/%Y')}")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(20 * mm, y - 8 * mm, "(Ce document date de plus de 90 jours)")
    
    c.save()
    
    return {
        "document_id": "KBIS-ERR-PER-001",
        "doc_type": "kbis",
        "expected_warnings": ["KBIS_PERIME"],
        "entities": {
            "siret": company.siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "date_delivrance": date_delivrance.isoformat(),
        },
    }


def generate_devis_expire(output_path: str, company) -> dict:
    """
    Génère un devis expiré.
    Règle: DEVIS_EXPIRE
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    draw_header(c, company, height, "DEVIS")
    
    num_devis = "DEV-ERR-EXP-001"
    date_emission = date.today() - timedelta(days=60)
    date_validite = date.today() - timedelta(days=30)  # EXPIRE
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, f"Devis N° {num_devis}")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 10 * mm, f"Date d'émission : {date_emission.strftime('%d/%m/%Y')}")
    
    c.setFillColor(colors.HexColor("#E53E3E"))
    c.drawString(20 * mm, y - 18 * mm, f"Validité : {date_validite.strftime('%d/%m/%Y')}")
    
    y -= 40 * mm
    c.setFillColor(colors.HexColor("#2D3748"))
    montant_ht = 2500.00
    montant_tva = 500.00
    montant_ttc = 3000.00
    
    c.drawString(20 * mm, y, "Installation système informatique")
    c.drawString(140 * mm, y, f"{montant_ht:.2f} €")
    
    y -= 20 * mm
    c.drawString(100 * mm, y, f"Total HT : {montant_ht:.2f} €")
    y -= 8 * mm
    c.drawString(100 * mm, y, f"TVA (20%) : {montant_tva:.2f} €")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:.2f} €")
    
    y -= 30 * mm
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    
    c.save()
    
    return {
        "document_id": "DEV-ERR-EXP-001",
        "doc_type": "devis",
        "expected_warnings": ["DEVIS_EXPIRE"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "date_validite": date_validite.isoformat(),
            "montant_ht": montant_ht,
            "montant_ttc": montant_ttc,
        },
    }


def generate_siret_invalide(output_path: str, company) -> dict:
    """
    Génère une facture avec SIRET invalide (format incorrect).
    Règle: SIRET_FORMAT_INVALIDE
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    siret_invalide = create_invalid_siret()
    
    draw_header(c, None, height, "FACTURE")
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Facture N° FAC-ERR-SIRET-001")
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, company.raison_sociale)
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIRET : {siret_invalide}")  # INVALIDE
    
    y -= 30 * mm
    montant_ht = 800.00
    montant_tva = 160.00
    montant_ttc = 960.00
    c.drawString(20 * mm, y, "Développement web")
    c.drawString(140 * mm, y, f"{montant_ht:.2f} €")
    
    y -= 20 * mm
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:.2f} €")
    
    c.save()
    
    return {
        "document_id": "FAC-ERR-SIRET-001",
        "doc_type": "facture",
        "expected_errors": ["SIRET_FORMAT_INVALIDE"],
        "entities": {
            "siret": siret_invalide,
            "raison_sociale": company.raison_sociale,
            "montant_ttc": montant_ttc,
        },
    }


def generate_iban_invalide(output_path: str, company) -> dict:
    """
    Génère un RIB avec IBAN invalide.
    Règle: IBAN_FORMAT_INVALIDE
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    iban_invalide = create_invalid_iban()
    bic = "BNPAFRPP"
    
    draw_header(c, company, height, "RELEVÉ D'IDENTITÉ BANCAIRE")
    
    y = height - 55 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Titulaire du compte")
    
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, company.raison_sociale)
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    
    y -= 20 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Coordonnées bancaires")
    
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#E53E3E"))
    c.drawString(20 * mm, y, f"IBAN : {iban_invalide}")  # INVALIDE
    y -= 8 * mm
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(20 * mm, y, f"BIC : {bic}")
    
    c.save()
    
    return {
        "document_id": "RIB-ERR-IBAN-001",
        "doc_type": "rib",
        "expected_errors": ["IBAN_FORMAT_INVALIDE"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "iban": iban_invalide,
            "bic": bic,
        },
    }


def generate_tva_intra_invalide(output_path: str, company) -> dict:
    """
    Génère une facture avec TVA intracommunautaire invalide.
    Règle: TVA_INTRA_INVALIDE
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    tva_invalide = create_invalid_tva_intra()
    
    draw_header(c, company, height, "FACTURE")
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Facture N° FAC-ERR-TVA-INTRA-001")
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, company.raison_sociale)
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    y -= 8 * mm
    c.setFillColor(colors.HexColor("#E53E3E"))
    c.drawString(20 * mm, y, f"TVA Intra : {tva_invalide}")  # INVALIDE
    
    y -= 30 * mm
    c.setFillColor(colors.HexColor("#2D3748"))
    montant_ttc = 1200.00
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:.2f} €")
    
    c.save()
    
    return {
        "document_id": "FAC-ERR-TVA-INTRA-001",
        "doc_type": "facture",
        "expected_warnings": ["TVA_INTRA_INVALIDE"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "tva_intra": tva_invalide,
            "montant_ttc": montant_ttc,
        },
    }


def generate_montant_anormal(output_path: str, company) -> dict:
    """
    Génère une facture avec montant anormalement élevé.
    Règle: MONTANT_ANORMAL (détection statistique)
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    draw_header(c, company, height, "FACTURE")
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Facture N° FAC-ERR-ANORMAL-001")
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 10 * mm, f"Date : {date.today().strftime('%d/%m/%Y')}")
    
    # Montant anormalement élevé
    montant_ht = 999999.99
    montant_tva = 199999.99
    montant_ttc = 1199999.98
    
    y -= 40 * mm
    c.drawString(20 * mm, y, "Prestation exceptionnelle")
    c.drawString(130 * mm, y, f"{montant_ht:,.2f} €")
    
    y -= 20 * mm
    c.drawString(100 * mm, y, f"Total HT : {montant_ht:,.2f} €")
    y -= 8 * mm
    c.drawString(100 * mm, y, f"TVA (20%) : {montant_tva:,.2f} €")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#E53E3E"))
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:,.2f} €")
    
    y -= 30 * mm
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    
    c.save()
    
    return {
        "document_id": "FAC-ERR-ANORMAL-001",
        "doc_type": "facture",
        "expected_infos": ["MONTANT_ANORMAL"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "montant_ht": montant_ht,
            "montant_tva": montant_tva,
            "montant_ttc": montant_ttc,
        },
    }


def generate_siret_mismatch_pair(output_dir: Path, company1, company2) -> list:
    """
    Génère une paire de documents avec SIRET différents mais même raison sociale.
    Règle: SIRET_MISMATCH (inter-documents)
    """
    results = []
    
    # Document 1 : Facture avec SIRET de company1
    path1 = str(output_dir / "FAC-ERR-MISMATCH-001.pdf")
    width, height = A4
    c = canvas.Canvas(path1, pagesize=A4)
    draw_header(c, company1, height, "FACTURE")
    
    raison_sociale_commune = "ENTREPRISE TEST MISMATCH"
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Facture N° FAC-ERR-MISMATCH-001")
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y, raison_sociale_commune)
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIRET : {company1.siret}")  # Premier SIRET
    
    y -= 30 * mm
    montant_ttc = 1500.00
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:.2f} €")
    c.save()
    
    results.append({
        "document_id": "FAC-ERR-MISMATCH-001",
        "doc_type": "facture",
        "expected_errors": ["SIRET_MISMATCH"],
        "supplier_group": "MISMATCH-GROUP",
        "entities": {
            "siret": company1.siret,
            "raison_sociale": raison_sociale_commune,
            "montant_ttc": montant_ttc,
        },
    })
    
    # Document 2 : Attestation URSSAF avec SIRET différent mais même raison sociale
    path2 = str(output_dir / "URSSAF-ERR-MISMATCH-001.pdf")
    c2 = canvas.Canvas(path2, pagesize=A4)
    
    c2.setFillColor(colors.HexColor("#1B2A4A"))
    c2.rect(0, height - 40 * mm, width, 40 * mm, fill=1, stroke=0)
    c2.setFillColor(colors.white)
    c2.setFont("Helvetica-Bold", 22)
    c2.drawString(20 * mm, height - 25 * mm, "URSSAF")
    
    y = height - 60 * mm
    c2.setFillColor(colors.HexColor("#2D3748"))
    c2.setFont("Helvetica", 10)
    c2.drawString(20 * mm, y, f"Raison Sociale : {raison_sociale_commune}")
    y -= 10 * mm
    c2.drawString(20 * mm, y, f"SIRET : {company2.siret}")  # SIRET DIFFÉRENT
    
    date_exp = date.today() + timedelta(days=60)
    y -= 20 * mm
    c2.drawString(20 * mm, y, f"Validité : {date_exp.strftime('%d/%m/%Y')}")
    c2.save()
    
    results.append({
        "document_id": "URSSAF-ERR-MISMATCH-001",
        "doc_type": "attestation_urssaf",
        "expected_errors": ["SIRET_MISMATCH"],
        "supplier_group": "MISMATCH-GROUP",
        "entities": {
            "siret": company2.siret,
            "raison_sociale": raison_sociale_commune,
            "date_expiration": date_exp.isoformat(),
        },
    })
    
    return results


def generate_raison_sociale_mismatch(output_path: str, company) -> dict:
    """
    Génère un document avec raison sociale différente du SIRET enregistré.
    Règle: RAISON_SOCIALE_MISMATCH
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)
    
    raison_sociale_differente = "AUTRE ENTREPRISE SARL"
    
    draw_header(c, company, height, "FACTURE")
    
    y = height - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Facture N° FAC-ERR-RS-001")
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#E53E3E"))
    c.drawString(20 * mm, y, raison_sociale_differente)  # Différente du SIRET
    y -= 8 * mm
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    
    y -= 30 * mm
    montant_ttc = 2000.00
    c.drawString(100 * mm, y, f"Total TTC : {montant_ttc:.2f} €")
    
    c.save()
    
    return {
        "document_id": "FAC-ERR-RS-001",
        "doc_type": "facture",
        "expected_warnings": ["RAISON_SOCIALE_MISMATCH"],
        "entities": {
            "siret": company.siret,
            "raison_sociale": raison_sociale_differente,
            "raison_sociale_siret_ref": company.raison_sociale,
            "montant_ttc": montant_ttc,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════
# Programme principal
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Génère des documents de test avec erreurs")
    parser.add_argument("--output", type=str, default="./output/test_errors",
                       help="Dossier de sortie")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GÉNÉRATION DES DOCUMENTS DE TEST AVEC ERREURS")
    print("=" * 60)
    
    factory = CompanyFactory()
    
    # Créer quelques entreprises de test
    companies = [factory.generate() for _ in range(3)]
    
    all_results = []
    
    # 1. TVA_CALCUL_ERROR
    print("\n[1/12] TVA_CALCUL_ERROR...")
    result = generate_tva_calcul_error(str(output_dir / "FAC-ERR-TVA-001.pdf"), companies[0])
    all_results.append(result)
    
    # 2. TTC_CALCUL_ERROR
    print("[2/12] TTC_CALCUL_ERROR...")
    result = generate_ttc_calcul_error(str(output_dir / "FAC-ERR-TTC-001.pdf"), companies[0])
    all_results.append(result)
    
    # 3. ATTESTATION_EXPIREE
    print("[3/12] ATTESTATION_EXPIREE...")
    result = generate_attestation_expiree(str(output_dir / "URSSAF-ERR-EXP-001.pdf"), companies[0])
    all_results.append(result)
    
    # 4. KBIS_PERIME
    print("[4/12] KBIS_PERIME...")
    result = generate_kbis_perime(str(output_dir / "KBIS-ERR-PER-001.pdf"), companies[0])
    all_results.append(result)
    
    # 5. DEVIS_EXPIRE
    print("[5/12] DEVIS_EXPIRE...")
    result = generate_devis_expire(str(output_dir / "DEV-ERR-EXP-001.pdf"), companies[1])
    all_results.append(result)
    
    # 6. SIRET_FORMAT_INVALIDE
    print("[6/12] SIRET_FORMAT_INVALIDE...")
    result = generate_siret_invalide(str(output_dir / "FAC-ERR-SIRET-001.pdf"), companies[1])
    all_results.append(result)
    
    # 7. IBAN_FORMAT_INVALIDE
    print("[7/12] IBAN_FORMAT_INVALIDE...")
    result = generate_iban_invalide(str(output_dir / "RIB-ERR-IBAN-001.pdf"), companies[1])
    all_results.append(result)
    
    # 8. TVA_INTRA_INVALIDE
    print("[8/12] TVA_INTRA_INVALIDE...")
    result = generate_tva_intra_invalide(str(output_dir / "FAC-ERR-TVA-INTRA-001.pdf"), companies[2])
    all_results.append(result)
    
    # 9. MONTANT_ANORMAL
    print("[9/12] MONTANT_ANORMAL...")
    result = generate_montant_anormal(str(output_dir / "FAC-ERR-ANORMAL-001.pdf"), companies[2])
    all_results.append(result)
    
    # 10-11. SIRET_MISMATCH (paire de documents)
    print("[10-11/12] SIRET_MISMATCH (2 documents)...")
    results = generate_siret_mismatch_pair(output_dir, companies[0], companies[1])
    all_results.extend(results)
    
    # 12. RAISON_SOCIALE_MISMATCH
    print("[12/12] RAISON_SOCIALE_MISMATCH...")
    result = generate_raison_sociale_mismatch(str(output_dir / "FAC-ERR-RS-001.pdf"), companies[2])
    all_results.append(result)
    
    # Sauvegarder le fichier de labels (ground truth)
    labels_file = output_dir / "test_errors_labels.json"
    with open(labels_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✓ {len(all_results)} documents générés dans : {output_dir}")
    print(f"✓ Labels sauvegardés dans : {labels_file}")
    print("=" * 60)
    
    # Résumé des erreurs couvertes
    print("\n📋 RÈGLES DE VALIDATION COUVERTES :")
    print("-" * 40)
    rules_covered = set()
    for doc in all_results:
        for key in ["expected_errors", "expected_warnings", "expected_infos"]:
            if key in doc:
                rules_covered.update(doc[key])
    
    for rule in sorted(rules_covered):
        print(f"  • {rule}")
    
    print(f"\nTotal : {len(rules_covered)} règles couvertes")
    

if __name__ == "__main__":
    main()
