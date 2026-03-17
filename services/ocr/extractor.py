"""
extractor.py — Extraction d'entités depuis le texte OCR
Classe : EntityExtractor

Notes regex :
- Les espaces insécables (\xa0) sont normalisés avant traitement
- Les erreurs OCR fréquentes (0↔O, 1↔l) sont gérées via des patterns tolérants
"""

import re
import logging
from typing import Optional

import spacy

logger = logging.getLogger(__name__)

# Chargement du modèle spaCy une seule fois au niveau module
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("fr_core_news_md")
    return _nlp


# Correspondance mois français → numéro
MOIS_FR = {
    "janvier": "01", "février": "02", "mars": "03", "avril": "04",
    "mai": "05", "juin": "06", "juillet": "07", "août": "08",
    "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
}


def _normalise(text: str) -> str:
    """Remplace les espaces insécables par des espaces normaux."""
    return text.replace("\xa0", " ").replace("\u202f", " ")


def _ocr_digit(c: str) -> str:
    """Retourne un pattern regex tolérant aux confusions OCR 0↔O et 1↔l."""
    if c == "0":
        return "[0Oo]"
    if c == "1":
        return "[1lI]"
    return re.escape(c)


class EntityExtractor:
    """Extrait les entités structurées d'un texte issu de l'OCR."""

    # ------------------------------------------------------------------
    # SIRET
    # ------------------------------------------------------------------

    def extract_siret(self, text: str) -> Optional[str]:
        """
        Extrait et valide un numéro SIRET (14 chiffres) via l'algorithme de Luhn.
        Gère les espaces entre groupes et les erreurs OCR O↔0 / l↔1.
        """
        text = _normalise(text)

        # Pattern : 14 chiffres avec séparateurs optionnels (espace, tiret, point)
        # Tolérance OCR : O↔0, l/I↔1
        raw_pattern = r"(?:SIRET|N[°o]\s*SIRET|Siret\s*:?)[\s:]*([0-9OolI]{3}[\s\-.]?[0-9OolI]{3}[\s\-.]?[0-9OolI]{3}[\s\-.]?[0-9OolI]{3}[\s\-.]?[0-9OolI]{2})"
        generic_pattern = r"\b([0-9OolI]{3}[\s\-.]?[0-9OolI]{3}[\s\-.]?[0-9OolI]{3}[\s\-.]?[0-9OolI]{3}[\s\-.]?[0-9OolI]{2})\b"

        candidates = []

        for pattern in (raw_pattern, generic_pattern):
            for m in re.finditer(pattern, text, re.IGNORECASE):
                raw = m.group(1)
                digits = self._ocr_to_digits(raw)
                # Luhn s'applique sur le SIREN (9 premiers chiffres du SIRET)
                if len(digits) == 14 and self._luhn_check(digits[:9]):
                    candidates.append(digits)

        return candidates[0] if candidates else None

    @staticmethod
    def _ocr_to_digits(raw: str) -> str:
        """Convertit un string OCR (avec O, l, I) en chiffres purs."""
        cleaned = re.sub(r"[\s\-.]", "", raw)
        return cleaned.translate(str.maketrans("OolI", "0011"))

    @staticmethod
    def _luhn_check(number: str) -> bool:
        """Vérifie un numéro via l'algorithme de Luhn."""
        if not number.isdigit():
            return False
        total = 0
        reverse = number[::-1]
        for i, digit in enumerate(reverse):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        return total % 10 == 0

    # ------------------------------------------------------------------
    # TVA intracommunautaire
    # ------------------------------------------------------------------

    def extract_tva_intra(self, text: str) -> Optional[str]:
        """
        Extrait un numéro de TVA intracommunautaire français.
        Format : FR + 2 chiffres/lettres + 9 chiffres (SIREN).
        """
        text = _normalise(text)
        # FR suivi de 2 caractères alphanum puis 9 chiffres (avec espaces tolérés)
        pattern = r"\b(FR[\s]?[0-9A-Z]{2}[\s]?[0-9]{3}[\s]?[0-9]{3}[\s]?[0-9]{3})\b"
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            tva = re.sub(r"\s", "", m.group(1)).upper()
            return tva
        return None

    # ------------------------------------------------------------------
    # Montants
    # ------------------------------------------------------------------

    def extract_montants(self, text: str) -> dict:
        """
        Extrait les montants HT, TVA et TTC depuis le texte.

        Returns:
            {"ht": float | None, "tva": float | None, "ttc": float | None}
        """
        text = _normalise(text)
        result: dict = {"ht": None, "tva": None, "ttc": None}

        # Pattern de montant : 1 234,56 € ou 1234.56 EUR ou 1 234 €
        amount_re = r"([\d\s]+[,.]?\d*)\s*(?:€|EUR|euros?)"

        # Labels associés à chaque champ
        label_map = {
            "ht": [
                r"(?:montant\s+)?H\.?T\.?",
                r"hors\s+tax[ée]s?",
                r"base\s+(?:imposable|HT)",
            ],
            "tva": [
                r"T\.?V\.?A\.?(?:\s+\d+[\.,]\d+\s*%)?",
                r"taxe\s+(?:sur\s+la\s+)?valeur\s+ajout[ée]e?",
            ],
            "ttc": [
                r"(?:montant\s+)?T\.?T\.?C\.?",
                r"net\s+[àa]\s+payer",
                r"total\s+(?:TTC|[àa]\s+payer)",
            ],
        }

        for field, labels in label_map.items():
            for label in labels:
                pattern = rf"(?:{label})\s*:?\s*{amount_re}"
                m = re.search(pattern, text, re.IGNORECASE)
                if m:
                    result[field] = self._parse_montant(m.group(1))
                    break

        return result

    @staticmethod
    def _parse_montant(raw: str) -> Optional[float]:
        """Convertit une chaîne de montant en float."""
        cleaned = re.sub(r"\s", "", raw)
        # Remplacer la virgule décimale par un point
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Dates
    # ------------------------------------------------------------------

    def extract_dates(self, text: str) -> dict:
        """
        Extrait les dates d'émission, d'expiration et de validité.

        Formats supportés :
        - DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        - YYYY-MM-DD (ISO 8601 — format des PDFs générés par Rôle 1)
        - "10 mars 2025" (littéral français)

        Returns:
            {"emission": str | None, "expiration": str | None, "validite": str | None}
        """
        text = _normalise(text)
        result: dict = {"emission": None, "expiration": None, "validite": None}

        # Pattern date numérique : DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
        date_num_re = r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})"
        # Pattern date ISO : YYYY-MM-DD (format Rôle 1)
        date_iso_re = r"(\d{4})-(\d{2})-(\d{2})"
        # Pattern date littérale : "10 mars 2025" ou "10 janvier 2025"
        date_lit_re = (
            r"(\d{1,2})\s+("
            + "|".join(MOIS_FR.keys())
            + r")\s+(\d{4})"
        )

        def parse_date_num(m) -> str:
            return f"{m.group(1).zfill(2)}/{m.group(2).zfill(2)}/{m.group(3)}"

        def parse_date_iso(m) -> str:
            """Convertit YYYY-MM-DD → DD/MM/YYYY."""
            return f"{m.group(3)}/{m.group(2)}/{m.group(1)}"

        def parse_date_lit(m) -> str:
            day = m.group(1).zfill(2)
            month = MOIS_FR.get(m.group(2).lower(), "??")
            year = m.group(3)
            return f"{day}/{month}/{year}"

        label_map = {
            "emission": [
                r"[ée]mis\s+le",
                r"date\s+(?:d[''e]\s*)?(?:[ée]mission|facture|document)",
                r"fait\s+le",
                r"le\s+(?=\d)",
                # Labels des PDFs générés par Rôle 1
                r"date\s+du\s+devis",
                r"date\s+de\s+d[eé]livrance",
                r"date\s+de\s+d[eé]but\s+de\s+validit[eé]",
                r"date\s+d[''']?\s*immatriculation",
            ],
            "expiration": [
                r"date\s+d[''e]\s*expiration",
                r"expire?\s+le",
                r"valable?\s+jusqu[''au]+",
                r"[ée]ch[ée]ance",
                # Labels des PDFs générés par Rôle 1
                r"date\s+de\s+fin\s+de\s+validit[eé]",
            ],
            "validite": [
                r"valable?\s+(?:jusqu[''au]+\s+le\s+)?",
                r"validit[ée]\s*:?",
                r"offre\s+valable",
                r"valable\s+jusqu[''']?au",
            ],
        }

        for field, labels in label_map.items():
            if result[field]:
                continue
            for label in labels:
                # Chercher label suivi d'une date numérique (DD/MM/YYYY)
                pattern_num = rf"(?:{label})\s*:?\s*{date_num_re}"
                m = re.search(pattern_num, text, re.IGNORECASE)
                if m:
                    result[field] = parse_date_num(m)
                    break

                # Chercher label suivi d'une date ISO (YYYY-MM-DD)
                pattern_iso = rf"(?:{label})\s*:?\s*{date_iso_re}"
                m = re.search(pattern_iso, text, re.IGNORECASE)
                if m:
                    result[field] = parse_date_iso(m)
                    break

                # Chercher label suivi d'une date littérale
                pattern_lit = rf"(?:{label})\s*:?\s*{date_lit_re}"
                m = re.search(pattern_lit, text, re.IGNORECASE)
                if m:
                    result[field] = parse_date_lit(m)
                    break

        # Fallback : première date numérique du texte → émission
        if not result["emission"]:
            m = re.search(date_num_re, text)
            if m:
                result["emission"] = parse_date_num(m)

        # Fallback ISO : première date ISO du texte → émission
        if not result["emission"]:
            m = re.search(date_iso_re, text)
            if m:
                result["emission"] = parse_date_iso(m)

        return result

    # ------------------------------------------------------------------
    # IBAN
    # ------------------------------------------------------------------

    def extract_iban(self, text: str) -> Optional[str]:
        """
        Extrait et valide un IBAN français (ISO 13616).
        Format : FR + 2 chiffres + 23 caractères alphanumériques.
        """
        text = _normalise(text)

        # Chercher après mots-clés ou directement
        patterns = [
            r"(?:IBAN|RIB|Domiciliation)\s*:?\s*(FR\s*\d{2}(?:\s*[0-9A-Z]{4}){5,6}(?:\s*[0-9A-Z]{1,3})?)",
            r"\b(FR\s*\d{2}(?:\s*[0-9A-Z]{4}){5,6}(?:\s*[0-9A-Z]{1,3})?)\b",
        ]

        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                iban = re.sub(r"\s", "", m.group(1)).upper()
                # Un IBAN FR fait exactement 27 caractères
                if len(iban) == 27 and self._iban_checksum(iban):
                    return iban

        return None

    @staticmethod
    def _iban_checksum(iban: str) -> bool:
        """Vérifie le checksum IBAN selon ISO 13616."""
        # Déplacer les 4 premiers caractères à la fin
        rearranged = iban[4:] + iban[:4]
        # Remplacer les lettres par des chiffres (A=10, B=11, …, Z=35)
        numeric = ""
        for c in rearranged:
            if c.isalpha():
                numeric += str(ord(c) - ord("A") + 10)
            else:
                numeric += c
        try:
            return int(numeric) % 97 == 1
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Raison sociale
    # ------------------------------------------------------------------

    def extract_raison_sociale(self, text: str) -> Optional[str]:
        """
        Extrait la raison sociale selon 3 stratégies (ordre de priorité) :
        1. Mots-clés explicites (Société :, Dénomination :, etc.)
        2. NER spaCy (entités de type ORG)
        3. Heuristique : ligne en MAJUSCULES de 3 à 50 chars avant le SIRET
        """
        text = _normalise(text)

        # Stratégie 1 : mots-clés
        keyword_pattern = (
            r"(?:Soci[ée]t[ée]\s*:|D[ée]nomination\s*sociale?\s*:|"
            r"Raison\s+sociale\s*:|Entreprise\s*:|Nom\s+(?:commercial|entreprise)\s*:)"
            r"\s*(.+)"
        )
        m = re.search(keyword_pattern, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip().split("\n")[0].strip()
            if 3 <= len(candidate) <= 100:
                return candidate

        # Stratégie 2 : NER spaCy
        nlp = _get_nlp()
        doc = nlp(text[:2000])  # Limiter pour les performances
        orgs = [ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"]
        if orgs:
            # Retourner l'entité ORG la plus longue (souvent la raison sociale complète)
            return max(orgs, key=len)

        # Stratégie 3 : heuristique MAJUSCULES avant SIRET
        siret_pos = re.search(r"SIRET", text, re.IGNORECASE)
        if siret_pos:
            before_siret = text[: siret_pos.start()]
            lines = [l.strip() for l in before_siret.split("\n") if l.strip()]
            for line in reversed(lines):
                if 3 <= len(line) <= 50 and line == line.upper() and re.search(r"[A-Z]", line):
                    return line

        return None

    # ------------------------------------------------------------------
    # Extraction globale
    # ------------------------------------------------------------------

    def extract_all(self, text: str) -> dict:
        """
        Appelle toutes les méthodes d'extraction et calcule un score de confiance.

        Returns:
            Dictionnaire avec toutes les entités + extraction_confidence.
        """
        siret = self.extract_siret(text)
        tva_intra = self.extract_tva_intra(text)
        montants = self.extract_montants(text)
        dates = self.extract_dates(text)
        iban = self.extract_iban(text)
        raison_sociale = self.extract_raison_sociale(text)

        # Champs critiques pour les rôles 4 et 5 — toujours présents (null si absent)
        entities = {
            "siret": siret,
            "tva_intra": tva_intra,
            "montant_ht": montants.get("ht"),
            "tva": montants.get("tva"),
            "montant_ttc": montants.get("ttc"),
            "date_emission": dates.get("emission"),
            "date_expiration": dates.get("expiration"),
            "raison_sociale": raison_sociale,
            "iban": iban,
            "bic": None,  # Extrait séparément si nécessaire
        }

        # Calcul du score de confiance : ratio champs trouvés / total attendu
        total_champs = len(entities)
        champs_trouves = sum(1 for v in entities.values() if v is not None)
        extraction_confidence = round(champs_trouves / total_champs, 4)

        return {**entities, "extraction_confidence": extraction_confidence}
