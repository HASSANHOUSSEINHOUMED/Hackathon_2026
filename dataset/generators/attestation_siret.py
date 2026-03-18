"""
Générateur d'avis de situation SIRENE (attestation SIRET) en PDF.
"""
import random
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from company_factory import Company


def generate_attestation_siret(
    company: Company,
    output_path: str,
    expired: bool = False,
    doc_index: int = 1,
) -> dict:
    """
    Génère un PDF d'avis de situation au répertoire SIRENE.

    Args:
        company: entreprise concernée
        output_path: chemin du PDF
        expired: si True, l'avis est daté de plus de 6 mois
        doc_index: numéro séquentiel
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    if expired:
        date_avis = date.today() - timedelta(days=random.randint(180, 365))
    else:
        date_avis = date.today() - timedelta(days=random.randint(0, 30))

    nic = company.siret[9:]

    # ── En-tête INSEE ──
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(0, height - 30 * mm, width, 30 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20 * mm, height - 15 * mm, "INSEE")
    c.setFont("Helvetica", 10)
    c.drawString(20 * mm, height - 22 * mm, "Institut National de la Statistique et des Études Économiques")

    # ── Titre ──
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 48 * mm, "Avis de situation au répertoire SIRENE")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawCentredString(
        width / 2, height - 56 * mm,
        f"Date de l'avis : {date_avis.strftime('%d/%m/%Y')}",
    )

    # ── Tableau d'informations ──
    table_data = [
        ("SIREN", company.siren),
        ("NIC", nic),
        ("SIRET", company.siret),
        ("Dénomination", company.raison_sociale),
        ("Forme Juridique", company.forme_juridique),
        ("Adresse", company.adresse_rue),
        ("Code Postal", company.adresse_cp),
        ("Commune", company.adresse_ville),
        ("Date de création", company.date_creation.strftime("%d/%m/%Y")),
        ("Code APE (NAF)", company.code_naf),
        ("Libellé APE", company.libelle_naf),
        ("Dirigeant", company.dirigeant),
    ]

    table_top = height - 70 * mm
    row_height = 8 * mm
    label_width = 55 * mm
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.HexColor("#E2E8F0"))

    for i, (label, value) in enumerate(table_data):
        y = table_top - i * row_height

        # Fond alterné
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#F8F9FA"))
            c.rect(20 * mm, y - 3 * mm, 170 * mm, row_height, fill=1, stroke=0)

        # Bordure
        c.rect(20 * mm, y - 3 * mm, 170 * mm, row_height, fill=0, stroke=1)
        c.line(20 * mm + label_width, y - 3 * mm, 20 * mm + label_width, y - 3 * mm + row_height)

        # Label
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#1B2A4A"))
        c.drawString(22 * mm, y + 1 * mm, label)

        # Valeur
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#2D3748"))
        c.drawString(22 * mm + label_width + 3 * mm, y + 1 * mm, str(value)[:55])

    # ── Mention légale ──
    y_bottom = table_top - len(table_data) * row_height - 15 * mm
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(
        20 * mm, y_bottom,
        "Ce document est délivré à titre informatif et n'a pas valeur de certificat.",
    )
    c.drawString(
        20 * mm, y_bottom - 4 * mm,
        "Source : répertoire SIRENE — INSEE — https://www.sirene.fr",
    )
    c.drawString(
        20 * mm, y_bottom - 8 * mm,
        f"Émis le {date_avis.strftime('%d/%m/%Y')} — Reproduction autorisée.",
    )

    c.save()

    return {
        "type": "attestation_siret",
        "siret": company.siret,
        "siren": company.siren,
        "nic": nic,
        "raison_sociale": company.raison_sociale,
        "forme_juridique": company.forme_juridique,
        "adresse": f"{company.adresse_rue}, {company.adresse_cp} {company.adresse_ville}",
        "date_creation": company.date_creation.strftime("%d/%m/%Y"),
        "code_naf": company.code_naf,
        "libelle_naf": company.libelle_naf,
        "dirigeant": company.dirigeant,
        "date_avis": date_avis.strftime("%d/%m/%Y"),
        "expired": expired,
    }
