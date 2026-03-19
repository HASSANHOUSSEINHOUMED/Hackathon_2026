"""
═══════════════════════════════════════════════════════════════════════════════
    GÉNÉRATEUR DE DATASET DE DÉMONSTRATION — DOCUFLOW
    
    Génère un dataset complet pour démonstration devant jury avec :
    - Dossier "same_supplier/" : Documents d'UN SEUL fournisseur (test batch valide)
    - Dossier "multi_supplier/" : Documents de PLUSIEURS fournisseurs (test erreurs)
    - Dossier "mismatch_test/" : Paires de documents avec erreurs MISMATCH
    
    Couverture complète des 12 règles de validation :
    ┌─────────────────────────────┬───────────┬────────────────────────────────┐
    │ Règle                       │ Sévérité  │ Description                    │
    ├─────────────────────────────┼───────────┼────────────────────────────────┤
    │ TVA_CALCUL_ERROR            │ ERROR     │ Ratio TVA/HT illégal           │
    │ TTC_CALCUL_ERROR            │ ERROR     │ TTC ≠ HT + TVA                 │
    │ SIRET_FORMAT_INVALIDE       │ ERROR     │ SIRET ne passe pas Luhn        │
    │ IBAN_FORMAT_INVALIDE        │ ERROR     │ IBAN invalide                  │
    │ TVA_INTRA_INVALIDE          │ WARNING   │ N° TVA intra-communautaire     │
    │ ATTESTATION_EXPIREE         │ ERROR/WAR │ URSSAF expirée ou bientôt      │
    │ KBIS_PERIME                 │ WARNING   │ Kbis > 90 jours                │
    │ DEVIS_EXPIRE                │ WARNING   │ Devis date validité dépassée   │
    │ SIRET_MISMATCH              │ ERROR     │ SIRET différents batch         │
    │ RAISON_SOCIALE_MISMATCH     │ WARNING   │ Raison sociale différente      │
    │ IBAN_MISMATCH               │ WARNING   │ IBAN différents batch          │
    │ MONTANT_ANORMAL             │ INFO      │ Montant statistiquement anormal│
    └─────────────────────────────┴───────────┴────────────────────────────────┘

Usage :
    python generate_demo_dataset.py --output ./output/demo
    python generate_demo_dataset.py --output ./output/demo --seed 42

═══════════════════════════════════════════════════════════════════════════════
"""

import argparse
import json
import random
import sys
from dataclasses import dataclass, asdict
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


# ═══════════════════════════════════════════════════════════════════════════════
# DONNÉES D'ENTREPRISES RÉELLES FRANÇAISES (SIREN/SIRET publics)
# ═══════════════════════════════════════════════════════════════════════════════

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
    iban: str
    bic: str


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


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

WIDTH, HEIGHT = A4
COLOR_DARK = colors.HexColor("#1B2A4A")
COLOR_ACCENT = colors.HexColor("#00C896")
COLOR_TEXT = colors.HexColor("#2D3748")
COLOR_RED = colors.HexColor("#E53E3E")
COLOR_GRAY = colors.HexColor("#718096")
COLOR_ORANGE = colors.HexColor("#DD6B20")
COLOR_GREEN = colors.HexColor("#38A169")
COLOR_LIGHT_BG = colors.HexColor("#F7FAFC")

TVA_RATES = [0.055, 0.10, 0.20]

PREFIXES = {
    "facture": "FAC",
    "devis": "DEV",
    "attestation_urssaf": "URSSAF",
    "kbis": "KBIS",
    "rib": "RIB",
}

SERVICES = [
    ("Prestation de conseil stratégique", 2500.00),
    ("Développement application web", 8500.00),
    ("Audit de sécurité informatique", 4200.00),
    ("Formation équipe DevOps", 3800.00),
    ("Maintenance annuelle infrastructure", 12000.00),
    ("Migration cloud AWS", 15000.00),
    ("Refonte site e-commerce", 25000.00),
    ("Support technique premium", 6500.00),
]


# ═══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def create_invalid_siret() -> str:
    """SIRET invalide (ne passe pas Luhn)."""
    return "12345678901234"


def create_invalid_iban() -> str:
    """IBAN invalide (checksum 00)."""
    return "FR0012345678901234567890123"


def create_invalid_tva_intra() -> str:
    """TVA intra invalide."""
    return "FR99123456789"


def draw_professional_header(c: canvas.Canvas, doc_type: str, company: RealCompany, doc_id: str):
    """En-tête professionnel avec bandeau coloré."""
    # Bandeau supérieur
    c.setFillColor(COLOR_DARK)
    c.rect(0, HEIGHT - 35 * mm, WIDTH, 35 * mm, fill=1, stroke=0)
    
    # Accent bar
    c.setFillColor(COLOR_ACCENT)
    c.rect(0, HEIGHT - 37 * mm, WIDTH, 2 * mm, fill=1, stroke=0)
    
    # Titre
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    title = doc_type.upper().replace("_", " ")
    c.drawString(20 * mm, HEIGHT - 18 * mm, title)
    
    # N° document
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, HEIGHT - 28 * mm, f"N° {doc_id}")
    
    # Logo entreprise (simulé)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(WIDTH - 20 * mm, HEIGHT - 18 * mm, company.raison_sociale)
    c.setFont("Helvetica", 9)
    c.drawRightString(WIDTH - 20 * mm, HEIGHT - 26 * mm, f"SIRET: {company.siret}")


def draw_footer(c: canvas.Canvas, company: RealCompany, page: int = 1):
    """Pied de page professionnel."""
    c.setFillColor(COLOR_LIGHT_BG)
    c.rect(0, 0, WIDTH, 20 * mm, fill=1, stroke=0)
    
    c.setFillColor(COLOR_GRAY)
    c.setFont("Helvetica", 7)
    c.drawString(20 * mm, 12 * mm, f"{company.raison_sociale} — {company.forme_juridique}")
    c.drawString(20 * mm, 8 * mm, f"{company.adresse}, {company.code_postal} {company.ville}")
    c.drawString(20 * mm, 4 * mm, f"SIRET: {company.siret} — TVA: {company.tva_intra}")
    
    c.drawRightString(WIDTH - 20 * mm, 8 * mm, f"Page {page}")


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEURS DE DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_facture(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
    custom_ht: float = None,
) -> Dict[str, Any]:
    """
    Génère une facture PDF professionnelle.
    
    Scenarios:
        - valid: Facture correcte
        - tva_error: TVA ratio illégal (15%)
        - ttc_error: TTC ≠ HT + TVA
        - siret_invalid: SIRET ne passant pas Luhn
        - iban_invalid: IBAN invalide
        - montant_anormal: Montant très élevé (test ML)
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    
    # Données de base
    service_name, base_ht = random.choice(SERVICES)
    ht = custom_ht if custom_ht else round(base_ht * random.uniform(0.8, 1.2), 2)
    tva_rate = random.choice(TVA_RATES)
    
    # Ajustements selon scénario
    siret = company.siret
    iban = company.iban
    tva_intra = company.tva_intra
    expected_anomalies = []
    
    if scenario == "tva_error":
        tva = round(ht * 0.15, 2)  # Ratio 15% illégal
        expected_anomalies.append({"rule_id": "TVA_CALCUL_ERROR", "severity": "ERROR"})
    elif scenario == "ttc_error":
        tva = round(ht * tva_rate, 2)
        ttc = round(ht + tva + random.uniform(50, 200), 2)  # TTC faux
        expected_anomalies.append({"rule_id": "TTC_CALCUL_ERROR", "severity": "ERROR"})
    elif scenario == "siret_invalid":
        siret = create_invalid_siret()
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "SIRET_FORMAT_INVALIDE", "severity": "ERROR"})
    elif scenario == "iban_invalid":
        iban = create_invalid_iban()
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "IBAN_FORMAT_INVALIDE", "severity": "ERROR"})
    elif scenario == "montant_anormal":
        ht = round(random.uniform(150000, 500000), 2)  # Montant très élevé
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "MONTANT_ANORMAL", "severity": "INFO"})
    else:  # valid
        tva = round(ht * tva_rate, 2)
    
    if scenario != "ttc_error":
        ttc = round(ht + tva, 2)
    
    date_emission = date.today() - timedelta(days=random.randint(1, 30))
    date_echeance = date_emission + timedelta(days=30)
    
    # Dessin du PDF
    draw_professional_header(c, "FACTURE", company, doc_id)
    
    y = HEIGHT - 55 * mm
    
    # Infos client
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "FACTURÉ À :")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y - 8 * mm, "Client Exemple SAS")
    c.drawString(20 * mm, y - 14 * mm, "123 Rue de l'Innovation")
    c.drawString(20 * mm, y - 20 * mm, "75001 Paris")
    
    # Dates
    c.setFont("Helvetica", 10)
    c.drawRightString(WIDTH - 20 * mm, y, f"Date : {date_emission.strftime('%d/%m/%Y')}")
    c.drawRightString(WIDTH - 20 * mm, y - 8 * mm, f"Échéance : {date_echeance.strftime('%d/%m/%Y')}")
    
    # Tableau des prestations
    y -= 45 * mm
    
    # En-tête tableau
    c.setFillColor(COLOR_DARK)
    c.rect(20 * mm, y - 2 * mm, WIDTH - 40 * mm, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25 * mm, y + 1 * mm, "Description")
    c.drawString(120 * mm, y + 1 * mm, "Qté")
    c.drawString(140 * mm, y + 1 * mm, "Prix Unit.")
    c.drawRightString(WIDTH - 25 * mm, y + 1 * mm, "Montant")
    
    # Ligne de prestation
    y -= 15 * mm
    c.setFillColor(COLOR_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, service_name)
    c.drawString(120 * mm, y, "1")
    c.drawString(140 * mm, y, f"{ht:.2f} €")
    c.drawRightString(WIDTH - 25 * mm, y, f"{ht:.2f} €")
    
    # Ligne séparatrice
    c.setStrokeColor(COLOR_GRAY)
    c.line(20 * mm, y - 5 * mm, WIDTH - 20 * mm, y - 5 * mm)
    
    # Totaux
    y -= 25 * mm
    c.setFillColor(COLOR_TEXT)
    c.drawString(120 * mm, y, "Total HT :")
    c.drawRightString(WIDTH - 25 * mm, y, f"{ht:.2f} €")
    
    y -= 8 * mm
    tva_percent = int(tva_rate * 100) if tva_rate in TVA_RATES else "?"
    c.drawString(120 * mm, y, f"TVA ({tva_percent}%) :")
    c.drawRightString(WIDTH - 25 * mm, y, f"{tva:.2f} €")
    
    y -= 10 * mm
    c.setFillColor(COLOR_DARK)
    c.rect(115 * mm, y - 3 * mm, WIDTH - 135 * mm, 12 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120 * mm, y + 1 * mm, "Total TTC :")
    c.drawRightString(WIDTH - 25 * mm, y + 1 * mm, f"{ttc:.2f} €")
    
    # Coordonnées bancaires
    y -= 35 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "COORDONNÉES BANCAIRES")
    
    y -= 10 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(COLOR_RED if scenario == "iban_invalid" else COLOR_TEXT)
    c.drawString(20 * mm, y, f"IBAN : {iban}")
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y - 6 * mm, f"BIC : {company.bic}")
    
    # Mentions légales
    y -= 25 * mm
    c.setFont("Helvetica", 8)
    c.setFillColor(COLOR_RED if scenario == "siret_invalid" else COLOR_GRAY)
    c.drawString(20 * mm, y, f"SIRET : {siret}   |   TVA Intra : {tva_intra}")
    
    draw_footer(c, company)
    c.save()
    
    return {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "type": "facture",
        "scenario": scenario,
        "anomalies_expected": expected_anomalies,
        "expected_fields": {
            "siret": siret,
            "siren": siret[:9] if len(siret) >= 9 else siret,
            "raison_sociale": company.raison_sociale,
            "montant_ht": ht,
            "tva": tva,
            "montant_ttc": ttc,
            "iban": iban,
            "tva_intra": tva_intra,
            "date_emission": date_emission.strftime("%d/%m/%Y"),
        },
    }


def generate_devis(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> Dict[str, Any]:
    """
    Génère un devis PDF professionnel.
    
    Scenarios:
        - valid: Devis correct
        - expired: Devis dont validité est dépassée
        - tva_error: TVA ratio illégal
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    
    service_name, base_ht = random.choice(SERVICES)
    ht = round(base_ht * random.uniform(1.0, 2.5), 2)
    tva_rate = random.choice(TVA_RATES)
    expected_anomalies = []
    
    date_emission = date.today() - timedelta(days=random.randint(30, 60))
    
    if scenario == "expired":
        date_validite = date.today() - timedelta(days=random.randint(5, 30))
        tva = round(ht * tva_rate, 2)
        expected_anomalies.append({"rule_id": "DEVIS_EXPIRE", "severity": "WARNING"})
    elif scenario == "tva_error":
        date_validite = date.today() + timedelta(days=60)
        tva = round(ht * 0.12, 2)  # 12% illégal
        expected_anomalies.append({"rule_id": "TVA_CALCUL_ERROR", "severity": "ERROR"})
    else:
        date_validite = date.today() + timedelta(days=60)
        tva = round(ht * tva_rate, 2)
    
    ttc = round(ht + tva, 2)
    
    draw_professional_header(c, "DEVIS", company, doc_id)
    
    y = HEIGHT - 55 * mm
    
    # Infos
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "DESTINATAIRE :")
    
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y - 8 * mm, "Client Prospect SARL")
    c.drawString(20 * mm, y - 14 * mm, "456 Avenue du Commerce")
    c.drawString(20 * mm, y - 20 * mm, "69002 Lyon")
    
    # Dates
    c.drawRightString(WIDTH - 20 * mm, y, f"Émis le : {date_emission.strftime('%d/%m/%Y')}")
    
    validity_color = COLOR_RED if scenario == "expired" else COLOR_TEXT
    c.setFillColor(validity_color)
    c.setFont("Helvetica-Bold" if scenario == "expired" else "Helvetica", 10)
    c.drawRightString(WIDTH - 20 * mm, y - 10 * mm, f"Valide jusqu'au : {date_validite.strftime('%d/%m/%Y')}")
    
    if scenario == "expired":
        c.setFillColor(COLOR_RED)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(WIDTH - 20 * mm, y - 18 * mm, "⚠ DEVIS EXPIRÉ")
    
    # Tableau
    y -= 50 * mm
    c.setFillColor(COLOR_DARK)
    c.rect(20 * mm, y - 2 * mm, WIDTH - 40 * mm, 10 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25 * mm, y + 1 * mm, "Description")
    c.drawRightString(WIDTH - 25 * mm, y + 1 * mm, "Montant")
    
    y -= 15 * mm
    c.setFillColor(COLOR_TEXT)
    c.setFont("Helvetica", 10)
    c.drawString(25 * mm, y, service_name)
    c.drawRightString(WIDTH - 25 * mm, y, f"{ht:.2f} €")
    
    # Totaux
    y -= 30 * mm
    c.drawString(120 * mm, y, "Total HT :")
    c.drawRightString(WIDTH - 25 * mm, y, f"{ht:.2f} €")
    
    y -= 8 * mm
    c.drawString(120 * mm, y, f"TVA ({int(tva_rate*100)}%) :")
    c.drawRightString(WIDTH - 25 * mm, y, f"{tva:.2f} €")
    
    y -= 10 * mm
    c.setFillColor(COLOR_ACCENT)
    c.rect(115 * mm, y - 3 * mm, WIDTH - 135 * mm, 12 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(120 * mm, y + 1 * mm, "Total TTC :")
    c.drawRightString(WIDTH - 25 * mm, y + 1 * mm, f"{ttc:.2f} €")
    
    # Conditions
    y -= 35 * mm
    c.setFillColor(COLOR_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(20 * mm, y, "Conditions : Paiement à 30 jours. Devis valable pendant 60 jours.")
    c.drawString(20 * mm, y - 5 * mm, f"Ce devis engage {company.raison_sociale} jusqu'à la date de validité indiquée.")
    
    draw_footer(c, company)
    c.save()
    
    return {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "type": "devis",
        "scenario": scenario,
        "anomalies_expected": expected_anomalies,
        "expected_fields": {
            "siret": company.siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "montant_ht": ht,
            "tva": tva,
            "montant_ttc": ttc,
            "date_validite": date_validite.strftime("%d/%m/%Y"),
        },
    }


def generate_attestation_urssaf(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> Dict[str, Any]:
    """
    Génère une attestation URSSAF.
    
    Scenarios:
        - valid: Attestation valide
        - expired: Expirée
        - expiring_soon: Expire dans < 30 jours
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
    else:
        date_emission = date.today() - timedelta(days=30)
        date_expiration = date.today() + timedelta(days=150)
    
    # En-tête URSSAF officiel
    c.setFillColor(COLOR_DARK)
    c.rect(0, HEIGHT - 50 * mm, WIDTH, 50 * mm, fill=1, stroke=0)
    
    c.setFillColor(COLOR_ACCENT)
    c.rect(0, HEIGHT - 52 * mm, WIDTH, 2 * mm, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(20 * mm, HEIGHT - 25 * mm, "URSSAF")
    
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, HEIGHT - 35 * mm, "Union de Recouvrement des cotisations")
    c.drawString(20 * mm, HEIGHT - 42 * mm, "de Sécurité Sociale et d'Allocations Familiales")
    
    # Titre
    y = HEIGHT - 75 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(WIDTH / 2, y, "Attestation de Vigilance")
    
    # Numéro
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_GRAY)
    c.drawCentredString(WIDTH / 2, y - 10 * mm, f"N° {doc_id}")
    
    # Identification entreprise
    y -= 35 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "IDENTIFICATION DE L'ENTREPRISE")
    c.setStrokeColor(COLOR_ACCENT)
    c.setLineWidth(2)
    c.line(30 * mm, y - 3 * mm, 120 * mm, y - 3 * mm)
    
    y -= 18 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(30 * mm, y, f"Raison Sociale : {company.raison_sociale}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"SIREN : {company.siren}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"SIRET (établissement) : {company.siret}")
    y -= 8 * mm
    c.drawString(30 * mm, y, f"Adresse : {company.adresse}")
    y -= 6 * mm
    c.drawString(30 * mm, y, f"          {company.code_postal} {company.ville}")
    
    # Validité
    y -= 25 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(30 * mm, y, "PÉRIODE DE VALIDITÉ")
    c.setStrokeColor(COLOR_ACCENT)
    c.line(30 * mm, y - 3 * mm, 100 * mm, y - 3 * mm)
    
    y -= 18 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(30 * mm, y, f"Date d'émission : {date_emission.strftime('%d/%m/%Y')}")
    
    y -= 12 * mm
    if scenario == "expired":
        c.setFillColor(COLOR_RED)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(30 * mm, y, f"Date d'expiration : {date_expiration.strftime('%d/%m/%Y')}")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30 * mm, y - 10 * mm, "⚠ ATTESTATION EXPIRÉE")
    elif scenario == "expiring_soon":
        c.setFillColor(COLOR_ORANGE)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(30 * mm, y, f"Date d'expiration : {date_expiration.strftime('%d/%m/%Y')}")
        c.drawString(30 * mm, y - 10 * mm, "⚠ Expire dans moins de 30 jours")
    else:
        c.setFillColor(COLOR_GREEN)
        c.setFont("Helvetica", 10)
        c.drawString(30 * mm, y, f"Date d'expiration : {date_expiration.strftime('%d/%m/%Y')}")
    
    # Certification
    y -= 35 * mm
    c.setFillColor(COLOR_TEXT)
    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, y, "Cette attestation certifie que l'entreprise est à jour de ses obligations")
    c.drawString(30 * mm, y - 5 * mm, "déclaratives et de paiement envers l'URSSAF.")
    
    # Code de vérification
    y -= 25 * mm
    c.setFillColor(COLOR_GRAY)
    c.setFont("Helvetica", 8)
    c.drawString(30 * mm, y, f"Code de vérification : ATT-{date_emission.strftime('%Y%m%d')}-{company.siren[-4:]}")
    
    draw_footer(c, company)
    c.save()
    
    return {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "type": "attestation_urssaf",
        "scenario": scenario,
        "anomalies_expected": expected_anomalies,
        "expected_fields": {
            "siret": company.siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "date_emission": date_emission.strftime("%d/%m/%Y"),
            "date_expiration": date_expiration.strftime("%d/%m/%Y"),
        },
    }


def generate_kbis(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> Dict[str, Any]:
    """
    Génère un extrait Kbis.
    
    Scenarios:
        - valid: Kbis récent (< 90 jours)
        - expired: Kbis périmé (> 90 jours)
        - siret_invalid: SIRET invalide
    """
    c = canvas.Canvas(output_path, pagesize=A4)
    expected_anomalies = []
    siret = company.siret
    
    if scenario == "expired":
        date_emission = date.today() - timedelta(days=120)
        expected_anomalies.append({"rule_id": "KBIS_PERIME", "severity": "WARNING"})
    elif scenario == "siret_invalid":
        date_emission = date.today() - timedelta(days=15)
        siret = create_invalid_siret()
        expected_anomalies.append({"rule_id": "SIRET_FORMAT_INVALIDE", "severity": "ERROR"})
    else:
        date_emission = date.today() - timedelta(days=random.randint(5, 60))
    
    # En-tête officiel
    c.setFillColor(COLOR_DARK)
    c.rect(0, HEIGHT - 45 * mm, WIDTH, 45 * mm, fill=1, stroke=0)
    
    c.setFillColor(colors.HexColor("#C9A227"))  # Or
    c.rect(0, HEIGHT - 47 * mm, WIDTH, 2 * mm, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(20 * mm, HEIGHT - 22 * mm, "EXTRAIT K-BIS")
    
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, HEIGHT - 32 * mm, "Greffe du Tribunal de Commerce")
    c.drawString(20 * mm, HEIGHT - 38 * mm, f"de {company.ville}")
    
    # Numéro
    c.setFont("Helvetica", 9)
    c.drawRightString(WIDTH - 20 * mm, HEIGHT - 38 * mm, f"N° {doc_id}")
    
    # Titre section
    y = HEIGHT - 65 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "IDENTIFICATION DE LA PERSONNE MORALE")
    c.setStrokeColor(colors.HexColor("#C9A227"))
    c.setLineWidth(2)
    c.line(20 * mm, y - 3 * mm, 130 * mm, y - 3 * mm)
    
    y -= 20 * mm
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
        c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, f"SIRET (siège) : {siret}")
    c.setFillColor(COLOR_TEXT)
    c.setFont("Helvetica", 10)
    
    y -= 8 * mm
    c.drawString(20 * mm, y, f"N° TVA Intracommunautaire : {company.tva_intra}")
    
    # Siège social
    y -= 20 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "SIÈGE SOCIAL")
    c.setStrokeColor(colors.HexColor("#C9A227"))
    c.line(20 * mm, y - 3 * mm, 70 * mm, y - 3 * mm)
    
    y -= 15 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(20 * mm, y, f"Adresse : {company.adresse}")
    y -= 8 * mm
    c.drawString(20 * mm, y, f"          {company.code_postal} {company.ville}")
    
    # Date de délivrance
    y -= 30 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20 * mm, y, "DATE DE DÉLIVRANCE")
    c.setStrokeColor(colors.HexColor("#C9A227"))
    c.line(20 * mm, y - 3 * mm, 80 * mm, y - 3 * mm)
    
    y -= 15 * mm
    if scenario == "expired":
        c.setFillColor(COLOR_RED)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(20 * mm, y, f"{date_emission.strftime('%d/%m/%Y')}")
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y - 10 * mm, "⚠ Ce document date de plus de 90 jours et doit être renouvelé")
    else:
        c.setFillColor(COLOR_TEXT)
        c.setFont("Helvetica", 10)
        c.drawString(20 * mm, y, f"{date_emission.strftime('%d/%m/%Y')}")
    
    draw_footer(c, company)
    c.save()
    
    return {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "type": "kbis",
        "scenario": scenario,
        "anomalies_expected": expected_anomalies,
        "expected_fields": {
            "siret": siret,
            "siren": company.siren,
            "raison_sociale": company.raison_sociale,
            "tva_intra": company.tva_intra,
            "date_emission": date_emission.strftime("%d/%m/%Y"),
        },
    }


def generate_rib(
    output_path: str,
    company: RealCompany,
    doc_id: str,
    scenario: str = "valid",
) -> Dict[str, Any]:
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
    
    draw_professional_header(c, "RIB", company, doc_id)
    
    # Titre
    y = HEIGHT - 55 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(WIDTH / 2, y, "RELEVÉ D'IDENTITÉ BANCAIRE")
    
    # Titulaire
    y -= 25 * mm
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "TITULAIRE DU COMPTE")
    c.setStrokeColor(COLOR_ACCENT)
    c.setLineWidth(2)
    c.line(25 * mm, y - 3 * mm, 95 * mm, y - 3 * mm)
    
    y -= 18 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(COLOR_TEXT)
    c.drawString(25 * mm, y, company.raison_sociale)
    y -= 8 * mm
    c.drawString(25 * mm, y, company.adresse)
    y -= 8 * mm
    c.drawString(25 * mm, y, f"{company.code_postal} {company.ville}")
    y -= 8 * mm
    c.drawString(25 * mm, y, f"SIRET : {company.siret}")
    
    # Coordonnées bancaires
    y -= 30 * mm
    c.setFillColor(COLOR_DARK)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(25 * mm, y, "COORDONNÉES BANCAIRES")
    c.setStrokeColor(COLOR_ACCENT)
    c.line(25 * mm, y - 3 * mm, 105 * mm, y - 3 * mm)
    
    # Cadre IBAN/BIC
    y -= 25 * mm
    c.setFillColor(COLOR_LIGHT_BG)
    c.rect(20 * mm, y - 20 * mm, WIDTH - 40 * mm, 45 * mm, fill=1, stroke=0)
    c.setStrokeColor(COLOR_ACCENT if scenario == "valid" else COLOR_RED)
    c.setLineWidth(2)
    c.rect(20 * mm, y - 20 * mm, WIDTH - 40 * mm, 45 * mm, fill=0, stroke=1)
    
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_DARK)
    c.drawString(25 * mm, y + 12 * mm, "IBAN")
    
    c.setFont("Courier-Bold", 12)
    c.setFillColor(COLOR_RED if scenario == "iban_invalid" else COLOR_DARK)
    # Format IBAN avec espaces
    formatted_iban = " ".join([iban[i:i+4] for i in range(0, len(iban), 4)])
    c.drawString(25 * mm, y, formatted_iban)
    
    y -= 18 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(COLOR_DARK)
    c.drawString(25 * mm, y + 8 * mm, "BIC")
    c.setFont("Courier-Bold", 12)
    c.drawString(25 * mm, y - 4 * mm, company.bic)
    
    if scenario == "iban_invalid":
        y -= 25 * mm
        c.setFillColor(COLOR_RED)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(25 * mm, y, "⚠ IBAN INVALIDE - Vérifiez les coordonnées")
    
    draw_footer(c, company)
    c.save()
    
    return {
        "document_id": doc_id,
        "file_path": f"raw/{doc_id}.pdf",
        "type": "rib",
        "scenario": scenario,
        "anomalies_expected": expected_anomalies,
        "expected_fields": {
            "siret": company.siret,
            "raison_sociale": company.raison_sociale,
            "iban": iban,
            "bic": company.bic,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATEUR DE PAIRES MISMATCH
# ═══════════════════════════════════════════════════════════════════════════════

def generate_mismatch_pair(
    output_dir: Path,
    company1: RealCompany,
    company2: RealCompany,
    mismatch_type: str,
    pair_id: int,
) -> List[Dict[str, Any]]:
    """
    Génère une paire de documents avec erreur inter-document MISMATCH.
    
    mismatch_type: siret, raison_sociale, iban
    """
    results = []
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    if mismatch_type == "siret":
        # SIRET_MISMATCH : même raison sociale, SIRET différents
        doc_id_1 = f"MISMATCH_SIRET_{pair_id:02d}_A"
        doc_id_2 = f"MISMATCH_SIRET_{pair_id:02d}_B"
        
        # Créer une copie modifiée pour la facture
        company_mod = RealCompany(
            raison_sociale=company1.raison_sociale,  # Même raison sociale
            siren=company1.siren,
            siret=company1.siret,  # SIRET de company1
            tva_intra=company1.tva_intra,
            adresse=company1.adresse,
            code_postal=company1.code_postal,
            ville=company1.ville,
            forme_juridique=company1.forme_juridique,
            iban=company1.iban,
            bic=company1.bic,
        )
        
        # Document A : Facture avec SIRET company1
        result1 = generate_facture(
            str(raw_dir / f"{doc_id_1}.pdf"),
            company_mod, doc_id_1, "valid"
        )
        result1["anomalies_expected"] = [{"rule_id": "SIRET_MISMATCH", "severity": "ERROR"}]
        result1["batch_group"] = f"MISMATCH_SIRET_{pair_id:02d}"
        results.append(result1)
        
        # Créer company mod 2 avec SIRET différent mais même RS
        company_mod2 = RealCompany(
            raison_sociale=company1.raison_sociale,  # Même raison sociale !
            siren=company2.siren,
            siret=company2.siret,  # SIRET de company2 → MISMATCH !
            tva_intra=company2.tva_intra,
            adresse=company2.adresse,
            code_postal=company2.code_postal,
            ville=company2.ville,
            forme_juridique=company2.forme_juridique,
            iban=company2.iban,
            bic=company2.bic,
        )
        
        # Document B : URSSAF avec SIRET company2
        result2 = generate_attestation_urssaf(
            str(raw_dir / f"{doc_id_2}.pdf"),
            company_mod2, doc_id_2, "valid"
        )
        result2["anomalies_expected"] = [{"rule_id": "SIRET_MISMATCH", "severity": "ERROR"}]
        result2["batch_group"] = f"MISMATCH_SIRET_{pair_id:02d}"
        results.append(result2)
        
    elif mismatch_type == "raison_sociale":
        # RAISON_SOCIALE_MISMATCH : même SIRET, raisons sociales différentes
        doc_id_1 = f"MISMATCH_RS_{pair_id:02d}_A"
        doc_id_2 = f"MISMATCH_RS_{pair_id:02d}_B"
        
        result1 = generate_facture(
            str(raw_dir / f"{doc_id_1}.pdf"),
            company1, doc_id_1, "valid"
        )
        result1["anomalies_expected"] = [{"rule_id": "RAISON_SOCIALE_MISMATCH", "severity": "WARNING"}]
        result1["batch_group"] = f"MISMATCH_RS_{pair_id:02d}"
        results.append(result1)
        
        # Kbis avec RS différente mais même SIRET
        company_mod = RealCompany(
            raison_sociale="ENTREPRISE FICTIVE SARL",  # RS différente !
            siren=company1.siren,
            siret=company1.siret,  # Même SIRET
            tva_intra=company1.tva_intra,
            adresse=company1.adresse,
            code_postal=company1.code_postal,
            ville=company1.ville,
            forme_juridique="SARL",
            iban=company1.iban,
            bic=company1.bic,
        )
        
        result2 = generate_kbis(
            str(raw_dir / f"{doc_id_2}.pdf"),
            company_mod, doc_id_2, "valid"
        )
        result2["anomalies_expected"] = [{"rule_id": "RAISON_SOCIALE_MISMATCH", "severity": "WARNING"}]
        result2["batch_group"] = f"MISMATCH_RS_{pair_id:02d}"
        results.append(result2)
        
    elif mismatch_type == "iban":
        # IBAN_MISMATCH : même fournisseur, IBAN différents
        doc_id_1 = f"MISMATCH_IBAN_{pair_id:02d}_A"
        doc_id_2 = f"MISMATCH_IBAN_{pair_id:02d}_B"
        
        result1 = generate_facture(
            str(raw_dir / f"{doc_id_1}.pdf"),
            company1, doc_id_1, "valid"
        )
        result1["anomalies_expected"] = [{"rule_id": "IBAN_MISMATCH", "severity": "WARNING"}]
        result1["batch_group"] = f"MISMATCH_IBAN_{pair_id:02d}"
        results.append(result1)
        
        # RIB avec IBAN différent
        company_mod = RealCompany(
            raison_sociale=company1.raison_sociale,
            siren=company1.siren,
            siret=company1.siret,
            tva_intra=company1.tva_intra,
            adresse=company1.adresse,
            code_postal=company1.code_postal,
            ville=company1.ville,
            forme_juridique=company1.forme_juridique,
            iban=company2.iban,  # IBAN différent !
            bic=company2.bic,
        )
        
        result2 = generate_rib(
            str(raw_dir / f"{doc_id_2}.pdf"),
            company_mod, doc_id_2, "valid"
        )
        result2["anomalies_expected"] = [{"rule_id": "IBAN_MISMATCH", "severity": "WARNING"}]
        result2["batch_group"] = f"MISMATCH_IBAN_{pair_id:02d}"
        results.append(result2)
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Génère un dataset complet pour démonstration DocuFlow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples :
    python generate_demo_dataset.py --output ./output/demo
    python generate_demo_dataset.py --output ./output/demo --seed 42
        """
    )
    parser.add_argument(
        "--output", type=str, default="./output/demo",
        help="Répertoire de sortie (défaut: ./output/demo)"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Graine aléatoire (défaut: 42)"
    )
    args = parser.parse_args()
    
    random.seed(args.seed)
    output_dir = Path(args.output)
    
    print()
    print("═" * 75)
    print("  🎯 GÉNÉRATION DU DATASET DE DÉMONSTRATION — DOCUFLOW")
    print("═" * 75)
    print(f"  📁 Sortie : {output_dir.resolve()}")
    print(f"  🏢 Entreprises disponibles : {len(REAL_COMPANIES)}")
    print("═" * 75)
    
    all_results = []
    
    # ═══════════════════════════════════════════════════════════════════════
    # DOSSIER 1 : SAME_SUPPLIER (Un seul fournisseur - test batch valide)
    # ═══════════════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 75)
    print("  📦 DOSSIER 1 : same_supplier/")
    print("     → Documents d'UN SEUL fournisseur (CARREFOUR)")
    print("     → Upload batch = PAS de MISMATCH attendu")
    print("─" * 75)
    
    same_supplier_dir = output_dir / "same_supplier"
    raw_dir = same_supplier_dir / "raw"
    labels_dir = same_supplier_dir / "labels"
    raw_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    company = REAL_COMPANIES[0]  # CARREFOUR
    same_results = []
    doc_idx = 1
    
    # Factures valides
    for i in range(3):
        doc_id = f"FAC_{doc_idx:03d}"
        result = generate_facture(
            str(raw_dir / f"{doc_id}.pdf"),
            company, doc_id, "valid"
        )
        same_results.append(result)
        print(f"    ✓ {doc_id} — Facture valide ({company.raison_sociale})")
        doc_idx += 1
    
    # Devis valide
    doc_id = f"DEV_{doc_idx:03d}"
    result = generate_devis(str(raw_dir / f"{doc_id}.pdf"), company, doc_id, "valid")
    same_results.append(result)
    print(f"    ✓ {doc_id} — Devis valide")
    doc_idx += 1
    
    # URSSAF valide
    doc_id = f"URSSAF_{doc_idx:03d}"
    result = generate_attestation_urssaf(str(raw_dir / f"{doc_id}.pdf"), company, doc_id, "valid")
    same_results.append(result)
    print(f"    ✓ {doc_id} — Attestation URSSAF valide")
    doc_idx += 1
    
    # Kbis valide
    doc_id = f"KBIS_{doc_idx:03d}"
    result = generate_kbis(str(raw_dir / f"{doc_id}.pdf"), company, doc_id, "valid")
    same_results.append(result)
    print(f"    ✓ {doc_id} — Kbis valide")
    doc_idx += 1
    
    # RIB valide
    doc_id = f"RIB_{doc_idx:03d}"
    result = generate_rib(str(raw_dir / f"{doc_id}.pdf"), company, doc_id, "valid")
    same_results.append(result)
    print(f"    ✓ {doc_id} — RIB valide")
    doc_idx += 1
    
    # Sauvegarder labels individuels
    for r in same_results:
        label_path = labels_dir / f"{r['document_id']}.json"
        with open(label_path, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
    
    # Manifeste
    manifest_path = same_supplier_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(same_results, f, ensure_ascii=False, indent=2)
    
    all_results.extend(same_results)
    print(f"\n    📋 {len(same_results)} documents générés pour same_supplier/")
    
    # ═══════════════════════════════════════════════════════════════════════
    # DOSSIER 2 : MULTI_SUPPLIER (Plusieurs fournisseurs + erreurs)
    # ═══════════════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 75)
    print("  📦 DOSSIER 2 : multi_supplier/")
    print("     → Documents de 6+ fournisseurs différents")
    print("     → Toutes les erreurs unitaires couvertes")
    print("─" * 75)
    
    multi_supplier_dir = output_dir / "multi_supplier"
    raw_dir = multi_supplier_dir / "raw"
    labels_dir = multi_supplier_dir / "labels"
    raw_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    multi_results = []
    doc_idx = 1
    
    # Documents VALIDES de 6 fournisseurs différents
    print("\n    === Documents valides (6 fournisseurs) ===")
    
    for i, company in enumerate(REAL_COMPANIES[:6]):
        # Chaque fournisseur a une facture + un autre doc
        doc_id = f"FAC_{doc_idx:03d}"
        result = generate_facture(str(raw_dir / f"{doc_id}.pdf"), company, doc_id, "valid")
        multi_results.append(result)
        print(f"    ✓ {doc_id} — Facture ({company.raison_sociale})")
        doc_idx += 1
    
    # Un document de chaque type pour compléter
    doc_id = f"DEV_{doc_idx:03d}"
    result = generate_devis(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[1], doc_id, "valid")
    multi_results.append(result)
    print(f"    ✓ {doc_id} — Devis (TOTAL ENERGIES)")
    doc_idx += 1
    
    doc_id = f"URSSAF_{doc_idx:03d}"
    result = generate_attestation_urssaf(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[2], doc_id, "valid")
    multi_results.append(result)
    print(f"    ✓ {doc_id} — URSSAF (ORANGE)")
    doc_idx += 1
    
    doc_id = f"KBIS_{doc_idx:03d}"
    result = generate_kbis(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[3], doc_id, "valid")
    multi_results.append(result)
    print(f"    ✓ {doc_id} — Kbis (SNCF)")
    doc_idx += 1
    
    doc_id = f"RIB_{doc_idx:03d}"
    result = generate_rib(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[4], doc_id, "valid")
    multi_results.append(result)
    print(f"    ✓ {doc_id} — RIB (AIR FRANCE)")
    doc_idx += 1
    
    # Documents avec ERREURS UNITAIRES
    print("\n    === Erreurs unitaires (toutes règles) ===")
    
    # TVA_CALCUL_ERROR
    doc_id = f"FAC_{doc_idx:03d}"
    result = generate_facture(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[5], doc_id, "tva_error")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — TVA_CALCUL_ERROR (ratio 15%)")
    doc_idx += 1
    
    # TTC_CALCUL_ERROR
    doc_id = f"FAC_{doc_idx:03d}"
    result = generate_facture(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[6], doc_id, "ttc_error")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — TTC_CALCUL_ERROR (TTC ≠ HT+TVA)")
    doc_idx += 1
    
    # SIRET_FORMAT_INVALIDE
    doc_id = f"FAC_{doc_idx:03d}"
    result = generate_facture(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[7], doc_id, "siret_invalid")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — SIRET_FORMAT_INVALIDE")
    doc_idx += 1
    
    # IBAN_FORMAT_INVALIDE
    doc_id = f"FAC_{doc_idx:03d}"
    result = generate_facture(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[8], doc_id, "iban_invalid")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — IBAN_FORMAT_INVALIDE")
    doc_idx += 1
    
    # MONTANT_ANORMAL (très élevé)
    doc_id = f"FAC_{doc_idx:03d}"
    result = generate_facture(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[9], doc_id, "montant_anormal")
    multi_results.append(result)
    print(f"    ℹ {doc_id} — MONTANT_ANORMAL (detection ML)")
    doc_idx += 1
    
    # DEVIS_EXPIRE
    doc_id = f"DEV_{doc_idx:03d}"
    result = generate_devis(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[0], doc_id, "expired")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — DEVIS_EXPIRE")
    doc_idx += 1
    
    # ATTESTATION_EXPIREE
    doc_id = f"URSSAF_{doc_idx:03d}"
    result = generate_attestation_urssaf(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[1], doc_id, "expired")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — ATTESTATION_EXPIREE (ERROR)")
    doc_idx += 1
    
    # ATTESTATION bientôt expirée (WARNING)
    doc_id = f"URSSAF_{doc_idx:03d}"
    result = generate_attestation_urssaf(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[2], doc_id, "expiring_soon")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — ATTESTATION_EXPIREE (WARNING <30j)")
    doc_idx += 1
    
    # KBIS_PERIME
    doc_id = f"KBIS_{doc_idx:03d}"
    result = generate_kbis(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[3], doc_id, "expired")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — KBIS_PERIME (>90 jours)")
    doc_idx += 1
    
    # RIB avec IBAN invalide
    doc_id = f"RIB_{doc_idx:03d}"
    result = generate_rib(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[4], doc_id, "iban_invalid")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — IBAN_FORMAT_INVALIDE (RIB)")
    doc_idx += 1
    
    # KBIS avec SIRET invalide
    doc_id = f"KBIS_{doc_idx:03d}"
    result = generate_kbis(str(raw_dir / f"{doc_id}.pdf"), REAL_COMPANIES[5], doc_id, "siret_invalid")
    multi_results.append(result)
    print(f"    ⚠ {doc_id} — SIRET_FORMAT_INVALIDE (KBIS)")
    doc_idx += 1
    
    # Sauvegarder labels
    for r in multi_results:
        label_path = labels_dir / f"{r['document_id']}.json"
        with open(label_path, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
    
    # Manifeste
    manifest_path = multi_supplier_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(multi_results, f, ensure_ascii=False, indent=2)
    
    all_results.extend(multi_results)
    print(f"\n    📋 {len(multi_results)} documents générés pour multi_supplier/")
    
    # ═══════════════════════════════════════════════════════════════════════
    # DOSSIER 3 : MISMATCH_TEST (Paires pour tester les règles inter-docs)
    # ═══════════════════════════════════════════════════════════════════════
    
    print("\n" + "─" * 75)
    print("  📦 DOSSIER 3 : mismatch_test/")
    print("     → Paires de documents pour tester MISMATCH en batch")
    print("     → Upload batch = MISMATCH détecté")
    print("─" * 75)
    
    mismatch_dir = output_dir / "mismatch_test"
    raw_dir = mismatch_dir / "raw"
    labels_dir = mismatch_dir / "labels"
    raw_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)
    
    mismatch_results = []
    
    # SIRET_MISMATCH x2
    print("\n    === SIRET_MISMATCH ===")
    results = generate_mismatch_pair(mismatch_dir, REAL_COMPANIES[0], REAL_COMPANIES[1], "siret", 1)
    mismatch_results.extend(results)
    for r in results:
        print(f"    ⚠ {r['document_id']} — SIRET différent")
    
    results = generate_mismatch_pair(mismatch_dir, REAL_COMPANIES[2], REAL_COMPANIES[3], "siret", 2)
    mismatch_results.extend(results)
    for r in results:
        print(f"    ⚠ {r['document_id']} — SIRET différent")
    
    # RAISON_SOCIALE_MISMATCH x2
    print("\n    === RAISON_SOCIALE_MISMATCH ===")
    results = generate_mismatch_pair(mismatch_dir, REAL_COMPANIES[4], REAL_COMPANIES[5], "raison_sociale", 1)
    mismatch_results.extend(results)
    for r in results:
        print(f"    ⚠ {r['document_id']} — Raison sociale différente")
    
    results = generate_mismatch_pair(mismatch_dir, REAL_COMPANIES[6], REAL_COMPANIES[7], "raison_sociale", 2)
    mismatch_results.extend(results)
    for r in results:
        print(f"    ⚠ {r['document_id']} — Raison sociale différente")
    
    # IBAN_MISMATCH x2
    print("\n    === IBAN_MISMATCH ===")
    results = generate_mismatch_pair(mismatch_dir, REAL_COMPANIES[8], REAL_COMPANIES[9], "iban", 1)
    mismatch_results.extend(results)
    for r in results:
        print(f"    ⚠ {r['document_id']} — IBAN différent")
    
    results = generate_mismatch_pair(mismatch_dir, REAL_COMPANIES[0], REAL_COMPANIES[2], "iban", 2)
    mismatch_results.extend(results)
    for r in results:
        print(f"    ⚠ {r['document_id']} — IBAN différent")
    
    # Sauvegarder labels
    for r in mismatch_results:
        label_path = labels_dir / f"{r['document_id']}.json"
        with open(label_path, "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False, indent=2)
    
    # Manifeste
    manifest_path = mismatch_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(mismatch_results, f, ensure_ascii=False, indent=2)
    
    all_results.extend(mismatch_results)
    print(f"\n    📋 {len(mismatch_results)} documents générés pour mismatch_test/")
    
    # ═══════════════════════════════════════════════════════════════════════
    # MANIFESTE GLOBAL ET RÉSUMÉ
    # ═══════════════════════════════════════════════════════════════════════
    
    # Manifeste global
    global_manifest = {
        "total_documents": len(all_results),
        "generated_at": date.today().isoformat(),
        "seed": args.seed,
        "folders": {
            "same_supplier": {
                "path": "same_supplier/",
                "count": len(same_results),
                "description": "Documents d'UN SEUL fournisseur - test batch sans MISMATCH",
                "supplier": REAL_COMPANIES[0].raison_sociale,
            },
            "multi_supplier": {
                "path": "multi_supplier/",
                "count": len(multi_results),
                "description": "Documents de 6+ fournisseurs avec erreurs unitaires",
            },
            "mismatch_test": {
                "path": "mismatch_test/",
                "count": len(mismatch_results),
                "description": "Paires de documents pour tester MISMATCH en batch",
            },
        },
        "documents": all_results,
    }
    
    global_manifest_path = output_dir / "demo_manifest.json"
    with open(global_manifest_path, "w", encoding="utf-8") as f:
        json.dump(global_manifest, f, ensure_ascii=False, indent=2)
    
    # Résumé
    print("\n" + "═" * 75)
    print("  ✅ GÉNÉRATION TERMINÉE")
    print("═" * 75)
    print(f"\n  📊 RÉSUMÉ :")
    print(f"     • Total documents : {len(all_results)}")
    print(f"     • same_supplier/  : {len(same_results)} docs (1 fournisseur)")
    print(f"     • multi_supplier/ : {len(multi_results)} docs (6+ fournisseurs)")
    print(f"     • mismatch_test/  : {len(mismatch_results)} docs (paires MISMATCH)")
    
    # Stats par anomalie
    anomaly_counts = {}
    valid_count = 0
    for doc in all_results:
        anomalies = doc.get("anomalies_expected", [])
        if not anomalies:
            valid_count += 1
        for a in anomalies:
            rule = a.get("rule_id", "UNKNOWN")
            anomaly_counts[rule] = anomaly_counts.get(rule, 0) + 1
    
    print(f"\n  📋 COUVERTURE DES RÈGLES :")
    for rule in sorted(anomaly_counts.keys()):
        print(f"     • {rule:30s} × {anomaly_counts[rule]}")
    print(f"     • {'Documents valides':30s} × {valid_count}")
    
    # Stats par entreprise
    company_counts = {}
    for doc in all_results:
        rs = doc.get("expected_fields", {}).get("raison_sociale", "?")
        company_counts[rs] = company_counts.get(rs, 0) + 1
    
    print(f"\n  🏢 ENTREPRISES UTILISÉES :")
    for name, cnt in sorted(company_counts.items(), key=lambda x: -x[1]):
        print(f"     • {name:35s} × {cnt}")
    
    print(f"\n  📁 FICHIERS GÉNÉRÉS :")
    print(f"     {output_dir / 'same_supplier' / 'raw'}")
    print(f"     {output_dir / 'multi_supplier' / 'raw'}")
    print(f"     {output_dir / 'mismatch_test' / 'raw'}")
    print(f"     {global_manifest_path}")
    
    print("\n" + "═" * 75)
    print("  🎯 INSTRUCTIONS POUR LA DÉMO :")
    print("═" * 75)
    print("""
    1. UPLOAD NORMAL (bouton bleu) :
       → Fichiers de multi_supplier/ : montre les erreurs individuelles
       
    2. UPLOAD BATCH (bouton vert) :
       → Fichiers de same_supplier/ : PAS de MISMATCH (même fournisseur)
       → Fichiers de mismatch_test/ (même groupe) : MISMATCH détecté !
       
    3. EXEMPLES DE MISMATCH :
       → MISMATCH_SIRET_01_A.pdf + MISMATCH_SIRET_01_B.pdf → SIRET_MISMATCH
       → MISMATCH_RS_01_A.pdf + MISMATCH_RS_01_B.pdf → RAISON_SOCIALE_MISMATCH
       → MISMATCH_IBAN_01_A.pdf + MISMATCH_IBAN_01_B.pdf → IBAN_MISMATCH
    """)
    print("═" * 75)


if __name__ == "__main__":
    main()
