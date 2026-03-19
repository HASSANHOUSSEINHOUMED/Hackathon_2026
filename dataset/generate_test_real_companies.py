"""
Générateur de documents de test avec VRAIES entreprises françaises.
Utilise des SIREN/SIRET réels pour tester la détection d'erreurs.

Usage:
    python generate_test_real_companies.py --output ./output/test_real
    python generate_test_real_companies.py --output ./output/test_real --scenario all
"""
import argparse
import json
import random
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ═══════════════════════════════════════════════════════════════════════════
# Données d'entreprises réelles françaises (SIREN/SIRET publics)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class RealCompany:
    """Données d'une vraie entreprise française."""
    raison_sociale: str
    siren: str
    siret: str
    tva_intra: str
    adresse: str
    code_postal: str
    ville: str
    forme_juridique: str
    iban: str  # IBAN fictif mais valide pour le format
    bic: str


# Entreprises réelles françaises (données publiques)
REAL_COMPANIES = [
    RealCompany(
        raison_sociale="CARREFOUR",
        siren="652014051",
        siret="65201405100013",
        tva_intra="FR39652014051",
        adresse="93 Avenue de Paris",
        code_postal="91300",
        ville="Massy",
        forme_juridique="SA",
        iban="FR7630004000031234567890143",
        bic="BNPAFRPP",
    ),
    RealCompany(
        raison_sociale="TOTAL ENERGIES SE",
        siren="542051180",
        siret="54205118000066",
        tva_intra="FR27542051180",
        adresse="2 Place Jean Millier",
        code_postal="92400",
        ville="Courbevoie",
        forme_juridique="SE",
        iban="FR7630006000011234567890123",
        bic="AGRIFRPP",
    ),
    RealCompany(
        raison_sociale="ORANGE SA",
        siren="380129866",
        siret="38012986600034",
        tva_intra="FR89380129866",
        adresse="111 Quai du Président Roosevelt",
        code_postal="92130",
        ville="Issy-les-Moulineaux",
        forme_juridique="SA",
        iban="FR7610107001011234567890129",
        bic="ABORFRPP",
    ),
    RealCompany(
        raison_sociale="SNCF VOYAGEURS",
        siren="519037584",
        siret="51903758400017",
        tva_intra="FR32519037584",
        adresse="9 Rue Jean-Philippe Rameau",
        code_postal="93200",
        ville="Saint-Denis",
        forme_juridique="SA",
        iban="FR7620041000010123456789012",
        bic="PSSTFRPP",
    ),
    RealCompany(
        raison_sociale="AIR FRANCE",
        siren="420495178",
        siret="42049517800015",
        tva_intra="FR61420495178",
        adresse="45 Rue de Paris",
        code_postal="95700",
        ville="Roissy-en-France",
        forme_juridique="SA",
        iban="FR7630003030001234567890185",
        bic="SOGEFRPP",
    ),
    RealCompany(
        raison_sociale="RENAULT SAS",
        siren="780129987",
        siret="78012998700015",
        tva_intra="FR56780129987",
        adresse="122-122 bis Avenue du Général Leclerc",
        code_postal="92100",
        ville="Boulogne-Billancourt",
        forme_juridique="SAS",
        iban="FR7617515900001234567890141",
        bic="CEABORPP",
    ),
    RealCompany(
        raison_sociale="DANONE SA",
        siren="552032534",
        siret="55203253400013",
        tva_intra="FR92552032534",
        adresse="17 Boulevard Haussmann",
        code_postal="75009",
        ville="Paris",
        forme_juridique="SA",
        iban="FR7630076020821234567890189",
        bic="NORDFRPP",
    ),
    RealCompany(
        raison_sociale="BOUYGUES SA",
        siren="572015246",
        siret="57201524600014",
        tva_intra="FR14572015246",
        adresse="32 Avenue Hoche",
        code_postal="75008",
        ville="Paris",
        forme_juridique="SA",
        iban="FR7614410000011234567890163",
        bic="BDFEFRPP",
    ),
    RealCompany(
        raison_sociale="ENGIE SA",
        siren="542107651",
        siret="54210765100018",
        tva_intra="FR03542107651",
        adresse="1 Place Samuel de Champlain",
        code_postal="92400",
        ville="Courbevoie",
        forme_juridique="SA",
        iban="FR7630027170001234567890127",
        bic="CMCIFRPP",
    ),
    RealCompany(
        raison_sociale="SOCIETE GENERALE",
        siren="552120222",
        siret="55212022200010",
        tva_intra="FR13552120222",
        adresse="29 Boulevard Haussmann",
        code_postal="75009",
        ville="Paris",
        forme_juridique="SA",
        iban="FR7630003000010123456789018",
        bic="SOGEFRPP",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# Constantes graphiques
# ═══════════════════════════════════════════════════════════════════════════

WIDTH, HEIGHT = A4
COLOR_DARK = colors.HexColor("#1B2A4A")
COLOR_TEXT = colors.HexColor("#2D3748")
COLOR_RED = colors.HexColor("#E53E3E")
COLOR_GRAY = colors.HexColor("#718096")
COLOR_ORANGE = colors.HexColor("#DD6B20")
COLOR_GREEN = colors.HexColor("#38A169")

TVA_RATES = [0.055, 0.10, 0.20]


# ═══════════════════════════════════════════════════════════════════════════
# Utilitaires de génération PDF
# ═══════════════════════════════════════════════════════════════════════════

def create_invalid_siret() -> str:
    """SIRET invalide (ne passe pas Luhn)."""
    return "12345678901234"


def create_invalid_iban() -> str:
    """IBAN invalide (checksum 00)."""
    return "FR0012345678901234567890123"


def create_invalid_tva_intra() -> str:
    """TVA intra invalide."""
    return "FR99123456789"


def draw_header(c, title: str, company: Optional[RealCompany] = None):
    """En-tête avec bandeau coloré."""
    c.setFillColor(COLOR_DARK)
    c.rect(0, HEIGHT - 30 * mm, WIDTH, 30 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, HEIGHT - 20 * mm, title)
    if company:
        c.setFont("Helvetica", 10)
        c.drawString(100 * mm, HEIGHT - 15 * mm, company.raison_sociale)
        c.drawString(100 * mm, HEIGHT - 22 * mm, f"SIRET: {company.siret}")


# ═══════════════════════════════════════════════════════════════════════════
# Générateurs de documents avec erreurs
# ═══════════════════════════════════════════════════════════════════════════

def gen_facture(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> dict:
    """
    Génère une facture PDF.
    
    Scenarios:
        - valid: Facture correcte
        - tva_error: TVA avec ratio illégal
        - ttc_error: TTC ≠ HT + TVA
        - siret_invalid: SIRET ne passant pas Luhn
        - iban_invalid: IBAN invalide
        - tva_intra_invalid: TVA intra invalide
        - multi_error: Plusieurs erreurs
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Données de base
    ht = round(random.uniform(500, 10000), 2)
    tva_rate = random.choice(TVA_RATES)
    
    # Ajustements selon le scénario
    siret = company.siret
    iban = company.iban
    tva_intra = company.tva_intra
    expected_anomalies = []
    
    if scenario == "tva_error":
        # TVA avec ratio illégal (15% au lieu de 5.5%, 10% ou 20%)
        tva = round(ht * 0.15, 2)
        expected_anomalies.append({"rule_id": "TVA_CALCUL_ERROR", "severity": "ERROR"})
    elif scenario == "ttc_error":
        tva = round(ht * tva_rate, 2)
        # TTC volontairement faux
        ttc = round(ht + tva + 100, 2)
        expected_anomalies.append({"rule_id": "TTC_CALCUL_ERROR", "severity": "ERROR"})
    elif scenario == "siret_invalid":
        siret = create_invalid_siret()
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "SIRET_FORMAT_INVALIDE", "severity": "ERROR"})
    elif scenario == "iban_invalid":
        iban = create_invalid_iban()
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "IBAN_FORMAT_INVALIDE", "severity": "ERROR"})
    elif scenario == "tva_intra_invalid":
        tva_intra = create_invalid_tva_intra()
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "TVA_INTRA_INVALIDE", "severity": "WARNING"})
    elif scenario == "multi_error":
        # Plusieurs erreurs cumulées
        siret = create_invalid_siret()
        iban = create_invalid_iban()
        tva = round(ht * 0.12, 2)  # ratio illégal
        expected_anomalies.extend([
            {"rule_id": "TVA_CALCUL_ERROR", "severity": "ERROR"},
            {"rule_id": "SIRET_FORMAT_INVALIDE", "severity": "ERROR"},
            {"rule_id": "IBAN_FORMAT_INVALIDE", "severity": "ERROR"},
        ])
    else:  # valid
        tva = round(ht * tva_rate, 2)
    
    # Calcul TTC si non défini
    if scenario != "ttc_error":
        ttc = round(ht + tva, 2)
    
    date_emission = date.today() - timedelta(days=random.randint(1, 30))
    
    # Dessin du PDF
    draw_header(c, "FACTURE", company if scenario not in ("siret_invalid", "multi_error") else None)
    
    y = HEIGHT - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, f"Facture N° {doc_id}")
    
    y -= 12 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"Date : {date_emission.strftime('%d/%m/%Y')}")
    
    y -= 20 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "Client :")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 6 * mm, company.raison_sociale)
    c.drawString(20 * mm, y - 12 * mm, company.adresse)
    c.drawString(20 * mm, y - 18 * mm, f"{company.code_postal} {company.ville}")
    
    # Tableau
    y -= 40 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, "Désignation")
    c.drawString(140 * mm, y, "Montant")
    
    c.line(20 * mm, y - 2 * mm, 180 * mm, y - 2 * mm)
    
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    services = [
        "Prestation de conseil",
        "Analyse et développement",
        "Support technique",
        "Formation équipe",
        "Maintenance annuelle",
    ]
    service = random.choice(services)
    c.drawString(20 * mm, y, service)
    c.drawString(140 * mm, y, f"{ht:.2f} €")
    
    # Totaux
    y -= 25 * mm
    c.drawString(100 * mm, y, "Total HT :")
    c.drawString(150 * mm, y, f"{ht:.2f} €")
    y -= 8 * mm
    c.drawString(100 * mm, y, f"TVA ({int(tva_rate*100) if tva_rate in TVA_RATES else '?'}%) :")
    c.drawString(150 * mm, y, f"{tva:.2f} €")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100 * mm, y, "Total TTC :")
    c.drawString(150 * mm, y, f"{ttc:.2f} €")
    
    # Mentions légales
    y -= 30 * mm
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_GRAY if scenario == "valid" else COLOR_RED)
    c.drawString(20 * mm, y, f"SIRET : {siret}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"TVA Intra : {tva_intra}")
    y -= 5 * mm
    c.drawString(20 * mm, y, f"IBAN : {iban}   BIC : {company.bic}")
    
    c.save()
    
    return {
        "document_id": doc_id,
        "doc_type": "facture",
        "scenario": scenario,
        "expected_anomalies": expected_anomalies,
        "entities": {
            "siret": siret,
            "siren": siret[:9],
            "raison_sociale": company.raison_sociale,
            "montant_ht": ht,
            "tva": tva,
            "montant_ttc": ttc,
            "iban": iban,
            "tva_intra": tva_intra,
            "date_emission": date_emission.strftime("%d/%m/%Y"),
        },
    }


def gen_devis(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> dict:
    """
    Génère un devis PDF.
    
    Scenarios:
        - valid: Devis correct
        - expired: Devis dont la validité est dépassée
        - tva_error: TVA ratio illégal
        - ttc_error: TTC ≠ HT + TVA
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    
    ht = round(random.uniform(1000, 50000), 2)
    tva_rate = random.choice(TVA_RATES)
    expected_anomalies = []
    
    date_emission = date.today() - timedelta(days=random.randint(30, 60))
    
    if scenario == "expired":
        date_validite = date.today() - timedelta(days=random.randint(10, 30))
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "DEVIS_EXPIRE", "severity": "WARNING"})
    elif scenario == "tva_error":
        date_validite = date.today() + timedelta(days=60)
        tva = round(ht * 0.08, 2)  # ratio 8% illégal
        expected_anomalies.append({"rule_id": "TVA_CALCUL_ERROR", "severity": "ERROR"})
    elif scenario == "ttc_error":
        date_validite = date.today() + timedelta(days=60)
        tva = round(ht * tva_rate, 2)
        ttc = round(ht + tva - 50, 2)  # TTC faux
        expected_anomalies.append({"rule_id": "TTC_CALCUL_ERROR", "severity": "ERROR"})
    else:  # valid
        date_validite = date.today() + timedelta(days=60)
        tva = round(ht * tva_rate, 2)
    
    if scenario != "ttc_error":
        ttc = round(ht + tva, 2)
    
    draw_header(c, "DEVIS", company)
    
    y = HEIGHT - 50 * mm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, f"Devis N° {doc_id}")
    
    y -= 12 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"Date d'émission : {date_emission.strftime('%d/%m/%Y')}")
    y -= 6 * mm
    validity_color = COLOR_RED if scenario == "expired" else COLOR_TEXT
    c.setFillColor(validity_color)
    c.drawString(20 * mm, y, f"Validité jusqu'au : {date_validite.strftime('%d/%m/%Y')}")
    
    y -= 20 * mm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, "Client :")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, y - 6 * mm, company.raison_sociale)
    c.drawString(20 * mm, y - 12 * mm, f"{company.code_postal} {company.ville}")
    
    # Tableau
    y -= 35 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, "Description")
    c.drawString(140 * mm, y, "Montant")
    c.line(20 * mm, y - 2 * mm, 180 * mm, y - 2 * mm)
    
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    prestations = [
        "Réalisation site web complet",
        "Audit et conseil stratégique",
        "Développement application mobile",
        "Migration infrastructure cloud",
        "Refonte système d'information",
    ]
    presta = random.choice(prestations)
    c.drawString(20 * mm, y, presta)
    c.drawString(140 * mm, y, f"{ht:.2f} €")
    
    y -= 25 * mm
    c.drawString(100 * mm, y, "Total HT :")
    c.drawString(150 * mm, y, f"{ht:.2f} €")
    y -= 8 * mm
    c.drawString(100 * mm, y, f"TVA ({int(tva_rate*100)}%) :")
    c.drawString(150 * mm, y, f"{tva:.2f} €")
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(100 * mm, y, "Total TTC :")
    c.drawString(150 * mm, y, f"{ttc:.2f} €")
    
    y -= 25 * mm
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_GRAY)
    c.drawString(20 * mm, y, f"SIRET : {company.siret}   Forme : {company.forme_juridique}")
    
    c.save()
    
    return {
        "document_id": doc_id,
        "doc_type": "devis",
        "scenario": scenario,
        "expected_anomalies": expected_anomalies,
        "entities": {
            "siret": company.siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "montant_ht": ht,
            "tva": tva,
            "montant_ttc": ttc,
            "date_validite": date_validite.strftime("%d/%m/%Y"),
        },
    }


def gen_attestation_urssaf(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> dict:
    """
    Génère une attestation URSSAF.
    
    Scenarios:
        - valid: Attestation valide
        - expired: Expirée
        - expiring_soon: Expire dans < 30 jours (WARNING)
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    expected_anomalies = []
    
    if scenario == "expired":
        date_emission = date.today() - timedelta(days=120)
        date_expiration = date.today() - timedelta(days=30)
        expected_anomalies.append({"rule_id": "ATTESTATION_EXPIREE", "severity": "ERROR"})
    elif scenario == "expiring_soon":
        date_emission = date.today() - timedelta(days=60)
        date_expiration = date.today() + timedelta(days=15)
        expected_anomalies.append({"rule_id": "ATTESTATION_EXPIREE", "severity": "WARNING"})
    else:  # valid
        date_emission = date.today() - timedelta(days=30)
        date_expiration = date.today() + timedelta(days=150)
    
    # En-tête URSSAF
    c.setFillColor(COLOR_DARK)
    c.rect(0, HEIGHT - 45 * mm, WIDTH, 45 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(20 * mm, HEIGHT - 22 * mm, "URSSAF")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, HEIGHT - 32 * mm, "Union de Recouvrement des cotisations")
    c.drawString(20 * mm, HEIGHT - 38 * mm, "de Sécurité Sociale et d'Allocations Familiales")
    
    y = HEIGHT - 65 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(WIDTH / 2, y, "Attestation de Vigilance")
    
    y -= 25 * mm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(COLOR_TEXT)
    c.drawString(30 * mm, y, "IDENTIFICATION DE L'ENTREPRISE")
    c.line(30 * mm, y - 2 * mm, 170 * mm, y - 2 * mm)
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, f"Raison Sociale : {company.raison_sociale}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"SIREN : {company.siren}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"SIRET : {company.siret}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"Adresse : {company.adresse}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"          {company.code_postal} {company.ville}")
    
    y -= 25 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "VALIDITÉ")
    c.line(30 * mm, y - 2 * mm, 170 * mm, y - 2 * mm)
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.drawString(30 * mm, y, f"Date d'émission : {date_emission.strftime('%d/%m/%Y')}")
    y -= 10 * mm
    
    if scenario == "expired":
        c.setFillColor(COLOR_RED)
        c.setFont("Helvetica-Bold", 10)
    elif scenario == "expiring_soon":
        c.setFillColor(COLOR_ORANGE)
        c.setFont("Helvetica-Bold", 10)
    
    c.drawString(30 * mm, y, f"Date d'expiration : {date_expiration.strftime('%d/%m/%Y')}")
    
    y -= 30 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_GRAY)
    text = "Cette attestation certifie que l'entreprise est à jour de ses obligations"
    c.drawString(30 * mm, y, text)
    c.drawString(30 * mm, y - 5 * mm, "déclaratives et de paiement envers l'URSSAF.")
    
    # Numéro de sécurité (fictif)
    y -= 25 * mm
    c.setFont("Helvetica", 8)
    c.drawString(30 * mm, y, f"N° Attestation : ATT-{doc_id}-{date_emission.strftime('%Y%m%d')}")
    
    c.save()
    
    return {
        "document_id": doc_id,
        "doc_type": "attestation_urssaf",
        "scenario": scenario,
        "expected_anomalies": expected_anomalies,
        "entities": {
            "siret": company.siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "date_emission": date_emission.strftime("%d/%m/%Y"),
            "date_expiration": date_expiration.strftime("%d/%m/%Y"),
        },
    }


def gen_kbis(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> dict:
    """
    Génère un extrait Kbis.
    
    Scenarios:
        - valid: Kbis récent (< 90 jours)
        - expired: Kbis périmé (> 90 jours)
        - siret_invalid: SIRET invalide
        - tva_intra_invalid: TVA intra invalide
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    expected_anomalies = []
    siret = company.siret
    tva_intra = company.tva_intra
    
    if scenario == "expired":
        date_emission = date.today() - timedelta(days=120)
        expected_anomalies.append({"rule_id": "KBIS_PERIME", "severity": "WARNING"})
    elif scenario == "siret_invalid":
        date_emission = date.today() - timedelta(days=15)
        siret = create_invalid_siret()
        expected_anomalies.append({"rule_id": "SIRET_FORMAT_INVALIDE", "severity": "ERROR"})
    elif scenario == "tva_intra_invalid":
        date_emission = date.today() - timedelta(days=10)
        tva_intra = create_invalid_tva_intra()
        expected_anomalies.append({"rule_id": "TVA_INTRA_INVALIDE", "severity": "WARNING"})
    else:  # valid
        date_emission = date.today() - timedelta(days=random.randint(5, 60))
    
    # En-tête officiel
    c.setFillColor(COLOR_DARK)
    c.rect(0, HEIGHT - 40 * mm, WIDTH, 40 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20 * mm, HEIGHT - 18 * mm, "EXTRAIT K-BIS")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, HEIGHT - 28 * mm, "Greffe du Tribunal de Commerce")
    c.drawString(20 * mm, HEIGHT - 34 * mm, f"de {company.ville}")
    
    y = HEIGHT - 60 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "IDENTIFICATION DE LA PERSONNE MORALE")
    c.line(20 * mm, y - 2 * mm, 180 * mm, y - 2 * mm)
    
    y -= 18 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"Dénomination : {company.raison_sociale}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"Forme juridique : {company.forme_juridique}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIREN : {company.siren}")
    y -= 8 * mm
    
    if scenario == "siret_invalid":
        c.setFillColor(COLOR_RED)
    c.drawString(20 * mm, y, f"SIRET (siège) : {siret}")
    c.setFillColor(COLOR_TEXT)
    
    y -= 8 * mm
    if scenario == "tva_intra_invalid":
        c.setFillColor(COLOR_RED)
    c.drawString(20 * mm, y, f"N° TVA Intracommunautaire : {tva_intra}")
    c.setFillColor(COLOR_TEXT)
    
    y -= 15 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, "SIÈGE SOCIAL")
    c.line(20 * mm, y - 2 * mm, 180 * mm, y - 2 * mm)
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"Adresse : {company.adresse}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"          {company.code_postal} {company.ville}")
    
    y -= 25 * mm
    c.setFont("Helvetica-Bold", 10)
    if scenario == "expired":
        c.setFillColor(COLOR_RED)
        c.drawString(20 * mm, y, f"Date de délivrance : {date_emission.strftime('%d/%m/%Y')}")
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y - 8 * mm, "(Ce document date de plus de 90 jours)")
    else:
        c.setFillColor(COLOR_TEXT)
        c.drawString(20 * mm, y, f"Date de délivrance : {date_emission.strftime('%d/%m/%Y')}")
    
    c.save()
    
    return {
        "document_id": doc_id,
        "doc_type": "kbis",
        "scenario": scenario,
        "expected_anomalies": expected_anomalies,
        "entities": {
            "siret": siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "tva_intra": tva_intra,
            "date_emission": date_emission.strftime("%d/%m/%Y"),
        },
    }


def gen_rib(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> dict:
    """
    Génère un RIB.
    
    Scenarios:
        - valid: RIB correct
        - iban_invalid: IBAN invalide
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    expected_anomalies = []
    iban = company.iban
    
    if scenario == "iban_invalid":
        iban = create_invalid_iban()
        expected_anomalies.append({"rule_id": "IBAN_FORMAT_INVALIDE", "severity": "ERROR"})
    
    draw_header(c, "RELEVÉ D'IDENTITÉ BANCAIRE", company)
    
    y = HEIGHT - 55 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, "Titulaire du compte")
    c.line(20 * mm, y - 2 * mm, 120 * mm, y - 2 * mm)
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, company.raison_sociale)
    y -= 8 * mm
    c.drawString(20 * mm, y, company.adresse)
    y -= 8 * mm
    c.drawString(20 * mm, y, f"{company.code_postal} {company.ville}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"SIRET : {company.siret}")
    
    y -= 25 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(COLOR_DARK)
    c.drawString(20 * mm, y, "Coordonnées bancaires")
    c.line(20 * mm, y - 2 * mm, 120 * mm, y - 2 * mm)
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    if scenario == "iban_invalid":
        c.setFillColor(COLOR_RED)
    else:
        c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"IBAN : {iban}")
    
    y -= 10 * mm
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"BIC : {company.bic}")
    
    # Cadre décoratif
    c.setStrokeColor(COLOR_GRAY)
    c.rect(15 * mm, y - 10 * mm, 170 * mm, 60 * mm, stroke=1, fill=0)
    
    c.save()
    
    return {
        "document_id": doc_id,
        "doc_type": "rib",
        "scenario": scenario,
        "expected_anomalies": expected_anomalies,
        "entities": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "iban": iban,
            "bic": company.bic,
        },
    }


def gen_mismatch_pair(
    output_dir: Path,
    company1: RealCompany,
    company2: RealCompany,
    mismatch_type: str,
    pair_id: str,
) -> List[dict]:
    """
    Génère une paire de documents avec mismatch inter-documents.
    
    mismatch_type:
        - siret: SIRET_MISMATCH
        - raison_sociale: RAISON_SOCIALE_MISMATCH
        - iban: IBAN_MISMATCH
    """
    results = []
    batch_group = f"MISMATCH-{mismatch_type.upper()}-{pair_id}"
    
    if mismatch_type == "siret":
        # Même raison sociale mais SIRET différents
        rs = company1.raison_sociale
        
        # Facture
        path1 = str(output_dir / f"FAC-MISMATCH-SIRET-{pair_id}-A.pdf")
        c = canvas.Canvas(path1, pagesize=A4)
        draw_header(c, "FACTURE")
        y = HEIGHT - 50 * mm
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(COLOR_DARK)
        c.drawString(20 * mm, y, f"Facture N° FAC-MISMATCH-SIRET-{pair_id}-A")
        y -= 15 * mm
        c.setFont("Helvetica", 10)
        c.setFillColor(COLOR_TEXT)
        c.drawString(20 * mm, y, rs)
        y -= 8 * mm
        c.drawString(20 * mm, y, f"SIRET : {company1.siret}")
        y -= 30 * mm
        c.drawString(100 * mm, y, "Total TTC : 5 000.00 €")
        c.save()
        
        results.append({
            "document_id": f"FAC-MISMATCH-SIRET-{pair_id}-A",
            "doc_type": "facture",
            "scenario": "siret_mismatch",
            "expected_anomalies": [{"rule_id": "SIRET_MISMATCH", "severity": "ERROR"}],
            "batch_group": batch_group,
            "entities": {
                "siret": company1.siret,
                "raison_sociale": rs,
                "montant_ttc": 5000.00,
            },
        })
        
        # URSSAF avec SIRET différent
        path2 = str(output_dir / f"URSSAF-MISMATCH-SIRET-{pair_id}-B.pdf")
        c2 = canvas.Canvas(path2, pagesize=A4)
        c2.setFillColor(COLOR_DARK)
        c2.rect(0, HEIGHT - 40 * mm, WIDTH, 40 * mm, fill=1, stroke=0)
        c2.setFillColor(colors.white)
        c2.setFont("Helvetica-Bold", 22)
        c2.drawString(20 * mm, HEIGHT - 25 * mm, "URSSAF")
        y = HEIGHT - 60 * mm
        c2.setFillColor(COLOR_TEXT)
        c2.setFont("Helvetica", 10)
        c2.drawString(20 * mm, y, f"Raison Sociale : {rs}")
        y -= 10 * mm
        c2.setFillColor(COLOR_RED)
        c2.drawString(20 * mm, y, f"SIRET : {company2.siret}")  # SIRET différent !
        exp = date.today() + timedelta(days=180)
        y -= 20 * mm
        c2.setFillColor(COLOR_TEXT)
        c2.drawString(20 * mm, y, f"Validité : {exp.strftime('%d/%m/%Y')}")
        c2.save()
        
        results.append({
            "document_id": f"URSSAF-MISMATCH-SIRET-{pair_id}-B",
            "doc_type": "attestation_urssaf",
            "scenario": "siret_mismatch",
            "expected_anomalies": [{"rule_id": "SIRET_MISMATCH", "severity": "ERROR"}],
            "batch_group": batch_group,
            "entities": {
                "siret": company2.siret,
                "raison_sociale": rs,
                "date_expiration": exp.strftime("%d/%m/%Y"),
            },
        })
    
    elif mismatch_type == "raison_sociale":
        # Même SIRET mais raisons sociales différentes
        siret = company1.siret
        rs1 = company1.raison_sociale
        rs2 = "ENTREPRISE COMPLETEMENT DIFFERENTE SARL"
        
        # Facture
        path1 = str(output_dir / f"FAC-MISMATCH-RS-{pair_id}-A.pdf")
        c = canvas.Canvas(path1, pagesize=A4)
        draw_header(c, "FACTURE")
        y = HEIGHT - 50 * mm
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(COLOR_DARK)
        c.drawString(20 * mm, y, f"Facture N° FAC-MISMATCH-RS-{pair_id}-A")
        y -= 15 * mm
        c.setFont("Helvetica", 10)
        c.setFillColor(COLOR_TEXT)
        c.drawString(20 * mm, y, rs1)
        y -= 8 * mm
        c.drawString(20 * mm, y, f"SIRET : {siret}")
        y -= 30 * mm
        c.drawString(100 * mm, y, "Total TTC : 3 500.00 €")
        c.save()
        
        results.append({
            "document_id": f"FAC-MISMATCH-RS-{pair_id}-A",
            "doc_type": "facture",
            "scenario": "raison_sociale_mismatch",
            "expected_anomalies": [{"rule_id": "RAISON_SOCIALE_MISMATCH", "severity": "WARNING"}],
            "batch_group": batch_group,
            "entities": {
                "siret": siret,
                "raison_sociale": rs1,
            },
        })
        
        # Kbis avec RS différente
        path2 = str(output_dir / f"KBIS-MISMATCH-RS-{pair_id}-B.pdf")
        c2 = canvas.Canvas(path2, pagesize=A4)
        c2.setFillColor(COLOR_DARK)
        c2.rect(0, HEIGHT - 35 * mm, WIDTH, 35 * mm, fill=1, stroke=0)
        c2.setFillColor(colors.white)
        c2.setFont("Helvetica-Bold", 20)
        c2.drawString(20 * mm, HEIGHT - 20 * mm, "EXTRAIT K-BIS")
        date_emission = date.today() - timedelta(days=10)
        y = HEIGHT - 55 * mm
        c2.setFont("Helvetica", 10)
        c2.setFillColor(COLOR_RED)
        c2.drawString(20 * mm, y, f"Dénomination : {rs2}")  # RS différente !
        y -= 8 * mm
        c2.setFillColor(COLOR_TEXT)
        c2.drawString(20 * mm, y, f"SIRET : {siret}")
        y -= 8 * mm
        c2.drawString(20 * mm, y, f"Date : {date_emission.strftime('%d/%m/%Y')}")
        c2.save()
        
        results.append({
            "document_id": f"KBIS-MISMATCH-RS-{pair_id}-B",
            "doc_type": "kbis",
            "scenario": "raison_sociale_mismatch",
            "expected_anomalies": [{"rule_id": "RAISON_SOCIALE_MISMATCH", "severity": "WARNING"}],
            "batch_group": batch_group,
            "entities": {
                "siret": siret,
                "raison_sociale": rs2,
                "date_emission": date_emission.strftime("%d/%m/%Y"),
            },
        })
    
    elif mismatch_type == "iban":
        # Même SIRET mais IBAN différents
        siret = company1.siret
        rs = company1.raison_sociale
        iban1 = company1.iban
        iban2 = company2.iban
        
        # Facture
        path1 = str(output_dir / f"FAC-MISMATCH-IBAN-{pair_id}-A.pdf")
        c = canvas.Canvas(path1, pagesize=A4)
        draw_header(c, "FACTURE")
        y = HEIGHT - 50 * mm
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(COLOR_DARK)
        c.drawString(20 * mm, y, f"Facture N° FAC-MISMATCH-IBAN-{pair_id}-A")
        y -= 15 * mm
        c.setFont("Helvetica", 10)
        c.setFillColor(COLOR_TEXT)
        c.drawString(20 * mm, y, rs)
        y -= 8 * mm
        c.drawString(20 * mm, y, f"SIRET : {siret}")
        y -= 8 * mm
        c.drawString(20 * mm, y, f"IBAN : {iban1}")
        y -= 30 * mm
        c.drawString(100 * mm, y, "Total TTC : 2 800.00 €")
        c.save()
        
        results.append({
            "document_id": f"FAC-MISMATCH-IBAN-{pair_id}-A",
            "doc_type": "facture",
            "scenario": "iban_mismatch",
            "expected_anomalies": [{"rule_id": "IBAN_MISMATCH", "severity": "WARNING"}],
            "batch_group": batch_group,
            "entities": {
                "siret": siret,
                "raison_sociale": rs,
                "iban": iban1,
            },
        })
        
        # RIB avec IBAN différent
        path2 = str(output_dir / f"RIB-MISMATCH-IBAN-{pair_id}-B.pdf")
        c2 = canvas.Canvas(path2, pagesize=A4)
        draw_header(c2, "RELEVÉ D'IDENTITÉ BANCAIRE")
        y = HEIGHT - 55 * mm
        c2.setFont("Helvetica-Bold", 12)
        c2.setFillColor(COLOR_DARK)
        c2.drawString(20 * mm, y, "Titulaire")
        y -= 12 * mm
        c2.setFont("Helvetica", 10)
        c2.setFillColor(COLOR_TEXT)
        c2.drawString(20 * mm, y, rs)
        y -= 8 * mm
        c2.drawString(20 * mm, y, f"SIRET : {siret}")
        y -= 20 * mm
        c2.setFillColor(COLOR_RED)
        c2.drawString(20 * mm, y, f"IBAN : {iban2}")  # IBAN différent !
        c2.save()
        
        results.append({
            "document_id": f"RIB-MISMATCH-IBAN-{pair_id}-B",
            "doc_type": "rib",
            "scenario": "iban_mismatch",
            "expected_anomalies": [{"rule_id": "IBAN_MISMATCH", "severity": "WARNING"}],
            "batch_group": batch_group,
            "entities": {
                "siret": siret,
                "raison_sociale": rs,
                "iban": iban2,
            },
        })
    
    return results


# ═══════════════════════════════════════════════════════════════════════════
# Programme principal
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Génère des documents de test avec entreprises réelles."
    )
    parser.add_argument(
        "--output", type=str, default="./output/test_real",
        help="Dossier de sortie"
    )
    parser.add_argument(
        "--scenario", type=str, default="all",
        choices=["all", "valid", "errors"],
        help="Types de scénarios à générer"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Graine aléatoire"
    )
    args = parser.parse_args()
    
    random.seed(args.seed)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(" GÉNÉRATION DE DOCUMENTS DE TEST — ENTREPRISES RÉELLES ")
    print("=" * 70)
    print(f" Sortie : {output_dir.resolve()}")
    print(f" Entreprises disponibles : {len(REAL_COMPANIES)}")
    print("=" * 70)
    
    all_results = []
    doc_counter = 0
    
    def add_doc(label, result):
        nonlocal doc_counter
        if isinstance(result, list):
            for r in result:
                all_results.append(r)
            print(f"  [{doc_counter+1:>2}-{doc_counter+len(result):>2}] {label} → {len(result)} docs")
            doc_counter += len(result)
        else:
            doc_counter += 1
            all_results.append(result)
            anomalies = result.get("expected_anomalies", [])
            status = "✓" if not anomalies else f"✗ {len(anomalies)} anomalie(s)"
            print(f"  [{doc_counter:>2}] {label} — {status}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. DOCUMENTS VALIDES (aucune anomalie)
    # ═══════════════════════════════════════════════════════════════════════
    
    if args.scenario in ("all", "valid"):
        print("\n─── DOCUMENTS VALIDES ───────────────────────────────────────")
        
        for i, company in enumerate(REAL_COMPANIES[:5]):
            # Facture valide
            add_doc(
                f"Facture {company.raison_sociale[:20]}",
                gen_facture(
                    str(output_dir / f"FAC-VALID-{i+1:03d}.pdf"),
                    company, f"FAC-VALID-{i+1:03d}", "valid"
                )
            )
            
            # Devis valide
            add_doc(
                f"Devis {company.raison_sociale[:20]}",
                gen_devis(
                    str(output_dir / f"DEV-VALID-{i+1:03d}.pdf"),
                    company, f"DEV-VALID-{i+1:03d}", "valid"
                )
            )
            
            # URSSAF valide
            add_doc(
                f"URSSAF {company.raison_sociale[:20]}",
                gen_attestation_urssaf(
                    str(output_dir / f"URSSAF-VALID-{i+1:03d}.pdf"),
                    company, f"URSSAF-VALID-{i+1:03d}", "valid"
                )
            )
            
            # Kbis valide
            add_doc(
                f"Kbis {company.raison_sociale[:20]}",
                gen_kbis(
                    str(output_dir / f"KBIS-VALID-{i+1:03d}.pdf"),
                    company, f"KBIS-VALID-{i+1:03d}", "valid"
                )
            )
            
            # RIB valide
            add_doc(
                f"RIB {company.raison_sociale[:20]}",
                gen_rib(
                    str(output_dir / f"RIB-VALID-{i+1:03d}.pdf"),
                    company, f"RIB-VALID-{i+1:03d}", "valid"
                )
            )
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. DOCUMENTS AVEC ERREURS UNITAIRES
    # ═══════════════════════════════════════════════════════════════════════
    
    if args.scenario in ("all", "errors"):
        print("\n─── ERREURS UNITAIRES ───────────────────────────────────────")
        
        co = REAL_COMPANIES
        
        # TVA_CALCUL_ERROR
        add_doc("Facture TVA illégale (CARREFOUR)",
                gen_facture(str(output_dir / "FAC-ERR-TVA-001.pdf"),
                           co[0], "FAC-ERR-TVA-001", "tva_error"))
        add_doc("Devis TVA illégale (TOTAL)",
                gen_devis(str(output_dir / "DEV-ERR-TVA-001.pdf"),
                         co[1], "DEV-ERR-TVA-001", "tva_error"))
        
        # TTC_CALCUL_ERROR
        add_doc("Facture TTC faux (ORANGE)",
                gen_facture(str(output_dir / "FAC-ERR-TTC-001.pdf"),
                           co[2], "FAC-ERR-TTC-001", "ttc_error"))
        add_doc("Devis TTC faux (SNCF)",
                gen_devis(str(output_dir / "DEV-ERR-TTC-001.pdf"),
                         co[3], "DEV-ERR-TTC-001", "ttc_error"))
        
        # SIRET_FORMAT_INVALIDE
        add_doc("Facture SIRET invalide (AIR FRANCE)",
                gen_facture(str(output_dir / "FAC-ERR-SIRET-001.pdf"),
                           co[4], "FAC-ERR-SIRET-001", "siret_invalid"))
        add_doc("Kbis SIRET invalide (RENAULT)",
                gen_kbis(str(output_dir / "KBIS-ERR-SIRET-001.pdf"),
                        co[5], "KBIS-ERR-SIRET-001", "siret_invalid"))
        
        # IBAN_FORMAT_INVALIDE
        add_doc("Facture IBAN invalide (DANONE)",
                gen_facture(str(output_dir / "FAC-ERR-IBAN-001.pdf"),
                           co[6], "FAC-ERR-IBAN-001", "iban_invalid"))
        add_doc("RIB IBAN invalide (BOUYGUES)",
                gen_rib(str(output_dir / "RIB-ERR-IBAN-001.pdf"),
                       co[7], "RIB-ERR-IBAN-001", "iban_invalid"))
        
        # TVA_INTRA_INVALIDE
        add_doc("Facture TVA intra invalide (ENGIE)",
                gen_facture(str(output_dir / "FAC-ERR-TVA-INTRA-001.pdf"),
                           co[8], "FAC-ERR-TVA-INTRA-001", "tva_intra_invalid"))
        add_doc("Kbis TVA intra invalide (SOCIETE GENERALE)",
                gen_kbis(str(output_dir / "KBIS-ERR-TVA-INTRA-001.pdf"),
                        co[9], "KBIS-ERR-TVA-INTRA-001", "tva_intra_invalid"))
        
        # ATTESTATION_EXPIREE
        add_doc("URSSAF expirée (CARREFOUR)",
                gen_attestation_urssaf(str(output_dir / "URSSAF-ERR-EXP-001.pdf"),
                                      co[0], "URSSAF-ERR-EXP-001", "expired"))
        add_doc("URSSAF expire bientôt (TOTAL)",
                gen_attestation_urssaf(str(output_dir / "URSSAF-WARN-EXP-001.pdf"),
                                      co[1], "URSSAF-WARN-EXP-001", "expiring_soon"))
        
        # KBIS_PERIME
        add_doc("Kbis périmé (ORANGE)",
                gen_kbis(str(output_dir / "KBIS-ERR-PER-001.pdf"),
                        co[2], "KBIS-ERR-PER-001", "expired"))
        
        # DEVIS_EXPIRE
        add_doc("Devis expiré (SNCF)",
                gen_devis(str(output_dir / "DEV-ERR-EXP-001.pdf"),
                         co[3], "DEV-ERR-EXP-001", "expired"))
        
        # MULTI-ERREURS
        add_doc("Facture multi-erreurs (AIR FRANCE)",
                gen_facture(str(output_dir / "FAC-MULTI-001.pdf"),
                           co[4], "FAC-MULTI-001", "multi_error"))
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. ERREURS INTER-DOCUMENTS
    # ═══════════════════════════════════════════════════════════════════════
    
    if args.scenario in ("all", "errors"):
        print("\n─── ERREURS INTER-DOCUMENTS ─────────────────────────────────")
        
        co = REAL_COMPANIES
        
        # SIRET_MISMATCH
        add_doc("SIRET mismatch (CARREFOUR vs TOTAL)",
                gen_mismatch_pair(output_dir, co[0], co[1], "siret", "001"))
        
        # RAISON_SOCIALE_MISMATCH
        add_doc("Raison sociale mismatch (ORANGE)",
                gen_mismatch_pair(output_dir, co[2], co[2], "raison_sociale", "001"))
        
        # IBAN_MISMATCH
        add_doc("IBAN mismatch (SNCF vs AIR FRANCE)",
                gen_mismatch_pair(output_dir, co[3], co[4], "iban", "001"))
    
    # ═══════════════════════════════════════════════════════════════════════
    # Sauvegarde des labels
    # ═══════════════════════════════════════════════════════════════════════
    
    labels_file = output_dir / "test_real_labels.json"
    with open(labels_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # ═══════════════════════════════════════════════════════════════════════
    # Résumé
    # ═══════════════════════════════════════════════════════════════════════
    
    print("\n" + "=" * 70)
    print(f" ✓ {len(all_results)} documents générés dans : {output_dir}")
    print(f" ✓ Labels sauvegardés dans : {labels_file}")
    print("=" * 70)
    
    # Stats par anomalie
    anomaly_counts = {}
    valid_count = 0
    for doc in all_results:
        anomalies = doc.get("expected_anomalies", [])
        if not anomalies:
            valid_count += 1
        for a in anomalies:
            key = f"{a['rule_id']} ({a['severity']})"
            anomaly_counts[key] = anomaly_counts.get(key, 0) + 1
    
    print("\n📋 COUVERTURE DES RÈGLES DE VALIDATION :")
    print("-" * 50)
    for key in sorted(anomaly_counts.keys()):
        print(f"  ✗ {key:45s} × {anomaly_counts[key]}")
    print(f"\n  ✓ Documents valides (aucune anomalie)       × {valid_count}")
    
    # Stats par type de document
    type_counts = {}
    for doc in all_results:
        t = doc.get("doc_type", "?")
        type_counts[t] = type_counts.get(t, 0) + 1
    
    print("\n📄 TYPES DE DOCUMENTS GÉNÉRÉS :")
    print("-" * 50)
    for t, cnt in sorted(type_counts.items()):
        print(f"  {t:30s} × {cnt}")
    
    # Stats par entreprise
    company_counts = {}
    for doc in all_results:
        rs = doc.get("entities", {}).get("raison_sociale", "?")
        if rs and rs != "ENTREPRISE COMPLETEMENT DIFFERENTE SARL":
            company_counts[rs[:25]] = company_counts.get(rs[:25], 0) + 1
    
    print("\n🏢 ENTREPRISES UTILISÉES :")
    print("-" * 50)
    for name, cnt in sorted(company_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"  {name:30s} × {cnt}")
    
    # Batch groups
    groups = set()
    for doc in all_results:
        g = doc.get("batch_group")
        if g:
            groups.add(g)
    
    if groups:
        print(f"\n🔗 GROUPES INTER-DOCUMENTS : {len(groups)}")
        for g in sorted(groups):
            members = [d["document_id"] for d in all_results if d.get("batch_group") == g]
            print(f"  {g}: {', '.join(members)}")
    
    print("\n" + "=" * 70)
    print(f" TOTAL : {len(all_results)} documents PDF générés")
    print("=" * 70)


if __name__ == "__main__":
    main()
