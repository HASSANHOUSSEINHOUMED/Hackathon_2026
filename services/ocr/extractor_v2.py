"""
Extracteur d'entités robuste v2.0
Combine regex avancés, validation stricte et extraction contextuelle.
"""
import logging
import re
from typing import Any

logger = logging.getLogger("ocr-service.extractor")


def _clean_text(text: str) -> str:
    """Normalise les espaces et caractères spéciaux fréquents en OCR."""
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _normalize_number(text: str) -> str:
    """Normalise un texte en supprimant tout sauf les chiffres."""
    return re.sub(r"[^0-9]", "", text)


def luhn_check(number: str) -> bool:
    """Vérifie le checksum de Luhn pour un numéro SIRET/SIREN."""
    number = _normalize_number(number)
    if not number:
        return False
    
    digits = [int(d) for d in number]
    # Somme impaire : digits en position impaire (depuis la fin)
    odd = digits[-1::-2]
    # Somme paire : digits en position paire doublés
    even_doubled = []
    for d in digits[-2::-2]:
        doubled = d * 2
        even_doubled.append(doubled - 9 if doubled > 9 else doubled)
    
    total = sum(odd) + sum(even_doubled)
    return total % 10 == 0


def iban_check(iban: str) -> bool:
    """Vérifie le checksum IBAN (algorithme ISO 13616)."""
    iban = re.sub(r"[\s\-]", "", iban).upper()
    if len(iban) < 15 or len(iban) > 34:
        return False
    
    # Réarranger : mettre les 4 premiers caractères à la fin
    rearranged = iban[4:] + iban[:4]
    
    # Convertir lettres en chiffres (A=10, B=11, ..., Z=35)
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
    except (ValueError, OverflowError):
        return False


def validate_date(day: int, month: int, year: int) -> bool:
    """Valide une date (jour/mois cohérents, année raisonnable)."""
    if not (1 <= month <= 12):
        return False
    if not (1900 <= year <= 2100):
        return False
    
    days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    # Année bissextile
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        days_in_month[1] = 29
    
    return 1 <= day <= days_in_month[month - 1]


class EntityExtractor:
    """
    Extracteur d'entités robuste avec validation stricte.
    
    Stratégie :
    1. Extraction par patterns regex multiples (du plus spécifique au générique)
    2. Validation de format pour chaque candidat
    3. Validation sémantique (Luhn, IBAN checksum, dates cohérentes)
    4. Extraction contextuelle (labels → valeurs)
    """

    # ═══════════════════════════════════════════════════════════════════
    # PATTERNS SIRET/SIREN
    # ═══════════════════════════════════════════════════════════════════
    
    SIRET_PATTERNS = [
        # Avec label explicite (tolère apostrophes, accents, OCR errors)
        r"(?:SIRET|N[°º'`]?\s*SIRET|Siret|siret)\s*[:;]?\s*(\d[\d\s\.\-]{12,20})",
        # Format groupé standard : 999 999 999 99999
        r"\b(\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{5})\b",
        # Format compact sans séparateurs
        r"\b(\d{14})\b",
        # Après "n°" générique suivi de 14 chiffres
        r"(?:N[°º]|n[°º])\s*[:;]?\s*(\d{14})",
        # Dans un contexte "immatriculation", "RCS", "SIREN"
        r"(?:immatricul[ée]|RCS\s*\w+)\s*[:;]?\s*(\d[\d\s]{12,20})",
    ]
    
    SIREN_PATTERNS = [
        r"(?:SIREN|Siren|siren)\s*[:;]?\s*(\d[\d\s]{7,12})",
        r"\b(\d{3}[\s\.\-]?\d{3}[\s\.\-]?\d{3})\b(?!\d)",
    ]
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERNS TVA INTRACOMMUNAUTAIRE
    # ═══════════════════════════════════════════════════════════════════
    
    TVA_PATTERNS = [
        # Avec label
        r"(?:TVA\s*(?:intra(?:communautaire)?)?|N[°º]?\s*TVA|Identifiant\s*TVA)\s*[:;]?\s*(FR\s*\d{2}\s*\d{9})",
        # Format compact
        r"\b(FR\s?\d{2}\s?\d{9})\b",
        # Avec espaces groupés
        r"\b(FR\s*\d{2}\s+\d{3}\s+\d{3}\s+\d{3})\b",
    ]
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERNS MONTANTS
    # ═══════════════════════════════════════════════════════════════════
    
    # Pattern générique pour un montant
    AMOUNT_PATTERN = r"(\d{1,3}(?:[\s\u00a0]?\d{3})*(?:[,\.]\d{1,2})?)\s*(?:€|EUR|euros?)?"
    
    # Labels pour identifier le type de montant
    AMOUNT_LABELS = {
        "ht": [
            r"(?:total\s*)?(?:hors\s*taxe|h\.?t\.?|ht)",
            r"montant\s*h\.?t\.?",
            r"sous[\-\s]?total",
            r"base\s*h\.?t\.?",
        ],
        "tva": [
            r"(?:montant\s*)?tva\s*(?:\(?\d+(?:[,\.]\d+)?\s*%?\)?)?",
            r"taxe\s*(?:\(?\d+(?:[,\.]\d+)?\s*%?\)?)?",
            r"dont\s*tva",
        ],
        "ttc": [
            r"(?:total|montant)?\s*(?:toutes\s*taxes\s*comprises|t\.?t\.?c\.?|ttc)",
            r"net\s*[àa]\s*payer",
            r"montant\s*(?:total|d[ûu])",
            r"total\s*(?:g[ée]n[ée]ral|facture)?",
            r"[àa]\s*payer",
            r"reste\s*[àa]\s*payer",
        ],
    }
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERNS DATES
    # ═══════════════════════════════════════════════════════════════════
    
    DATE_NUMERIC = r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})"
    
    MOIS_FR = {
        "janvier": "01", "février": "02", "fevrier": "02", "mars": "03",
        "avril": "04", "mai": "05", "juin": "06", "juillet": "07",
        "août": "08", "aout": "08", "septembre": "09", "octobre": "10",
        "novembre": "11", "décembre": "12", "decembre": "12",
    }
    
    DATE_LABELS = {
        "emission": [
            r"(?:date\s*)?(?:d['']?)?[ée]mission",
            r"[ée]mis(?:e)?\s*le",
            r"date\s*(?:de\s*)?facture",
            r"le\s*(?=\d)",
            r"date\s*[:;]",
            r"du\s*(?=\d)",
            r"fait\s*(?:à|le)",
        ],
        "expiration": [
            r"(?:date\s*)?(?:d['']?)?expiration",
            r"expire\s*le",
            r"valable\s*jusqu",
            r"valid(?:e|it[ée])?\s*jusqu",
            r"fin\s*de\s*validit[ée]",
            r"[ée]ch[ée]ance",
        ],
        "validite": [
            r"valable\s*(?:du|à\s*partir)",
            r"validit[ée]",
            r"d[ée]but\s*de\s*validit[ée]",
        ],
    }
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERNS IBAN/BIC
    # ═══════════════════════════════════════════════════════════════════
    
    IBAN_PATTERNS = [
        # Avec label
        r"(?:IBAN|Compte|RIB|Domiciliation)\s*[:;]?\s*(FR\s*\d{2}[\s\d]{10,30}[A-Z0-9]*)",
        # Format groupé : FR76 1234 5678 9012 3456 7890 123
        r"\b(FR\s*\d{2}\s+(?:[\dA-Z]{4}\s+){5}[\dA-Z]{3})\b",
        # Format compact
        r"\b(FR\d{2}[A-Z0-9]{23})\b",
        # Format semi-compact
        r"\b(FR\s*\d{2}\s*[A-Z0-9]{10,25})\b",
    ]
    
    BIC_PATTERNS = [
        r"(?:BIC|SWIFT|Code\s*BIC)\s*[:;]?\s*([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)",
        r"\b([A-Z]{4}FR[A-Z0-9]{2}(?:[A-Z0-9]{3})?)\b",
    ]
    
    # ═══════════════════════════════════════════════════════════════════
    # PATTERNS RAISON SOCIALE
    # ═══════════════════════════════════════════════════════════════════
    
    RS_PATTERNS = [
        r"(?:Soci[ée]t[ée]|D[ée]nomination|Raison\s*sociale|Nom|Entreprise)\s*[:;]?\s*(.+?)(?=\s*(?:SIRET|TVA|SIREN|RCS|$|\n))",
        r"(?:^|\n)([A-Z][A-Z\s\-&\.]{5,50}(?:SARL|SAS|SA|SCI|EURL|SASU)?)\s*(?=\n|SIRET|$)",
    ]

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
            except (OSError, ImportError):
                logger.warning("Modèle spaCy fr_core_news_md non disponible")
                self._nlp = False
        return self._nlp

    # ═══════════════════════════════════════════════════════════════════
    # MÉTHODES D'EXTRACTION
    # ═══════════════════════════════════════════════════════════════════

    def extract_siret(self, text: str) -> str | None:
        """
        Extrait un numéro SIRET (14 chiffres) validé par Luhn.
        """
        text = _clean_text(text)
        
        for pattern in self.SIRET_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                candidate = _normalize_number(match.group(1))
                
                # Doit avoir exactement 14 chiffres
                if len(candidate) == 14:
                    if luhn_check(candidate):
                        logger.debug("SIRET trouvé et validé: %s", candidate)
                        return candidate
                    else:
                        logger.debug("SIRET candidat invalide (Luhn): %s", candidate)
        
        return None

    def extract_siren(self, text: str, siret: str | None = None) -> str | None:
        """
        Extrait un numéro SIREN (9 chiffres).
        Si un SIRET est fourni, extrait les 9 premiers chiffres.
        """
        if siret and len(siret) == 14:
            return siret[:9]
        
        text = _clean_text(text)
        
        for pattern in self.SIREN_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                candidate = _normalize_number(match.group(1))
                if len(candidate) == 9:
                    if luhn_check(candidate):
                        return candidate
        
        return None

    def extract_tva_intra(self, text: str) -> str | None:
        """Extrait le numéro de TVA intracommunautaire (FR + 2 + 9 chiffres)."""
        text = _clean_text(text)
        
        for pattern in self.TVA_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = re.sub(r"\s", "", match.group(1)).upper()
                # Validation format : FR + 11 chiffres
                if re.match(r"^FR\d{11}$", candidate):
                    # Validation clé TVA (les 2 chiffres après FR)
                    siren = candidate[4:]
                    cle = int(candidate[2:4])
                    cle_calculee = (12 + 3 * (int(siren) % 97)) % 97
                    if cle == cle_calculee:
                        return candidate
                    # Accepter quand même si le SIREN semble valide
                    elif luhn_check(siren):
                        logger.debug("TVA avec clé incorrecte mais SIREN valide: %s", candidate)
                        return candidate
        
        return None

    def extract_montants(self, text: str) -> dict[str, float | None]:
        """
        Extrait les montants HT, TVA et TTC du texte.
        Gère les formats français et anglais.
        """
        text = _clean_text(text)
        result: dict[str, float | None] = {"ht": None, "tva": None, "ttc": None}
        
        for key, labels in self.AMOUNT_LABELS.items():
            for label_pattern in labels:
                # Construire le pattern complet
                full_pattern = rf"{label_pattern}\s*[:;]?\s*{self.AMOUNT_PATTERN}"
                
                for match in re.finditer(full_pattern, text, re.IGNORECASE):
                    raw = match.group(1)
                    value = self._parse_amount(raw)
                    
                    if value is not None and result[key] is None:
                        result[key] = value
                        logger.debug("Montant %s trouvé: %.2f", key, value)
                        break
                
                if result[key] is not None:
                    break
        
        # Validation croisée des montants
        result = self._validate_amounts(result)
        
        return result

    def _parse_amount(self, raw: str) -> float | None:
        """Parse un montant dans différents formats."""
        if not raw:
            return None
        
        # Nettoyer les espaces
        cleaned = re.sub(r"[\s\u00a0]", "", raw)
        
        # Détecter le format
        if "," in cleaned and "." in cleaned:
            # Format avec séparateur de milliers
            if cleaned.rfind(",") > cleaned.rfind("."):
                # Format FR : 1.234,56
                cleaned = cleaned.replace(".", "").replace(",", ".")
            else:
                # Format EN : 1,234.56
                cleaned = cleaned.replace(",", "")
        elif "," in cleaned:
            # Virgule comme séparateur décimal (FR)
            cleaned = cleaned.replace(",", ".")
        
        try:
            value = float(cleaned)
            # Validation : montant raisonnable
            if 0.01 <= value <= 100_000_000:
                return round(value, 2)
        except ValueError:
            pass
        
        return None

    def _validate_amounts(self, amounts: dict[str, float | None]) -> dict[str, float | None]:
        """
        Valide la cohérence des montants HT + TVA = TTC.
        Corrige si possible.
        """
        ht = amounts.get("ht")
        tva = amounts.get("tva")
        ttc = amounts.get("ttc")
        
        # Si on a les 3, vérifier la cohérence
        if ht and tva and ttc:
            expected_ttc = round(ht + tva, 2)
            if abs(expected_ttc - ttc) > 0.02:
                logger.warning("Incohérence montants: HT(%.2f) + TVA(%.2f) = %.2f != TTC(%.2f)",
                              ht, tva, expected_ttc, ttc)
        
        # Si on a HT et TTC mais pas TVA, calculer
        if ht and ttc and not tva:
            amounts["tva"] = round(ttc - ht, 2)
        
        # Si on a HT et TVA mais pas TTC, calculer
        if ht and tva and not ttc:
            amounts["ttc"] = round(ht + tva, 2)
        
        return amounts

    def extract_dates(self, text: str) -> dict[str, str | None]:
        """
        Extrait les dates pertinentes avec validation.
        """
        text = _clean_text(text)
        result: dict[str, str | None] = {
            "emission": None,
            "expiration": None,
            "validite": None,
        }
        
        # Fonction de parsing de date
        def parse_date(match, format_type: str = "numeric") -> str | None:
            try:
                if format_type == "numeric":
                    day = int(match.group(1))
                    month = int(match.group(2))
                    year = int(match.group(3))
                else:  # lettres
                    day = int(match.group(1))
                    month = int(self.MOIS_FR.get(match.group(2).lower(), "00"))
                    year = int(match.group(3))
                
                # Normaliser l'année
                if year < 100:
                    year += 2000 if year < 50 else 1900
                
                # Valider
                if validate_date(day, month, year):
                    return f"{day:02d}/{month:02d}/{year}"
            except (ValueError, TypeError):
                pass
            return None
        
        # Extraire par type de date
        for date_type, labels in self.DATE_LABELS.items():
            for label in labels:
                # Date numérique
                pattern = rf"{label}\s*[:;]?\s*{self.DATE_NUMERIC}"
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    parsed = parse_date(match, "numeric")
                    if parsed and result[date_type] is None:
                        result[date_type] = parsed
                        break
                
                # Date en lettres
                mois_pattern = "|".join(self.MOIS_FR.keys())
                letter_pattern = rf"{label}\s*[:;]?\s*(?:le\s*)?(\d{{1,2}})\s+({mois_pattern})\s+(\d{{2,4}})"
                match = re.search(letter_pattern, text, re.IGNORECASE)
                if match:
                    parsed = parse_date(match, "lettres")
                    if parsed and result[date_type] is None:
                        result[date_type] = parsed
                        break
        
        # Fallback : première date trouvée pour émission
        if result["emission"] is None:
            match = re.search(self.DATE_NUMERIC, text)
            if match:
                parsed = parse_date(match, "numeric")
                if parsed:
                    result["emission"] = parsed
        
        return result

    def extract_iban(self, text: str) -> str | None:
        """Extrait un IBAN français validé."""
        text = _clean_text(text)
        
        for pattern in self.IBAN_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                candidate = re.sub(r"[\s\-]", "", match.group(1)).upper()
                
                # Doit commencer par FR et avoir 27 caractères
                if candidate.startswith("FR") and len(candidate) == 27:
                    if iban_check(candidate):
                        return candidate
                    else:
                        logger.debug("IBAN candidat invalide (checksum): %s", candidate)
        
        return None

    def extract_bic(self, text: str) -> str | None:
        """Extrait un code BIC/SWIFT."""
        text = _clean_text(text)
        
        for pattern in self.BIC_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                candidate = match.group(1).upper()
                # BIC = 8 ou 11 caractères
                if len(candidate) in (8, 11):
                    return candidate
        
        return None

    def extract_raison_sociale(self, text: str) -> str | None:
        """
        Extrait la raison sociale de l'entreprise.
        Combine recherche par mots-clés, NER et heuristiques.
        """
        text = _clean_text(text)
        
        # 1. Recherche par mots-clés
        for pattern in self.RS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                rs = match.group(1).strip()
                # Nettoyer
                rs = re.sub(r"\s+", " ", rs)
                rs = rs.strip(":-;,.")
                if 3 <= len(rs) <= 80:
                    return rs
        
        # 2. NER spaCy
        if self.nlp and self.nlp is not False:
            try:
                doc = self.nlp(text[:2000])
                for ent in doc.ents:
                    if ent.label_ == "ORG":
                        rs = ent.text.strip()
                        if 3 <= len(rs) <= 80:
                            return rs
            except Exception as e:
                logger.debug("Erreur NER: %s", str(e))
        
        # 3. Heuristique : ligne en majuscules
        for line in text.split("\n"):
            line = line.strip()
            if (
                line.isupper()
                and 3 <= len(line) <= 60
                and not line.isdigit()
                and not re.match(r"^(SIRET|SIREN|TVA|IBAN|FACTURE|DEVIS|KBIS)\b", line)
                and not re.match(r"^\d", line)
            ):
                return line
        
        return None

    def extract_all(self, text: str) -> dict[str, Any]:
        """
        Extrait toutes les entités et retourne un dictionnaire unifié.
        """
        siret = self.extract_siret(text)
        siren = self.extract_siren(text, siret)
        tva_intra = self.extract_tva_intra(text)
        montants = self.extract_montants(text)
        dates = self.extract_dates(text)
        iban = self.extract_iban(text)
        bic = self.extract_bic(text)
        raison_sociale = self.extract_raison_sociale(text)
        
        entities = {
            "siret": siret,
            "siren": siren,
            "tva_intra": tva_intra,
            "montant_ht": montants["ht"],
            "tva": montants["tva"],
            "montant_ttc": montants["ttc"],
            "date_emission": dates["emission"],
            "date_expiration": dates["expiration"],
            "date_validite": dates["validite"],
            "raison_sociale": raison_sociale,
            "iban": iban,
            "bic": bic,
        }
        
        # Score de confiance
        total_fields = len([k for k in entities.keys() if k not in ("siren", "date_validite", "bic")])
        filled = sum(1 for k, v in entities.items() if v is not None and k not in ("siren", "date_validite", "bic"))
        extraction_confidence = filled / total_fields if total_fields > 0 else 0.0
        
        entities["extraction_confidence"] = round(extraction_confidence, 4)
        
        logger.info(
            "Extraction: %d/%d champs (confiance=%.2f)",
            filled, total_fields, extraction_confidence,
        )
        
        return entities
