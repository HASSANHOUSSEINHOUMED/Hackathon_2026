"""
Générateur de Relevés d'Identité Bancaire (RIB) en PDF.
"""
import random

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from company_factory import Company
from config import LOGO_COLORS


# Noms de banques fictives
BANQUES_FICTIVES: list[str] = [
    "Banque Nationale de France",
    "Crédit Moderne",
    "Banque de l'Avenir",
    "Caisse Régionale du Centre",
    "Banque Européenne de Commerce",
    "Crédit Industriel et Financier",
    "Banque Solidaire de France",
    "Crédit Coopératif du Sud",
]

AGENCES: list[str] = [
    "Agence Paris Opéra",
    "Agence Lyon Part-Dieu",
    "Agence Marseille Canebière",
    "Agence Bordeaux Centre",
    "Agence Toulouse Capitole",
    "Agence Nantes Commerce",
    "Agence Lille Grand-Place",
    "Agence Strasbourg Kléber",
]


def generate_rib(
    company: Company,
    output_path: str,
    doc_index: int = 1,
) -> dict:
    """
    Génère un PDF de Relevé d'Identité Bancaire (RIB).

    Args:
        company: entreprise titulaire
        output_path: chemin du PDF
        doc_index: numéro séquentiel
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    banque_nom = random.choice(BANQUES_FICTIVES)
    agence = random.choice(AGENCES)

    # Décomposer l'IBAN pour affichage
    iban = company.iban
    iban_formate = " ".join([iban[i:i+4] for i in range(0, len(iban), 4)])

    # Extraire les composants du RIB depuis l'IBAN
    # FR76 + code banque (5) + code guichet (5) + n° compte (11) + clé (2)
    iban_body = iban[4:]  # après FRxx
    code_banque = iban_body[:5]
    code_guichet = iban_body[5:10]
    numero_compte = iban_body[10:21]
    cle_rib = iban_body[21:23]

    # ── Logo banque fictive ──
    color_hex = random.choice(LOGO_COLORS)
    r, g, b = (int(color_hex[i:i+2], 16) / 255 for i in (1, 3, 5))
    c.setFillColorRGB(r, g, b)
    c.roundRect(20 * mm, height - 35 * mm, 50 * mm, 18 * mm, 4 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(45 * mm, height - 24 * mm, banque_nom[:18])
    c.setFont("Helvetica", 8)
    c.drawCentredString(45 * mm, height - 30 * mm, "Établissement bancaire")

    # ── Titre ──
    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawCentredString(width / 2, height - 55 * mm, "RELEVÉ D'IDENTITÉ BANCAIRE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawCentredString(width / 2, height - 62 * mm, "RIB")

    # ── Titulaire ──
    y = height - 80 * mm
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setLineWidth(1)
    c.rect(20 * mm, y - 25 * mm, 170 * mm, 28 * mm, fill=0, stroke=1)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(25 * mm, y, "Titulaire du compte")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(25 * mm, y - 8 * mm, company.raison_sociale)
    c.drawString(25 * mm, y - 15 * mm, f"{company.adresse_rue}, {company.adresse_cp} {company.adresse_ville}")
    c.drawString(25 * mm, y - 22 * mm, f"SIRET : {company.siret}")

    # ── IBAN et BIC ──
    y -= 40 * mm
    c.setFillColor(colors.HexColor("#F0F4F8"))
    c.rect(20 * mm, y - 20 * mm, 170 * mm, 25 * mm, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.rect(20 * mm, y - 20 * mm, 170 * mm, 25 * mm, fill=0, stroke=1)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(25 * mm, y, "IBAN")
    c.setFont("Courier-Bold", 13)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(50 * mm, y, iban_formate)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(25 * mm, y - 12 * mm, "BIC / SWIFT")
    c.setFont("Courier-Bold", 13)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(70 * mm, y - 12 * mm, company.bic)

    # ── Domiciliation ──
    y -= 35 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(25 * mm, y, "Domiciliation")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(25 * mm, y - 8 * mm, f"{banque_nom} — {agence}")

    # ── Tableau code banque / guichet / compte / clé ──
    y -= 25 * mm
    headers = ["Code Banque", "Code Guichet", "N° de Compte", "Clé RIB"]
    values = [code_banque, code_guichet, numero_compte, cle_rib]
    col_width = 170 * mm / 4

    for i, (header, value) in enumerate(zip(headers, values)):
        x = 20 * mm + i * col_width
        # En-tête
        c.setFillColor(colors.HexColor("#1B2A4A"))
        c.rect(x, y, col_width, 8 * mm, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + col_width / 2, y + 2 * mm, header)
        # Valeur
        c.setStrokeColor(colors.HexColor("#CBD5E0"))
        c.rect(x, y - 10 * mm, col_width, 10 * mm, fill=0, stroke=1)
        c.setFillColor(colors.HexColor("#2D3748"))
        c.setFont("Courier-Bold", 11)
        c.drawCentredString(x + col_width / 2, y - 6 * mm, value)

    # ── Mention ──
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(20 * mm, 25 * mm, "Ce document est un relevé d'identité bancaire à usage interne.")
    c.drawString(20 * mm, 21 * mm, f"Banque : {banque_nom} — Domiciliation : {agence}")

    c.save()

    return {
        "type": "rib",
        "siret": company.siret,
        "raison_sociale": company.raison_sociale,
        "iban": iban,
        "iban_formate": iban_formate,
        "bic": company.bic,
        "code_banque": code_banque,
        "code_guichet": code_guichet,
        "numero_compte": numero_compte,
        "cle_rib": cle_rib,
        "banque": banque_nom,
        "agence": agence,
    }
