import os
import random
import json
from faker import Faker
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
import cv2
import numpy as np
from datetime import datetime, timedelta
from pdf2image import convert_from_path
from dotenv import load_dotenv

fake = Faker('fr_FR')
load_dotenv()

POPPLER_PATH = os.getenv("POPPLER_PATH")

# ─────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────

def generate_siret() -> str:
    siren = str(random.randint(100_000_000, 999_999_999))
    nic = str(random.randint(10_000, 99_999))
    return siren + nic


def generate_company() -> dict:
    return {
        'raison_sociale': fake.company(),
        'siret': generate_siret(),
        'adresse': fake.address().replace('\n', ', '),
        'iban': fake.iban(),
        'bic': random.choice(['BNPAFRPP', 'CEPAFRPP', 'AGRIFRPP', 'CMCIFRPP']),
        'tva_intra': f"FR{random.randint(10,99)}{str(random.randint(100_000_000, 999_999_999))}",
    }


def save_ground_truth(doc_id: str, doc_type: str, scenario: str,
                      doc: dict, anomalies: list = []) -> None:
    degradation = 'noisy' if scenario == 'D' else 'none'
    data = {
        'document_id': doc_id,
        'type': doc_type,
        'scenario': scenario,
        'degradation': degradation,
        'expected_fields': doc,
        'expected_anomalies': anomalies,
    }
    with open(f"dataset/labels/{doc_id}.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def draw_separator(c: canvas.Canvas, y: float, width: float = 500) -> None:
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(50, y, 50 + width, y)


def draw_header_band(c: canvas.Canvas, title: str, subtitle: str = "") -> float:
    """Bande d'en-tête bleue, retourne le y courant après la bande."""
    c.setFillColorRGB(0.1, 0.3, 0.6)
    c.rect(0, 800, A4[0], 42, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 815, title)
    if subtitle:
        c.setFont("Helvetica", 10)
        c.drawString(50, 805, subtitle)
    c.setFillColor(colors.black)
    return 780.0


def field(c: canvas.Canvas, label: str, value: str, x: float, y: float,
          label_width: float = 160) -> float:
    """Affiche label: valeur et retourne le nouveau y."""
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x, y, f"{label} :")
    c.setFont("Helvetica", 9)
    c.drawString(x + label_width, y, str(value))
    return y - 16


def section_title(c: canvas.Canvas, title: str, y: float) -> float:
    c.setFillColorRGB(0.1, 0.3, 0.6)
    c.rect(50, y - 3, 500, 16, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(55, y, title)
    c.setFillColor(colors.black)
    return y - 22


# ─────────────────────────────────────────
# Générateurs de PDF par type
# ─────────────────────────────────────────

def create_pdf_facture(doc: dict, emetteur: dict, client: dict, filename: str) -> None:
    c = canvas.Canvas(filename, pagesize=A4)
    y = draw_header_band(c, "FACTURE", f"N° FAC-{random.randint(1000,9999)}")

    # Émetteur
    y = section_title(c, "ÉMETTEUR", y - 10)
    y = field(c, "Raison sociale", emetteur['raison_sociale'], 50, y)
    y = field(c, "SIRET", doc['siret_emetteur'], 50, y)
    y = field(c, "N° TVA Intracommunautaire", emetteur['tva_intra'], 50, y)
    y = field(c, "Adresse", emetteur['adresse'], 50, y)
    y = field(c, "IBAN", emetteur['iban'], 50, y)
    y = field(c, "BIC", emetteur['bic'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    # Client
    y = section_title(c, "CLIENT", y - 5)
    y = field(c, "Raison sociale", client['raison_sociale'], 50, y)
    y = field(c, "SIRET", doc['siret_client'], 50, y)
    y = field(c, "Adresse", client['adresse'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    # Informations facture
    y = section_title(c, "DÉTAIL DE LA FACTURE", y - 5)
    y = field(c, "Date d'émission", doc['date_emission'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 20

    # Tableau montants
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(50, y - 60, 500, 65, fill=1, stroke=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, y - 5, "Désignation")
    c.drawString(400, y - 5, "Montant")
    draw_separator(c, y - 10, 500)

    c.setFont("Helvetica", 10)
    c.drawString(60, y - 25, "Prestation de services")
    c.drawRightString(545, y - 25, f"{doc['montant_ht']:.2f} EUR")
    draw_separator(c, y - 32, 500)

    c.setFont("Helvetica", 9)
    c.drawString(350, y - 45, "Montant HT :")
    c.drawRightString(545, y - 45, f"{doc['montant_ht']:.2f} EUR")
    c.drawString(350, y - 55, "TVA (20%) :")
    c.drawRightString(545, y - 55, f"{doc['tva']:.2f} EUR")

    y -= 65
    c.setFillColorRGB(0.1, 0.3, 0.6)
    c.rect(50, y - 20, 500, 22, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(300, y - 14, "MONTANT TTC :")
    c.drawRightString(545, y - 14, f"{doc['ttc']:.2f} EUR")
    c.setFillColor(colors.black)

    y -= 30
    c.setFont("Helvetica", 9)
    c.drawString(50, y - 10, f"Net à payer : {doc['ttc']:.2f} EUR")

    c.save()


def create_pdf_devis(doc: dict, emetteur: dict, filename: str) -> None:
    c = canvas.Canvas(filename, pagesize=A4)
    y = draw_header_band(c, "DEVIS", f"N° DEV-{random.randint(1000,9999)}")

    y = section_title(c, "PRESTATAIRE", y - 10)
    y = field(c, "Raison sociale", emetteur['raison_sociale'], 50, y)
    y = field(c, "SIRET", doc['siret_emetteur'], 50, y)
    y = field(c, "Adresse", emetteur['adresse'], 50, y)
    y = field(c, "N° TVA Intracommunautaire", emetteur['tva_intra'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    y = section_title(c, "INFORMATIONS DU DEVIS", y - 5)
    y = field(c, "Date du devis", doc['date_devis'], 50, y)
    y = field(c, "Valable jusqu'au", doc['date_validite'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 20

    # Tableau
    c.setFillColorRGB(0.1, 0.3, 0.6)
    c.rect(50, y, 500, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(55, y + 5, "Désignation")
    c.drawString(300, y + 5, "Qté")
    c.drawString(360, y + 5, "Prix unitaire HT")
    c.drawString(470, y + 5, "Total HT")
    c.setFillColor(colors.black)

    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(55, y, doc['designation'])
    c.drawString(300, y, str(doc['quantite']))
    c.drawString(360, y, f"{doc['prix_unitaire']:.2f} EUR")
    c.drawString(470, y, f"{doc['total_ht']:.2f} EUR")

    y -= 25
    draw_separator(c, y)
    y -= 15

    c.setFont("Helvetica", 9)
    c.drawString(350, y, "Montant HT :")
    c.drawRightString(545, y, f"{doc['total_ht']:.2f} EUR")
    y -= 15
    c.drawString(350, y, "TVA (20%) :")
    c.drawRightString(545, y, f"{doc['tva']:.2f} EUR")
    y -= 15

    c.setFillColorRGB(0.1, 0.3, 0.6)
    c.rect(50, y - 5, 500, 18, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(300, y + 2, "Montant TTC :")
    c.drawRightString(545, y + 2, f"{doc['ttc']:.2f} EUR")
    c.setFillColor(colors.black)

    y -= 30
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(50, y, "Bon pour accord : ___________________________     Date : _______________")

    c.save()


def create_pdf_attestation_siret(doc: dict, filename: str) -> None:
    c = canvas.Canvas(filename, pagesize=A4)
    y = draw_header_band(c, "AVIS DE SITUATION AU RÉPERTOIRE SIRENE",
                         "Institut National de la Statistique et des Études Économiques — INSEE")

    y -= 20
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(50, y, "Cet avis certifie l'existence légale de l'entreprise ou de l'établissement.")
    c.setFillColor(colors.black)

    y -= 20
    y = section_title(c, "IDENTIFICATION DE L'ÉTABLISSEMENT", y - 5)
    y = field(c, "Dénomination (Raison sociale)", doc['raison_sociale'], 50, y)
    y = field(c, "N° SIRET", doc['siret'], 50, y)
    y = field(c, "Code APE", f"{random.randint(1000,9999)}{random.choice('ABCDEFGHIJKLMNOP')}", 50, y)
    y = field(c, "Adresse", doc['adresse'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    y = section_title(c, "VALIDITÉ DE L'AVIS", y - 5)
    y = field(c, "Date de délivrance", doc['date_delivrance'], 50, y)
    y = field(c, "Date d'expiration", doc['date_expiration'], 50, y)

    y -= 20
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(50, y, "Document généré automatiquement depuis le répertoire SIRENE — INSEE")
    c.setFillColor(colors.black)
    c.save()


def create_pdf_attestation_urssaf(doc: dict, filename: str) -> None:
    c = canvas.Canvas(filename, pagesize=A4)
    y = draw_header_band(c, "ATTESTATION DE VIGILANCE",
                         "Union de Recouvrement des cotisations de Sécurité Sociale et d'Allocations Familiales")

    y -= 15
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    lines = [
        "L'URSSAF atteste que l'employeur ci-dessous est à jour de ses obligations déclaratives",
        "et de paiement à l'égard de l'organisme.",
    ]
    for line in lines:
        c.drawString(50, y, line)
        y -= 14
    c.setFillColor(colors.black)

    y -= 10
    y = section_title(c, "IDENTIFICATION DE L'ENTREPRISE", y - 5)
    y = field(c, "Raison sociale", doc['raison_sociale'], 50, y)
    y = field(c, "N° SIRET", doc['siret'], 50, y)
    y = field(c, "N° d'attestation URSSAF", str(doc['numero_attestation']), 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    y = section_title(c, "PÉRIODE DE VALIDITÉ", y - 5)
    y = field(c, "Date de début de validité", doc['date_debut_validite'], 50, y)
    y = field(c, "Date de fin de validité", doc['date_fin_validite'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 20

    c.setFont("Helvetica", 9)
    c.drawString(50, y, "Cotisations sociales : À JOUR")

    y -= 30
    c.setFont("Helvetica-Bold", 9)
    c.drawString(50, y, "Cette attestation est établie conformément aux articles L.243-15 et D.8222-5 du Code du travail.")

    c.save()


def create_pdf_kbis(doc: dict, filename: str) -> None:
    c = canvas.Canvas(filename, pagesize=A4)
    y = draw_header_band(c, "EXTRAIT KBIS",
                         "Registre du Commerce et des Sociétés — Greffe du Tribunal de Commerce")

    y -= 15
    c.setFont("Helvetica-Oblique", 9)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.drawString(50, y,
                 "Ce document certifie l'immatriculation de la société au Registre du Commerce et des Sociétés (RCS).")
    c.setFillColor(colors.black)

    y -= 20
    y = section_title(c, "IDENTIFICATION DE LA SOCIÉTÉ", y - 5)
    y = field(c, "Dénomination (Raison sociale)", doc['raison_sociale'], 50, y)
    y = field(c, "Forme juridique", doc['forme_juridique'], 50, y)
    y = field(c, "Capital social", doc['capital_social'], 50, y)
    y = field(c, "N° SIREN", doc['siren'], 50, y)
    y = field(c, "N° SIRET (siège)", doc['siret'], 50, y)
    y = field(c, "Date d'immatriculation", doc['date_immatriculation'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    y = section_title(c, "DIRIGEANT", y - 5)
    y = field(c, "Nom du dirigeant", doc['dirigeant'], 50, y)
    y = field(c, "Qualité", "Gérant", 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 20

    c.setFont("Helvetica", 9)
    c.drawString(50, y, f"Greffe du Tribunal de Commerce — RCS {fake.city()}")
    y -= 14
    c.drawString(50, y, f"Date d'immatriculation : {doc['date_immatriculation']}")

    c.save()


def create_pdf_rib(doc: dict, filename: str) -> None:
    c = canvas.Canvas(filename, pagesize=A4)
    y = draw_header_band(c, "RELEVÉ D'IDENTITÉ BANCAIRE (RIB)",
                         "Document confidentiel — à ne pas divulguer")

    y -= 10
    y = section_title(c, "IDENTIFICATION DU TITULAIRE", y - 10)
    y = field(c, "Titulaire du compte", doc['titulaire'], 50, y)
    y = field(c, "N° SIRET associé", doc['siret_associe'], 50, y)

    y -= 10
    draw_separator(c, y)
    y -= 15

    y = section_title(c, "COORDONNÉES BANCAIRES", y - 5)
    y = field(c, "Domiciliation bancaire", doc['domiciliation_bancaire'], 50, y)
    y = field(c, "IBAN", doc['iban'], 50, y)
    y = field(c, "BIC / SWIFT", doc['bic'], 50, y)

    y -= 20
    draw_separator(c, y)
    y -= 20

    # Représentation graphique du RIB
    c.setFillColorRGB(0.95, 0.95, 0.95)
    c.rect(50, y - 40, 500, 42, fill=1, stroke=1)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(60, y - 10, "Banque")
    c.drawString(160, y - 10, "Guichet")
    c.drawString(260, y - 10, "N° de compte")
    c.drawString(420, y - 10, "Clé RIB")
    draw_separator(c, y - 16, 500)
    c.setFont("Helvetica", 9)
    # Parse IBAN: FR76 BBBB GGGG NNNN NNNN NNNN NCC
    iban_clean = doc['iban'].replace(' ', '')
    c.drawString(60, y - 30, iban_clean[4:9])
    c.drawString(160, y - 30, iban_clean[9:14])
    c.drawString(260, y - 30, iban_clean[14:25])
    c.drawString(420, y - 30, iban_clean[25:27] if len(iban_clean) >= 27 else "XX")

    c.save()


# ─────────────────────────────────────────
# Dégradation image (scénario D)
# ─────────────────────────────────────────

def degrade_image(pdf_path: str, output_path: str, level: str = 'medium') -> None:
    """Convertit le PDF en image et applique des dégradations visuelles."""
    kwargs = {}
    if POPPLER_PATH:
        kwargs['poppler_path'] = POPPLER_PATH
    images = convert_from_path(pdf_path, dpi=200, **kwargs)
    img_pil = images[0]
    img = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]

    # Rotation aléatoire
    angle = random.uniform(-15, 15)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1)
    img = cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))

    # Flou gaussien
    ksize = {'light': 3, 'medium': 5, 'heavy': 7}[level]
    img = cv2.GaussianBlur(img, (ksize, ksize), 0)

    # Bruit gaussien
    noise = np.random.normal(0, 15, img.shape).astype(np.uint8)
    img = cv2.add(img, noise)

    # Réduction contraste
    img = cv2.convertScaleAbs(img, alpha=0.85, beta=10)

    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 60])


# ─────────────────────────────────────────
# Génération document selon type
# ─────────────────────────────────────────

def generate_document(doc_type: str, emetteur: dict, client: dict = None,
                      coherent: bool = True) -> dict:
    today = datetime.today()
    if doc_type == 'facture':
        ht = round(random.uniform(100, 5000), 2)
        tva_rate = 0.20
        tva = round(ht * tva_rate, 2)
        ttc = round(ht + tva, 2)
        if not coherent:
            emetteur['siret'] = generate_siret()
            ttc += random.randint(1, 50)
        return {
            'siret_emetteur': emetteur['siret'],
            'siret_client': client['siret'] if client else generate_siret(),
            'montant_ht': ht,
            'tva': tva,
            'ttc': ttc,
            'date_emission': today.strftime("%Y-%m-%d"),
        }
    elif doc_type == 'devis':
        qty = random.randint(1, 50)
        unit = round(random.uniform(10, 500), 2)
        total_ht = round(qty * unit, 2)
        tva = round(total_ht * 0.20, 2)
        ttc = round(total_ht + tva, 2)
        valid_date = today + timedelta(days=30)
        if not coherent:
            ttc += 5
        return {
            'siret_emetteur': emetteur['siret'],
            'date_devis': today.strftime("%Y-%m-%d"),
            'date_validite': valid_date.strftime("%Y-%m-%d"),
            'designation': fake.bs(),
            'quantite': qty,
            'prix_unitaire': unit,
            'total_ht': total_ht,
            'tva': tva,
            'ttc': ttc,
        }
    elif doc_type == 'siret':
        expiration = today + timedelta(days=365)
        if not coherent:
            expiration = today - timedelta(days=30)
        return {
            'siret': emetteur['siret'],
            'raison_sociale': emetteur['raison_sociale'],
            'adresse': emetteur['adresse'],
            'date_delivrance': today.strftime("%Y-%m-%d"),
            'date_expiration': expiration.strftime("%Y-%m-%d"),
        }
    elif doc_type == 'urssaf':
        end_date = today + timedelta(days=365)
        if not coherent:
            end_date = today - timedelta(days=30)
        return {
            'siret': emetteur['siret'],
            'raison_sociale': emetteur['raison_sociale'],
            'date_debut_validite': today.strftime("%Y-%m-%d"),
            'date_fin_validite': end_date.strftime("%Y-%m-%d"),
            'numero_attestation': fake.random_number(digits=8),
        }
    elif doc_type == 'kbis':
        immatriculation = today - timedelta(days=random.randint(0, 365))
        if not coherent:
            emetteur['raison_sociale'] = fake.company()
        return {
            'siret': emetteur['siret'],
            'siren': emetteur['siret'][:9],
            'raison_sociale': emetteur['raison_sociale'],
            'forme_juridique': random.choice(['SARL', 'SAS', 'SA', 'EURL', 'SNC']),
            'capital_social': f"{random.randint(1_000, 100_000)} €",
            'date_immatriculation': immatriculation.strftime("%Y-%m-%d"),
            'dirigeant': fake.name(),
        }
    elif doc_type == 'rib':
        iban = emetteur['iban'] if coherent else generate_company()['iban']
        return {
            'iban': iban,
            'bic': emetteur['bic'],
            'titulaire': emetteur['raison_sociale'],
            'domiciliation_bancaire': fake.company(),
            'siret_associe': emetteur['siret'],
        }


# Dispatch PDF → fonction de création
PDF_CREATORS = {
    'facture': lambda doc, emetteur, client, path: create_pdf_facture(doc, emetteur, client, path),
    'devis': lambda doc, emetteur, client, path: create_pdf_devis(doc, emetteur, path),
    'siret': lambda doc, emetteur, client, path: create_pdf_attestation_siret(doc, path),
    'urssaf': lambda doc, emetteur, client, path: create_pdf_attestation_urssaf(doc, path),
    'kbis': lambda doc, emetteur, client, path: create_pdf_kbis(doc, path),
    'rib': lambda doc, emetteur, client, path: create_pdf_rib(doc, path),
}

# Noms de fichier courts — les préfixes de fichiers restent inchangés pour ne pas
# casser les fichiers déjà générés (ATTESTATION_SIRET_*, ATTESTATION_URSSAF_*)
DOC_ID_PREFIX = {
    'facture': 'FACTURE',
    'devis': 'DEVIS',
    'siret': 'ATTESTATION_SIRET',
    'urssaf': 'ATTESTATION_URSSAF',
    'kbis': 'KBIS',
    'rib': 'RIB',
}

# Compteurs par type (pour les IDs uniques)
_counters: dict = {}


def next_id(doc_type: str) -> str:
    prefix = DOC_ID_PREFIX[doc_type]
    _counters[prefix] = _counters.get(prefix, 0) + 1
    return f"{prefix}_{_counters[prefix]:03d}"


# ─────────────────────────────────────────
# Génération du dataset complet
# ─────────────────────────────────────────

def generate_dataset(n: int = 100) -> None:
    os.makedirs("dataset/raw", exist_ok=True)
    os.makedirs("dataset/noisy", exist_ok=True)
    os.makedirs("dataset/labels", exist_ok=True)

    doc_types = [
        'facture', 'devis', 'siret',
        'urssaf', 'kbis', 'rib',
    ]

    generated = 0
    for _ in range(n):
        scenario = random.choices(['A', 'B', 'C', 'D'], weights=[30, 30, 20, 20])[0]
        emetteur = generate_company()
        client = generate_company()
        coherent = scenario == 'A'

        doc_type = random.choice(doc_types)
        doc = generate_document(doc_type, emetteur, client, coherent=coherent)
        doc_id = next_id(doc_type)

        pdf_path = f"dataset/raw/{doc_id}.pdf"
        PDF_CREATORS[doc_type](doc, emetteur, client, pdf_path)
        save_ground_truth(doc_id, doc_type, scenario, doc)

        # Scénario D : version dégradée (simulation scan)
        if scenario == 'D':
            img_path = f"dataset/noisy/{doc_id}.jpg"
            try:
                degrade_image(pdf_path, img_path, level='medium')
            except Exception as e:
                print(f"  [WARN] Dégradation impossible pour {doc_id}: {e}")

        generated += 1
        print(f"  [{generated:3d}/{n}] {doc_id}  (scénario {scenario})")

    print(f"\nDataset généré : {generated} documents dans dataset/")


if __name__ == "__main__":
    generate_dataset(100)
    print("Dataset complet généré avec succès !")
