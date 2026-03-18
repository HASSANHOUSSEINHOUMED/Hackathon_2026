"""
Générateur de factures PDF réalistes avec ReportLab.
"""
import random
from datetime import date, timedelta
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from company_factory import Company
from config import LOGO_COLORS, TVA_DEFAULT


def _draw_logo(c: canvas.Canvas, company: Company, x: float, y: float) -> None:
    """Dessine un logo procédural : rectangle coloré + initiales."""
    color_hex = random.choice(LOGO_COLORS)
    r = int(color_hex[1:3], 16) / 255
    g = int(color_hex[3:5], 16) / 255
    b = int(color_hex[5:7], 16) / 255
    c.setFillColorRGB(r, g, b)
    c.roundRect(x, y, 40 * mm, 15 * mm, 3 * mm, fill=1, stroke=0)
    initiales = "".join(
        [w[0] for w in company.raison_sociale.split()[:2] if w]
    ).upper()
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(x + 20 * mm, y + 4 * mm, initiales)


def _draw_signature(c: canvas.Canvas, x: float, y: float) -> None:
    """Dessine une signature manuscrite simulée (courbe de Bézier)."""
    c.setStrokeColor(colors.HexColor("#1B2A4A"))
    c.setLineWidth(1.2)
    p = c.beginPath()
    p.moveTo(x, y)
    cx1 = x + random.uniform(10, 25) * mm
    cy1 = y + random.uniform(3, 8) * mm
    cx2 = x + random.uniform(25, 45) * mm
    cy2 = y - random.uniform(3, 8) * mm
    ex = x + random.uniform(45, 60) * mm
    ey = y + random.uniform(-2, 2) * mm
    p.curveTo(cx1, cy1, cx2, cy2, ex, ey)
    c.drawPath(p, fill=0, stroke=1)


def generate_facture(
    company: Company,
    output_path: str,
    coherent: bool = True,
    doc_index: int = 1,
    tva_rate: float = TVA_DEFAULT,
) -> dict:
    """
    Génère un PDF de facture A4 et retourne les champs attendus (ground truth).

    Args:
        company: entreprise émettrice
        output_path: chemin de sortie du PDF
        coherent: si False, introduit une incohérence (SIRET ou TVA)
        doc_index: numéro séquentiel pour le numéro de facture
        tva_rate: taux de TVA à appliquer

    Returns:
        dict des champs attendus (ground truth)
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    # ── Numéro de facture ──
    date_emission = date.today() - timedelta(days=random.randint(0, 60))
    num_facture = f"FAC-{date_emission.year}-{doc_index:04d}"

    # ── Valeurs pour les lignes de prestation ──
    nb_lignes = random.randint(3, 8)
    prestations = []
    designations = [
        "Prestation de conseil", "Développement logiciel", "Maintenance serveur",
        "Audit sécurité", "Formation Python", "Intégration API",
        "Support technique", "Migration cloud", "Analyse de données",
        "Design UX/UI", "Rédaction technique", "Tests automatisés",
    ]
    for _ in range(nb_lignes):
        designation = random.choice(designations)
        qte = random.randint(1, 20)
        pu = round(random.uniform(50, 2000), 2)
        total_ligne = round(qte * pu, 2)
        prestations.append((designation, qte, pu, total_ligne))

    montant_ht = round(sum(p[3] for p in prestations), 2)
    montant_tva = round(montant_ht * tva_rate, 2)
    montant_ttc = round(montant_ht + montant_tva, 2)

    # ── Incohérences volontaires ──
    siret_affiche = company.siret
    tva_affichee = montant_tva
    if not coherent:
        anomaly_type = random.choice(["siret", "tva"])
        if anomaly_type == "siret":
            siret_affiche = str(random.randint(10000000000000, 99999999999999))
        else:
            tva_affichee = round(montant_tva * random.uniform(1.1, 1.5), 2)
            montant_ttc = round(montant_ht + tva_affichee, 2)

    # ── Dessin du PDF ──
    # En-tête
    _draw_logo(c, company, 20 * mm, height - 35 * mm)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(70 * mm, height - 22 * mm, company.raison_sociale)
    c.setFont("Helvetica", 9)
    c.drawString(70 * mm, height - 27 * mm, company.adresse_rue)
    c.drawString(
        70 * mm, height - 32 * mm,
        f"{company.adresse_cp} {company.adresse_ville}",
    )

    # Titre FACTURE
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, height - 55 * mm, "FACTURE")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 62 * mm, f"N° {num_facture}")
    c.drawString(
        20 * mm, height - 68 * mm,
        f"Date : {date_emission.strftime('%d/%m/%Y')}",
    )

    # Infos client (fictif)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(120 * mm, height - 55 * mm, "DESTINATAIRE")
    c.setFont("Helvetica", 9)
    c.drawString(120 * mm, height - 62 * mm, "Client Exemple SA")
    c.drawString(120 * mm, height - 67 * mm, "12 rue de la Paix")
    c.drawString(120 * mm, height - 72 * mm, "75002 Paris")

    # ── Tableau des prestations ──
    table_top = height - 90 * mm
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.rect(20 * mm, table_top - 7 * mm, 170 * mm, 8 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(22 * mm, table_top - 5 * mm, "Désignation")
    c.drawString(105 * mm, table_top - 5 * mm, "Qté")
    c.drawString(125 * mm, table_top - 5 * mm, "P.U. (€)")
    c.drawString(155 * mm, table_top - 5 * mm, "Total (€)")

    c.setFillColor(colors.HexColor("#2D3748"))
    c.setFont("Helvetica", 9)
    y_pos = table_top - 15 * mm
    for i, (desig, qte, pu, total) in enumerate(prestations):
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#F8F9FA"))
            c.rect(20 * mm, y_pos - 3 * mm, 170 * mm, 7 * mm, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#2D3748"))
        c.drawString(22 * mm, y_pos, desig[:40])
        c.drawRightString(115 * mm, y_pos, str(qte))
        c.drawRightString(142 * mm, y_pos, f"{pu:,.2f}")
        c.drawRightString(185 * mm, y_pos, f"{total:,.2f}")
        y_pos -= 8 * mm

    # ── Totaux ──
    y_pos -= 10 * mm
    c.setLineWidth(0.5)
    c.setStrokeColor(colors.HexColor("#E2E8F0"))
    c.line(120 * mm, y_pos + 5 * mm, 190 * mm, y_pos + 5 * mm)

    c.setFont("Helvetica", 10)
    c.drawString(120 * mm, y_pos, f"Total HT :")
    c.drawRightString(185 * mm, y_pos, f"{montant_ht:,.2f} €")
    y_pos -= 7 * mm
    c.drawString(120 * mm, y_pos, f"TVA ({tva_rate*100:.1f}%) :")
    c.drawRightString(185 * mm, y_pos, f"{tva_affichee:,.2f} €")
    y_pos -= 7 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(120 * mm, y_pos, "Total TTC :")
    c.drawRightString(185 * mm, y_pos, f"{montant_ttc:,.2f} €")

    # ── Mentions légales ──
    y_pos -= 25 * mm
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(20 * mm, y_pos, f"SIRET : {siret_affiche}")
    c.drawString(20 * mm, y_pos - 4 * mm, f"TVA Intra : {company.tva_intra}")
    c.drawString(
        20 * mm, y_pos - 8 * mm,
        f"IBAN : {company.iban}  —  BIC : {company.bic}",
    )
    c.drawString(
        20 * mm, y_pos - 12 * mm,
        f"{company.raison_sociale} — Capital {company.capital_social:,} €",
    )
    c.drawString(
        20 * mm, y_pos - 16 * mm,
        "En cas de retard de paiement, une pénalité de 3× le taux d'intérêt légal sera appliquée.",
    )

    # Signature
    _draw_signature(c, 130 * mm, y_pos - 15 * mm)

    c.save()

    # ── Ground truth ──
    return {
        "type": "facture",
        "num_facture": num_facture,
        "siret": company.siret,
        "siret_affiche": siret_affiche,
        "tva_intra": company.tva_intra,
        "raison_sociale": company.raison_sociale,
        "montant_ht": montant_ht,
        "tva": montant_tva,
        "tva_affichee": tva_affichee,
        "montant_ttc": montant_ttc,
        "date_emission": date_emission.strftime("%d/%m/%Y"),
        "iban": company.iban,
        "bic": company.bic,
        "nb_lignes": nb_lignes,
        "tva_rate": tva_rate,
        "coherent": coherent,
    }
