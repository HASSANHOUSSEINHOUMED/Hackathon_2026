"""
Extracteur d'entités à partir du texte OCR.
Combine regex et spaCy NER pour extraire SIRET, TVA, IBAN, montants, dates, etc.
"""
import logging
import re
from typing import Any

logger = logging.getLogger("ocr-service.extractor")


def _clean_text(text: str) -> str:
    """Normalise les espaces et caractères spéciaux fréquents en OCR."""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fix_ocr_digits(text: str) -> str:
    """Corrige les confusions OCR courantes entre lettres et chiffres."""
    replacements = {
        "O": "0", "o": "0",
        "l": "1", "I": "1",
        "S": "5", "s": "5",
        "B": "8",
    }
    result = ""
    for c in text:
        result += replacements.get(c, c)
    return result


def luhn_check(number: str) -> bool:
    """Vérifie le checksum de Luhn pour un numéro SIRET/SIREN."""
    digits = [int(d) for d in number if d.isdigit()]
    if not digits:
        return False
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd) + sum(sum(divmod(d * 2, 10)) for d in even)
    return total % 10 == 0


def iban_check(iban: str) -> bool:
    """Vérifie le checksum IBAN (algorithme ISO 13616)."""
    iban = iban.replace(" ", "").upper()
    if len(iban) < 15:
        return False
    rearranged = iban[4:] + iban[:4]
    numeric = ""
    for c in rearranged:
        if c.isdigit():
            numeric += c
        elif c.isalpha():
            numeric += str(ord(c) - 55)
        else:
            return False
    try:
        return int(numeric) % 97 == 1
    except ValueError:
        return False


class EntityExtractor:
    """Extrait les entités structurées depuis le texte OCR."""

    def __init__(self) -> None:
        self._nlp = None

    @property
    def nlp(self):
        """Chargement paresseux du modèle spaCy."""
        if self._nlp is None:
            try:
                import spacy
                self._nlp = spacy.load("fr_core_news_md")
                logger.info("Modèle spaCy fr_core_news_md chargé")
            except OSError:
                logger.warning("Modèle spaCy fr_core_news_md non disponible")
                self._nlp = False
        return self._nlp

    def extract_siret(self, text: str) -> str | None:
        """
        Extrait un numéro SIRET (14 chiffres) du texte.
        Tolère les espaces entre groupes de chiffres.
        """
        text = _clean_text(text)

        # Chercher après les mots-clés
        patterns = [
            r"(?:SIRET|N°\s*SIRET|Siret\s*:?)\s*(\d[\d\s]{12,16}\d)",
            r"\b(\d{3}\s?\d{3}\s?\d{3}\s?\d{5})\b",
            r"\b(\d{14})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = re.sub(r"\s", "", match.group(1))
                if len(candidate) == 14 and candidate.isdigit():
                    if luhn_check(candidate):
                        return candidate
                    # Tenter des corrections OCR
                    fixed = _fix_ocr_digits(match.group(1))
                    fixed = re.sub(r"\s", "", fixed)
                    if len(fixed) == 14 and fixed.isdigit() and luhn_check(fixed):
                        return fixed

        return None

    def extract_tva_intra(self, text: str) -> str | None:
        """Extrait le numéro de TVA intracommunautaire (FR + 2 + 9 chiffres)."""
        text = _clean_text(text)
        pattern = r"(?:TVA\s*(?:intra(?:communautaire)?)?[\s:]*)?FR\s*(\d{2})\s*(\d{9})"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"FR{match.group(1)}{match.group(2)}"
        return None

    def extract_montants(self, text: str) -> dict[str, float | None]:
        """
        Extrait les montants HT, TVA et TTC du texte.
        Gère les formats : 1 234,56 € / 1234.56 EUR / 1 234.56
        """
        text = _clean_text(text)
        result: dict[str, float | None] = {"ht": None, "tva": None, "ttc": None}

        # Pattern pour un montant
        montant_pattern = r"(\d[\d\s]*[\.,]\d{2})\s*(?:€|EUR|euros?)?"

        # Associations label → clé
        label_map = {
            "ht": [r"(?:total\s*)?h\.?t\.?", r"hors\s*taxe"],
            "tva": [r"tva\s*(?:\(\d+(?:[\.,]\d+)?\s*%\))?", r"taxe"],
            "ttc": [r"(?:total\s*)?t\.?t\.?c\.?", r"net\s*[àa]\s*payer", r"montant\s*total"],
        }

        for key, labels in label_map.items():
            for label in labels:
                pattern = rf"{label}\s*:?\s*{montant_pattern}"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    raw = match.group(1).replace(" ", "").replace(",", ".")
                    try:
                        result[key] = round(float(raw), 2)
                    except ValueError:
                        pass
                    break

        return result

    def extract_dates(self, text: str) -> dict[str, str | None]:
        """
        Extrait les dates pertinentes (émission, expiration, validité).
        Formats : DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, "le XX mois YYYY"
        """
        text = _clean_text(text)
        result: dict[str, str | None] = {
            "emission": None,
            "expiration": None,
            "validite": None,
        }

        # Mois en lettres
        mois = {
            "janvier": "01", "février": "02", "mars": "03", "avril": "04",
            "mai": "05", "juin": "06", "juillet": "07", "août": "08",
            "septembre": "09", "octobre": "10", "novembre": "11", "décembre": "12",
        }

        date_numeric = r"(\d{2})[/\-\.](\d{2})[/\-\.](\d{4})"
        date_letters = r"(\d{1,2})\s+(" + "|".join(mois.keys()) + r")\s+(\d{4})"

        # Labels pour chaque type de date
        emission_labels = [r"[eé]mis[e]?\s*le", r"date\s*:?", r"date\s*d[''']?\s*[eé]mission", r"du\s*"]
        expiration_labels = [r"date\s*d[''']?\s*expiration", r"expire\s*le", r"valable\s*jusqu", r"date\s*d[''']?\s*[eé]ch[eé]ance"]
        validite_labels = [r"valable\s*jusqu", r"validit[eé]"]

        def find_date_near_label(labels: list[str]) -> str | None:
            for label in labels:
                # Date numérique
                pattern = rf"{label}\s*:?\s*{date_numeric}"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    return f"{match.group(1)}/{match.group(2)}/{match.group(3)}"
                # Date en lettres
                pattern = rf"{label}\s*:?\s*(?:le\s*)?{date_letters}"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    jour = match.group(1).zfill(2)
                    m = mois.get(match.group(2).lower(), "01")
                    return f"{jour}/{m}/{match.group(3)}"
            return None

        result["emission"] = find_date_near_label(emission_labels)
        result["expiration"] = find_date_near_label(expiration_labels)
        result["validite"] = find_date_near_label(validite_labels)

        # Fallback : première date trouvée pour émission
        if result["emission"] is None:
            match = re.search(date_numeric, text)
            if match:
                result["emission"] = f"{match.group(1)}/{match.group(2)}/{match.group(3)}"

        return result

    def extract_iban(self, text: str) -> str | None:
        """Extrait un IBAN français valide (FR + 2 chiffres + 23 alphanum)."""
        text = _clean_text(text)

        patterns = [
            r"(?:IBAN|RIB|Domiciliation)\s*:?\s*(FR\s*\d{2}[\s\d A-Z]{10,30})",
            r"\b(FR\s*\d{2}\s*[\d A-Z]{4}\s*[\d A-Z]{4}\s*[\d A-Z]{4}\s*[\d A-Z]{4}\s*[\d A-Z]{4}\s*[\d A-Z]{3})\b",
            r"\b(FR\d{24,25})\b",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = re.sub(r"\s", "", match.group(1)).upper()
                if iban_check(candidate):
                    return candidate

        return None

    def extract_raison_sociale(self, text: str) -> str | None:
        """
        Extrait la raison sociale en combinant :
        1. Recherche par mots-clés
        2. NER spaCy (entités ORG)
        3. Heuristique (lignes en majuscules)
        """
        text = _clean_text(text)

        # 1. Mots-clés
        keywords = [
            r"(?:Soci[eé]t[eé]|D[eé]nomination|Raison\s*sociale)\s*:?\s*(.+?)(?:\n|$|SIRET|TVA)",
        ]
        for pattern in keywords:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rs = match.group(1).strip()
                if 3 <= len(rs) <= 80:
                    return rs

        # 2. spaCy NER
        if self.nlp and self.nlp is not False:
            doc = self.nlp(text[:2000])  # Limiter pour la performance
            for ent in doc.ents:
                if ent.label_ == "ORG" and 3 <= len(ent.text) <= 80:
                    return ent.text

        # 3. Heuristique : ligne en majuscules avant le SIRET
        lines = text.split("\n")
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (
                stripped.isupper()
                and 3 <= len(stripped) <= 50
                and not stripped.isdigit()
                and not stripped.startswith("SIRET")
                and not stripped.startswith("FACTURE")
            ):
                return stripped

        return None

    def extract_all(self, text: str) -> dict[str, Any]:
        """
        Extrait toutes les entités et retourne un dictionnaire unifié.
        Ajoute un score de confiance d'extraction.
        """
        siret = self.extract_siret(text)
        tva_intra = self.extract_tva_intra(text)
        montants = self.extract_montants(text)
        dates = self.extract_dates(text)
        iban = self.extract_iban(text)
        raison_sociale = self.extract_raison_sociale(text)

        entities = {
            "siret": siret,
            "tva_intra": tva_intra,
            "montant_ht": montants["ht"],
            "tva": montants["tva"],
            "montant_ttc": montants["ttc"],
            "date_emission": dates["emission"],
            "date_expiration": dates["expiration"],
            "date_validite": dates["validite"],
            "raison_sociale": raison_sociale,
            "iban": iban,
        }

        # Calcul de la confiance d'extraction
        total_fields = len(entities)
        filled_fields = sum(1 for v in entities.values() if v is not None)
        extraction_confidence = filled_fields / total_fields if total_fields > 0 else 0.0

        entities["extraction_confidence"] = round(extraction_confidence, 4)

        logger.info(
            "Extraction : %d/%d champs trouvés (confiance=%.2f)",
            filled_fields, total_fields, extraction_confidence,
        )

        return entities
