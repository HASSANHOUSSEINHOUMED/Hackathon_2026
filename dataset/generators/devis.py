"""
Générateur de devis PDF réalistes avec ReportLab.
"""
import random
from datetime import date, timedelta

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from company_factory import Company
from config import LOGO_COLORS, TVA_DEFAULT


def generate_devis(
    company: Company,
    output_path: str,
    coherent: bool = True,
    expired: bool = False,
    doc_index: int = 1,
    tva_rate: float = TVA_DEFAULT,
) -> dict:
    """
    Génère un PDF de devis A4 et retourne le ground truth.

    Args:
        company: entreprise émettrice
        output_path: chemin du PDF
        coherent: si False, introduit une incohérence
        expired: si True, la date de validité est dans le passé
        doc_index: numéro séquentiel
        tva_rate: taux de TVA à appliquer
    """
    width, height = A4
    c = canvas.Canvas(output_path, pagesize=A4)

    date_emission = date.today() - timedelta(days=random.randint(5, 60))
    if expired:
        date_validite = date_emission + timedelta(days=15)  # déjà passée
    else:
        date_validite = date.today() + timedelta(days=30)

    num_devis = f"DEV-{date_emission.year}-{doc_index:04d}"

    # Logo
    color_hex = random.choice(LOGO_COLORS)
    r, g, b = (int(color_hex[i:i+2], 16) / 255 for i in (1, 3, 5))
    c.setFillColorRGB(r, g, b)
    c.roundRect(20 * mm, height - 35 * mm, 40 * mm, 15 * mm, 3 * mm, fill=1, stroke=0)
    initiales = "".join([w[0] for w in company.raison_sociale.split()[:2] if w]).upper()
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(40 * mm, height - 31 * mm, initiales)

    # En-tête entreprise
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(70 * mm, height - 22 * mm, company.raison_sociale)
    c.setFont("Helvetica", 9)
    c.drawString(70 * mm, height - 27 * mm, company.adresse_rue)
    c.drawString(70 * mm, height - 32 * mm, f"{company.adresse_cp} {company.adresse_ville}")
    c.drawString(70 * mm, height - 37 * mm, f"SIRET : {company.siret}")

    # Titre
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(20 * mm, height - 55 * mm, "DEVIS")
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, height - 62 * mm, f"N° {num_devis}")
    c.drawString(20 * mm, height - 68 * mm, f"Date : {date_emission.strftime('%d/%m/%Y')}")
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#E63946") if expired else colors.HexColor("#00C896"))
    c.drawString(
        20 * mm, height - 75 * mm,
        f"Ce devis est valable jusqu'au {date_validite.strftime('%d/%m/%Y')}",
    )

    # Destinataire
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(120 * mm, height - 55 * mm, "DESTINATAIRE")
    c.setFont("Helvetica", 9)
    c.drawString(120 * mm, height - 62 * mm, "Client Prospect SARL")
    c.drawString(120 * mm, height - 67 * mm, "45 avenue des Champs-Élysées")
    c.drawString(120 * mm, height - 72 * mm, "75008 Paris")

    # Tableau des prestations
    nb_lignes = random.randint(3, 8)
    designations = [
        "Étude préliminaire", "Développement front-end", "Développement back-end",
        "Intégration système", "Tests de recette", "Formation utilisateurs",
        "Documentation technique", "Déploiement production", "Support 3 mois",
        "Licence logicielle annuelle", "Hébergement cloud", "Accompagnement projet",
    ]
    prestations = []
    for _ in range(nb_lignes):
        desig = random.choice(designations)
        qte = random.randint(1, 15)
        pu = round(random.uniform(100, 3000), 2)
        total = round(qte * pu, 2)
        prestations.append((desig, qte, pu, total))

    montant_ht = round(sum(p[3] for p in prestations), 2)
    montant_tva = round(montant_ht * tva_rate, 2)
    montant_ttc = round(montant_ht + montant_tva, 2)

    siret_affiche = company.siret
    if not coherent:
        siret_affiche = str(random.randint(10000000000000, 99999999999999))

    # Tableau
    table_top = height - 95 * mm
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

    # Totaux
    y_pos -= 10 * mm
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(120 * mm, y_pos, "Total HT :")
    c.drawRightString(185 * mm, y_pos, f"{montant_ht:,.2f} €")
    y_pos -= 7 * mm
    c.drawString(120 * mm, y_pos, f"TVA ({tva_rate*100:.1f}%) :")
    c.drawRightString(185 * mm, y_pos, f"{montant_tva:,.2f} €")
    y_pos -= 7 * mm
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.HexColor("#1B2A4A"))
    c.drawString(120 * mm, y_pos, "Total TTC :")
    c.drawRightString(185 * mm, y_pos, f"{montant_ttc:,.2f} €")

    # Case "Bon pour accord"
    y_pos -= 25 * mm
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(colors.HexColor("#2D3748"))
    c.drawString(20 * mm, y_pos, "☐ Bon pour accord")
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y_pos - 6 * mm, "Date et signature du client :")
    c.setStrokeColor(colors.HexColor("#CBD5E0"))
    c.setDash(3, 3)
    c.line(20 * mm, y_pos - 18 * mm, 90 * mm, y_pos - 18 * mm)
    c.setDash()

    # Mentions SIRET en bas
    y_pos -= 35 * mm
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#718096"))
    c.drawString(20 * mm, y_pos, f"SIRET : {siret_affiche} — TVA Intra : {company.tva_intra}")

    c.save()

    return {
        "type": "devis",
        "num_devis": num_devis,
        "siret": company.siret,
        "siret_affiche": siret_affiche,
        "tva_intra": company.tva_intra,
        "raison_sociale": company.raison_sociale,
        "montant_ht": montant_ht,
        "tva": montant_tva,
        "montant_ttc": montant_ttc,
        "date_emission": date_emission.strftime("%d/%m/%Y"),
        "date_validite": date_validite.strftime("%d/%m/%Y"),
        "expired": expired,
        "coherent": coherent,
    }
