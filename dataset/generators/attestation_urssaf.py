"""
Générateur d'attestations de vigilance URSSAF en PDF.
"""
import random
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from company_factory import Company


def _draw_tampon(c: canvas.Canvas, x: float, y: float) -> None:
    """Dessine un tampon rond simulé."""
    c.setStrokeColor(colors.HexColor("#1B2A4A"))
    c.setLineWidth(2)
    c.circle(x, y, 15 * mm, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 7)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawCentredString(x, y + 5 * mm, "URSSAF")
    c.setFont("Helvetica", 6)
    c.drawCentredString(x, y, "Attestation")
    c.drawCentredString(x, y - 5 * mm, "Vérifiée")


def generate_attestation_urssaf(
    company: Company,
    output_path: str,
    expired: bool = False,
    doc_index: int = 1,
) -> dict:
    """
    Génère un PDF d'attestation de vigilance URSSAF.

    Args:
        company: entreprise concernée
        output_path: chemin du PDF
        expired: si True, la date d'expiration est dans le passé
        doc_index: numéro séquentiel
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    # Dates
    date_emission = date.today() - timedelta(days=random.randint(10, 50))
    if expired:
        date_expiration = date.today() - timedelta(days=random.randint(1, 90))
    else:
        date_expiration = date.today() + timedelta(days=random.randint(30, 90))

    num_attestation = f"ATT-{random.randint(10000000, 99999999)}"

    # ── En-tête URSSAF ──
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(0, height - 40 * mm, width, 40 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(20 * mm, height - 20 * mm, "URSSAF")
    c.setFont("Helvetica", 12)
    c.drawString(20 * mm, height - 30 * mm, "Union de Recouvrement des Cotisations")
    c.drawString(20 * mm, height - 36 * mm, "de Sécurité Sociale et d'Allocations Familiales")

    # ── Titre ──
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 60 * mm, "Attestation de vigilance")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawCentredString(width / 2, height - 68 * mm, f"N° {num_attestation}")

    # ── Encadré informations entreprise ──
    box_top = height - 80 * mm
    box_height = 55 * mm
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setLineWidth(1)
    c.rect(20 * mm, box_top - box_height, 170 * mm, box_height, fill=0, stroke=1)

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(25 * mm, box_top - 10 * mm, "Informations de l'entreprise")

    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    fields = [
        ("Raison Sociale", company.raison_sociale),
        ("SIRET", company.siret),
        ("SIREN", company.siren),
        ("Adresse", f"{company.adresse_rue}, {company.adresse_cp} {company.adresse_ville}"),
        ("Forme Juridique", company.forme_juridique),
    ]
    y = box_top - 20 * mm
    for label, value in fields:
        c.setFont("Helvetica-Bold", 9)
        c.drawString(30 * mm, y, f"{label} :")
        c.setFont("Helvetica", 9)
        c.drawString(75 * mm, y, str(value)[:60])
        y -= 8 * mm

    # ── Période de validité ──
    y -= 15 * mm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, y, "Période de validité")
    y -= 10 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(25 * mm, y, f"Date d'émission : {date_emission.strftime('%d/%m/%Y')}")
    y -= 8 * mm

    # Date d'expiration bien visible
    if expired:
        c.setFillColor(colors.HexColor("#E63946"))
        c.setFont("Helvetica-Bold", 12)
    else:
        c.setFillColor(colors.HexColor("#00C896"))
        c.setFont("Helvetica-Bold", 11)
    c.drawString(
        25 * mm, y,
        f"Date d'expiration : {date_expiration.strftime('%d/%m/%Y')}",
    )

    # ── Mention légale ──
    y -= 25 * mm
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(
        20 * mm, y,
        "Cette attestation certifie que l'entreprise est à jour de ses obligations",
    )
    c.drawString(
        20 * mm, y - 4 * mm,
        "déclaratives et de paiement des cotisations sociales.",
    )
    c.drawString(
        20 * mm, y - 8 * mm,
        "Art. L.243-15 du Code de la Sécurité Sociale.",
    )

    # Tampon
    _draw_tampon(c, 160 * mm, y - 5 * mm)

    c.save()

    return {
        "type": "attestation_urssaf",
        "num_attestation": num_attestation,
        "siret": company.siret,
        "siren": company.siren,
        "raison_sociale": company.raison_sociale,
        "date_emission": date_emission.strftime("%d/%m/%Y"),
        "date_expiration": date_expiration.strftime("%d/%m/%Y"),
        "expired": expired,
    }
