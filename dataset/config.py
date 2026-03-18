"""
Configuration globale pour la génération du dataset.
"""
from pathlib import Path

# Nombre de documents par type
N_DOCS: int = 15

# Répartition des scénarios (doit sommer à 1.0)
SCENARIOS: dict[str, float] = {
    "coherent": 0.30,   # Documents corrects et cohérents
    "mismatch": 0.30,   # Incohérences volontaires (SIRET, montants…)
    "expired": 0.20,    # Dates d'expiration dépassées
    "noisy": 0.20,      # Dégradations visuelles (scan, bruit…)
}

# Types de documents générés
DOC_TYPES: list[str] = [
    "facture",
    "devis",
    "attestation_urssaf",
    "attestation_siret",
    "kbis",
    "rib",
]

# Taux de TVA possibles en France
TVA_RATES: list[float] = [0.055, 0.10, 0.20]

# Taux de TVA par défaut
TVA_DEFAULT: float = 0.20

# Chemins de sortie
OUTPUT_DIR: Path = Path("output")
RAW_DIR: Path = OUTPUT_DIR / "raw"
NOISY_DIR: Path = OUTPUT_DIR / "noisy"
LABELS_DIR: Path = OUTPUT_DIR / "labels"

# Niveaux de dégradation (pour le scénario "noisy")
DEGRADATION_LEVELS: list[str] = ["light", "medium", "heavy"]

# Codes NAF courants avec libellés
CODES_NAF: list[tuple[str, str]] = [
    ("6201Z", "Programmation informatique"),
    ("6202A", "Conseil en systèmes et logiciels informatiques"),
    ("4321A", "Travaux d'installation électrique"),
    ("4120A", "Construction de maisons individuelles"),
    ("4399C", "Travaux de maçonnerie générale"),
    ("5610A", "Restauration traditionnelle"),
    ("4711B", "Commerce d'alimentation générale"),
    ("8559A", "Formation continue d'adultes"),
    ("7022Z", "Conseil pour les affaires et autres conseils de gestion"),
    ("4941A", "Transports routiers de fret interurbains"),
    ("6311Z", "Traitement de données, hébergement et activités connexes"),
    ("7112B", "Ingénierie, études techniques"),
    ("4690Z", "Commerce de gros non spécialisé"),
    ("8121Z", "Nettoyage courant des bâtiments"),
    ("6910Z", "Activités juridiques"),
    ("6920Z", "Activités comptables"),
    ("4399A", "Travaux d'étanchéification"),
    ("2562B", "Mécanique industrielle"),
    ("4332A", "Travaux de menuiserie bois et PVC"),
    ("7010Z", "Activités des sièges sociaux"),
]

# BIC de banques françaises courantes
BICS_FR: list[str] = [
    "BNPAFRPP",  # BNP Paribas
    "CEPAFRPP",  # Caisse d'Épargne
    "CRLYFRPP",  # Crédit Lyonnais (LCL)
    "SOGEFRPP",  # Société Générale
    "AGRIFRPP",  # Crédit Agricole
    "CMCIFRPP",  # CIC
    "BPCEFRPP",  # BPCE
    "CCBPFRPP",  # Banque Populaire
    "TRNOFRP1",  # La Banque Postale
    "CMCIFR2A",  # Crédit Mutuel
]

# Formes juridiques possibles
FORMES_JURIDIQUES: list[str] = ["SAS", "SARL", "SA", "EURL", "SNC"]

# Villes de greffes pour le Kbis
VILLES_GREFFES: list[str] = [
    "Paris", "Lyon", "Marseille", "Bordeaux", "Toulouse",
    "Nantes", "Lille", "Strasbourg", "Nice", "Montpellier",
    "Rennes", "Grenoble", "Rouen", "Toulon", "Clermont-Ferrand",
]

# Couleurs pour les logos procéduraux (hex RGB)
LOGO_COLORS: list[str] = [
    "#1B2A4A", "#00C896", "#E63946", "#F4A261", "#2A9D8F",
    "#264653", "#E76F51", "#606C38", "#283618", "#DDA15E",
    "#6D6875", "#B5838D", "#457B9D", "#1D3557", "#A8DADC",
]
