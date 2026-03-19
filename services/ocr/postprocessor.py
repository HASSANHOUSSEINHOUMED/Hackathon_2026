"""
Post-processeur OCR pour corriger les erreurs courantes
avant l'extraction d'entités.
"""
import logging
import re
from typing import Callable

logger = logging.getLogger("ocr-service.postprocessor")


class OCRPostProcessor:
    """
    Corrige les erreurs OCR courantes dans le texte extrait.
    
    Applique des corrections contextuelles pour améliorer
    la qualité de l'extraction d'entités.
    """
    
    # Corrections de caractères générales
    CHAR_CORRECTIONS = {
        "\xa0": " ",      # Espace insécable
        "»": "",          # Guillemets parasites
        "«": "",
        "…": "...",
        "—": "-",
        "–": "-",
        "'": "'",
        "'": "'",
        """: '"',
        """: '"',
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
    }
    
    # Corrections de mots métier courants
    WORD_CORRECTIONS = {
        # SIRET
        "STRET": "SIRET",
        "SIREI": "SIRET",
        "5IRET": "SIRET",
        "S1RET": "SIRET",
        "SIRËT": "SIRET",
        "SJRET": "SIRET",
        "51RET": "SIRET",
        # SIREN
        "STREN": "SIREN",
        "5IREN": "SIREN",
        "S1REN": "SIREN",
        # TVA
        "T.V.A.": "TVA",
        "T.V.A": "TVA",
        "TYA": "TVA",
        "IVA": "TVA",
        # IBAN
        "IBAM": "IBAN",
        "1BAN": "IBAN",
        "LBAN": "IBAN",
        "I8AN": "IBAN",
        # BIC
        "B1C": "BIC",
        "81C": "BIC",
        # URSSAF
        "URSSAE": "URSSAF",
        "URSAF": "URSSAF",
        "URSSÀF": "URSSAF",
        "URS5AF": "URSSAF",
        # Autres
        "FACTURE": "FACTURE",
        "FACIURE": "FACTURE",
        "FAC7URE": "FACTURE",
        "KBTS": "KBIS",
        "K8IS": "KBIS",
        "KB1S": "KBIS",
        "K-8IS": "K-BIS",
    }
    
    # Corrections contextuelles pour les chiffres
    # (appliquées uniquement dans un contexte numérique)
    DIGIT_CORRECTIONS = {
        "O": "0",
        "o": "0",
        "Q": "0",
        "D": "0",
        "l": "1",
        "I": "1",
        "i": "1",
        "|": "1",
        "!": "1",
        "S": "5",
        "s": "5",
        "B": "8",
        "Z": "2",
        "z": "2",
        "G": "6",
        "g": "9",
        "q": "9",
        "A": "4",
        "T": "7",
    }
    
    def __init__(self):
        # Compiler les patterns regex pour performance
        self._word_pattern = re.compile(
            r"\b(" + "|".join(re.escape(k) for k in self.WORD_CORRECTIONS.keys()) + r")\b",
            re.IGNORECASE
        )
    
    def process(self, text: str) -> str:
        """
        Applique toutes les corrections au texte OCR.
        
        Pipeline :
        1. Normalisation des caractères spéciaux
        2. Correction des mots métier
        3. Normalisation des espaces
        4. Correction contextuelle des chiffres (SIRET, IBAN, etc.)
        """
        if not text:
            return ""
        
        # 1. Corrections de caractères
        result = self._apply_char_corrections(text)
        
        # 2. Corrections de mots métier
        result = self._apply_word_corrections(result)
        
        # 3. Normalisation des espaces
        result = self._normalize_spaces(result)
        
        # 4. Corrections contextuelles des chiffres
        result = self._fix_numeric_contexts(result)
        
        # 5. Nettoyage final
        result = self._final_cleanup(result)
        
        return result
    
    def _apply_char_corrections(self, text: str) -> str:
        """Remplace les caractères problématiques."""
        for old, new in self.CHAR_CORRECTIONS.items():
            text = text.replace(old, new)
        return text
    
    def _apply_word_corrections(self, text: str) -> str:
        """Corrige les mots métier mal reconnus."""
        def replace_word(match):
            word = match.group(1)
            # Trouver la correction en ignorant la casse
            for wrong, correct in self.WORD_CORRECTIONS.items():
                if word.upper() == wrong.upper():
                    return correct
            return word
        
        return self._word_pattern.sub(replace_word, text)
    
    def _normalize_spaces(self, text: str) -> str:
        """Normalise les espaces multiples et les lignes."""
        # Supprimer espaces multiples
        text = re.sub(r"[ \t]+", " ", text)
        # Supprimer espaces en début/fin de ligne
        text = re.sub(r"^ +| +$", "", text, flags=re.MULTILINE)
        # Limiter les lignes vides consécutives
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    
    def _fix_numeric_contexts(self, text: str) -> str:
        """
        Corrige les erreurs OCR dans les contextes numériques.
        
        Applique les corrections de chiffres uniquement après
        des labels comme SIRET, IBAN, montant, etc.
        """
        # Patterns pour identifier les contextes numériques
        contexts = [
            # SIRET : corriger les 14 caractères après le label
            (r"(SIRET\s*:?\s*)([A-Za-z0-9\s]{10,20})", self._fix_siret_like),
            # SIREN : corriger les 9 caractères après le label
            (r"(SIREN\s*:?\s*)([A-Za-z0-9\s]{7,12})", self._fix_siren_like),
            # IBAN : corriger les caractères après FR
            (r"(IBAN\s*:?\s*)(FR\s*[A-Za-z0-9\s]{20,35})", self._fix_iban_like),
            # TVA intracommunautaire
            (r"(TVA\s*(?:intra(?:communautaire)?)?\s*:?\s*)(FR\s*[A-Za-z0-9\s]{10,15})", self._fix_tva_like),
            # Montants : après Total, HT, TTC, etc.
            (r"((?:Total|Montant|HT|TTC|TVA)\s*:?\s*)([A-Za-z0-9\s,\.]{3,20}\s*€?)", self._fix_amount_like),
        ]
        
        result = text
        for pattern, fixer in contexts:
            result = re.sub(pattern, fixer, result, flags=re.IGNORECASE)
        
        return result
    
    def _fix_siret_like(self, match) -> str:
        """Corrige un SIRET potentiel."""
        prefix = match.group(1)
        value = match.group(2)
        
        # Garder uniquement les chiffres potentiels
        fixed = self._apply_digit_corrections(value)
        fixed = re.sub(r"[^0-9\s]", "", fixed)
        
        return prefix + fixed
    
    def _fix_siren_like(self, match) -> str:
        """Corrige un SIREN potentiel."""
        return self._fix_siret_like(match)
    
    def _fix_iban_like(self, match) -> str:
        """Corrige un IBAN potentiel."""
        prefix = match.group(1)
        value = match.group(2)
        
        # IBAN peut contenir des lettres (mais pas n'importe lesquelles)
        fixed = self._apply_digit_corrections_selective(value)
        
        return prefix + fixed
    
    def _fix_tva_like(self, match) -> str:
        """Corrige un numéro TVA potentiel."""
        prefix = match.group(1)
        value = match.group(2)
        
        # FR + 11 chiffres
        if value.upper().startswith("FR"):
            rest = value[2:]
            fixed = self._apply_digit_corrections(rest)
            fixed = re.sub(r"[^0-9\s]", "", fixed)
            return prefix + "FR" + fixed
        
        return match.group(0)
    
    def _fix_amount_like(self, match) -> str:
        """Corrige un montant potentiel."""
        prefix = match.group(1)
        value = match.group(2)
        
        # Garder chiffres, virgule, point, espace, euro
        fixed = self._apply_digit_corrections(value)
        fixed = re.sub(r"[^0-9,.\s€]", "", fixed)
        
        return prefix + fixed
    
    def _apply_digit_corrections(self, text: str) -> str:
        """Applique les corrections de chiffres à tout le texte."""
        result = ""
        for c in text:
            result += self.DIGIT_CORRECTIONS.get(c, c)
        return result
    
    def _apply_digit_corrections_selective(self, text: str) -> str:
        """
        Applique les corrections de chiffres sélectivement.
        Conserve les lettres valides dans un IBAN.
        """
        result = ""
        in_letter_zone = False
        
        for i, c in enumerate(text):
            # Les 4 premiers caractères après FR sont des lettres (code banque)
            # puis c'est principalement des chiffres
            if c.upper() in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" and i < 10:
                result += c.upper()
            elif c in self.DIGIT_CORRECTIONS and c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz":
                result += self.DIGIT_CORRECTIONS[c]
            else:
                result += c
        
        return result
    
    def _final_cleanup(self, text: str) -> str:
        """Nettoyage final du texte."""
        # Supprimer les caractères de contrôle
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        
        # S'assurer que le texte ne commence/finit pas par des espaces
        return text.strip()


# Instance globale
postprocessor = OCRPostProcessor()
