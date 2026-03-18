"""
Générateur d'extraits Kbis simplifiés en PDF avec QR code.
"""
import json
import random
from datetime import date, timedelta
from io import BytesIO

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from company_factory import Company
from config import VILLES_GREFFES


def _draw_greffier_signature(c: canvas.Canvas, x: float, y: float) -> None:
    """Dessine une signature et un tampon de greffier simulés."""
    # Tampon rectangulaire
    c.setStrokeColor(colors.HexColor("#1B2A4A"))
    c.setLineWidth(1.5)
    c.rect(x, y, 50 * mm, 18 * mm, fill=0, stroke=1)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawCentredString(x + 25 * mm, y + 12 * mm, "GREFFE DU TRIBUNAL")
    c.drawCentredString(x + 25 * mm, y + 7 * mm, "DE COMMERCE")
    c.setFont("Helvetica", 6)
    c.drawCentredString(x + 25 * mm, y + 2 * mm, "Certifié conforme")

    # Signature
    c.setLineWidth(1)
    p = c.beginPath()
    p.moveTo(x + 5 * mm, y - 5 * mm)
    p.curveTo(
        x + 15 * mm, y - 2 * mm,
        x + 25 * mm, y - 8 * mm,
        x + 40 * mm, y - 4 * mm,
    )
    c.drawPath(p, fill=0, stroke=1)


def generate_kbis(
    company: Company,
    output_path: str,
    expired: bool = False,
    doc_index: int = 1,
) -> dict:
    """
    Génère un PDF d'extrait Kbis simplifié.

    Args:
        company: entreprise concernée
        output_path: chemin du PDF
        expired: si True, date d'immatriculation très ancienne (> 90 jours)
        doc_index: numéro séquentiel
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    ville_greffe = random.choice(VILLES_GREFFES)
    num_rcs = f"{random.randint(100, 999)} {random.randint(100, 999)} {random.randint(100, 999)}"
    date_immatriculation = company.date_creation

    if expired:
        date_kbis = date.today() - timedelta(days=random.randint(91, 365))
    else:
        date_kbis = date.today() - timedelta(days=random.randint(0, 30))

    objet_social = random.choice([
        "Conseil et développement en systèmes informatiques",
        "Commerce de gros de matériel électrique et électronique",
        "Travaux de construction et de rénovation de bâtiments",
        "Restauration et services de traiteur",
        "Transport routier de marchandises",
        "Activités de nettoyage et d'entretien",
        "Formation professionnelle continue",
        "Activités d'architecture et d'ingénierie",
    ])

    # ── En-tête ──
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(0, height - 35 * mm, width, 35 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 18 * mm, "EXTRAIT Kbis")
    c.setFont("Helvetica", 10)
    c.drawCentredString(
        width / 2, height - 26 * mm,
        f"Greffe du Tribunal de Commerce de {ville_greffe}",
    )

    # ── Date ──
    c.setFillColor(colors.HexColor("#718096"))
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, height - 45 * mm, f"Extrait délivré le {date_kbis.strftime('%d/%m/%Y')}")

    # ── Informations ──
    fields = [
        ("N° RCS", f"{num_rcs} RCS {ville_greffe}"),
        ("Dénomination", company.raison_sociale),
        ("Forme juridique", company.forme_juridique),
        ("Capital social", f"{company.capital_social:,} €".replace(",", " ")),
        ("Adresse du siège", f"{company.adresse_rue}"),
        ("", f"{company.adresse_cp} {company.adresse_ville}"),
        ("SIREN", company.siren),
        ("SIRET (siège)", company.siret),
        ("Code APE", f"{company.code_naf} — {company.libelle_naf}"),
        ("Dirigeant", f"{company.dirigeant} (Président / Gérant)"),
        ("Date d'immatriculation", date_immatriculation.strftime("%d/%m/%Y")),
        ("Objet social", objet_social[:65]),
        ("TVA intracommunautaire", company.tva_intra),
    ]

    y = height - 60 * mm
    row_h = 9 * mm

    for i, (label, value) in enumerate(fields):
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#F0F4F8"))
            c.rect(20 * mm, y - 3 * mm, 170 * mm, row_h, fill=1, stroke=0)

        c.setStrokeColor(colors.HexColor("#E2E8F0"))
        c.rect(20 * mm, y - 3 * mm, 170 * mm, row_h, fill=0, stroke=1)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.HexColor("#1B2A4A"))
        if label:
            c.drawString(22 * mm, y + 1 * mm, label)

        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#2D3748"))
        c.drawString(75 * mm, y + 1 * mm, str(value)[:55])
        y -= row_h

    # ── QR Code ──
    qr_data = json.dumps({
        "siren": company.siren,
        "siret": company.siret,
        "raison_sociale": company.raison_sociale,
        "rcs": num_rcs,
        "greffe": ville_greffe,
    }, ensure_ascii=False)
    qr = qrcode.make(qr_data, box_size=4, border=2)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    c.drawImage(ImageReader(qr_buffer), 20 * mm, y - 35 * mm, 30 * mm, 30 * mm)

    # ── Tampon et signature du greffier ──
    _draw_greffier_signature(c, 120 * mm, y - 30 * mm)

    # ── Mentions ──
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(20 * mm, 25 * mm, "Ce document est un extrait simplifié et n'a pas de valeur juridique officielle.")
    c.drawString(20 * mm, 21 * mm, f"Source simulée — Greffe du Tribunal de Commerce de {ville_greffe}.")

    c.save()

    return {
        "type": "kbis",
        "siret": company.siret,
        "siren": company.siren,
        "raison_sociale": company.raison_sociale,
        "forme_juridique": company.forme_juridique,
        "capital_social": company.capital_social,
        "dirigeant": company.dirigeant,
        "num_rcs": num_rcs,
        "ville_greffe": ville_greffe,
        "date_immatriculation": date_immatriculation.strftime("%d/%m/%Y"),
        "objet_social": objet_social,
        "tva_intra": company.tva_intra,
        "code_naf": company.code_naf,
        "date_kbis": date_kbis.strftime("%d/%m/%Y"),
        "expired": expired,
    }
