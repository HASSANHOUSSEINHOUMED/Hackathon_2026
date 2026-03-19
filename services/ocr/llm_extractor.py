"""
Extracteur LLM pour renforcer l'extraction d'entités.
Utilise OpenAI GPT-4o-mini pour corriger et compléter l'extraction regex.
"""
import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger("ocr-service.llm_extractor")

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_ENABLED = bool(OPENAI_API_KEY)


class LLMExtractor:
    """
    Extracteur LLM pour renforcer l'extraction d'entités.
    
    Stratégie :
    1. Reçoit le texte OCR + les entités déjà extraites par regex
    2. Demande au LLM de valider/corriger/compléter
    3. Retourne les entités consolidées avec score de confiance
    """
    
    def __init__(self):
        self._client = None
        self._available = False
        
        if LLM_ENABLED:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=OPENAI_API_KEY)
                self._available = True
                logger.info("LLM Extractor initialisé (modèle: %s)", LLM_MODEL)
            except ImportError:
                logger.warning("OpenAI SDK non installé - LLM extraction désactivée")
            except Exception as e:
                logger.warning("Erreur init OpenAI: %s", str(e))
        else:
            logger.info("LLM Extractor désactivé (OPENAI_API_KEY non configurée)")
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def extract_and_validate(
        self,
        raw_text: str,
        doc_type: str,
        regex_entities: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Extrait et valide les entités via LLM.
        
        Args:
            raw_text: Texte OCR brut (limité à 4000 chars)
            doc_type: Type de document détecté
            regex_entities: Entités déjà extraites par regex
        
        Returns:
            Entités corrigées/complétées avec confiance
        """
        if not self._available:
            return regex_entities
        
        try:
            # Limiter le texte pour économiser les tokens
            text_truncated = raw_text[:4000]
            
            # Construire le prompt
            prompt = self._build_prompt(text_truncated, doc_type, regex_entities)
            
            # Appel LLM
            response = self._client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,  # Très déterministe
                max_tokens=1000,
                response_format={"type": "json_object"},
            )
            
            # Parser la réponse
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info("LLM extraction réussie: %d champs extraits", len(result.get("entities", {})))
            
            return self._merge_results(regex_entities, result.get("entities", {}))
            
        except Exception as e:
            logger.warning("Erreur LLM extraction: %s - fallback regex", str(e))
            return regex_entities
    
    def _system_prompt(self) -> str:
        return """Tu es un expert en extraction d'informations de documents administratifs français.
Tu reçois du texte OCR (potentiellement bruité) et des entités déjà extraites par regex.

Ta tâche :
1. VÉRIFIER les entités existantes (corriger si erreur évidente)
2. EXTRAIRE les entités manquantes
3. VALIDER le format de chaque champ

Règles strictes :
- SIRET : exactement 14 chiffres, doit passer le test de Luhn
- SIREN : les 9 premiers chiffres du SIRET
- TVA intracommunautaire : format FR + 2 chiffres + 9 chiffres (ex: FR12345678901)
- IBAN français : FR + 2 chiffres + 23 caractères alphanumériques
- Montants : nombres décimaux positifs (ex: 1234.56)
- Dates : format DD/MM/YYYY

IMPORTANT : Si tu n'es pas sûr d'une valeur, mets null plutôt qu'une valeur incorrecte.
Retourne UNIQUEMENT un JSON valide."""

    def _build_prompt(self, text: str, doc_type: str, regex_entities: dict) -> str:
        # Formatter les entités regex pour le prompt
        entities_str = json.dumps(regex_entities, indent=2, ensure_ascii=False)
        
        return f"""Document de type : {doc_type}

=== TEXTE OCR ===
{text}

=== ENTITÉS EXTRAITES PAR REGEX ===
{entities_str}

=== TÂCHE ===
Analyse le texte OCR et retourne un JSON avec :
{{
  "entities": {{
    "siret": "14 chiffres ou null",
    "siren": "9 chiffres ou null",
    "tva_intra": "FR + 11 chiffres ou null",
    "raison_sociale": "nom entreprise ou null",
    "montant_ht": nombre ou null,
    "tva": nombre ou null,
    "montant_ttc": nombre ou null,
    "iban": "FR + 25 caractères ou null",
    "bic": "8-11 caractères ou null",
    "date_emission": "DD/MM/YYYY ou null",
    "date_expiration": "DD/MM/YYYY ou null"
  }},
  "corrections": ["liste des corrections apportées"],
  "confidence": 0.0 à 1.0
}}

Vérifie particulièrement :
- SIRET/SIREN : souvent mal lu par OCR (0/O, 1/l, 5/S confondus)
- Montants : bien séparer HT, TVA et TTC
- Dates : ne pas inventer, extraire uniquement si présentes"""

    def _merge_results(
        self,
        regex_entities: dict[str, Any],
        llm_entities: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fusionne les résultats regex et LLM intelligemment.
        
        Stratégie :
        - Si LLM et regex concordent : garder la valeur
        - Si LLM a une valeur et regex null : prendre LLM si format valide
        - Si LLM null et regex a une valeur : garder regex
        - Si LLM et regex diffèrent : privilégier LLM si format valide
        """
        result = dict(regex_entities)
        
        for key, llm_value in llm_entities.items():
            if key not in result:
                continue
                
            regex_value = result.get(key)
            
            # LLM a une valeur
            if llm_value is not None:
                # Valider le format avant d'accepter
                if self._validate_field(key, llm_value):
                    # Si regex n'a pas de valeur ou diffère, prendre LLM
                    if regex_value is None or regex_value != llm_value:
                        logger.debug("LLM correction %s: %s → %s", key, regex_value, llm_value)
                        result[key] = llm_value
        
        return result
    
    def _validate_field(self, field: str, value: Any) -> bool:
        """Valide le format d'un champ."""
        if value is None:
            return True
        
        try:
            if field == "siret":
                return self._validate_siret(str(value))
            elif field == "siren":
                return len(str(value)) == 9 and str(value).isdigit()
            elif field == "tva_intra":
                return bool(re.match(r"^FR\d{11}$", str(value)))
            elif field == "iban":
                return self._validate_iban(str(value))
            elif field in ("montant_ht", "tva", "montant_ttc"):
                return isinstance(value, (int, float)) and value >= 0
            elif field in ("date_emission", "date_expiration", "date_validite"):
                return bool(re.match(r"^\d{2}/\d{2}/\d{4}$", str(value)))
            elif field == "raison_sociale":
                return isinstance(value, str) and 2 <= len(value) <= 100
            elif field == "bic":
                return bool(re.match(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$", str(value).upper()))
        except Exception:
            return False
        
        return True
    
    def _validate_siret(self, siret: str) -> bool:
        """Validation SIRET avec algorithme de Luhn."""
        siret = re.sub(r"\s", "", siret)
        if len(siret) != 14 or not siret.isdigit():
            return False
        
        # Algorithme de Luhn
        digits = [int(d) for d in siret]
        total = 0
        for i, d in enumerate(digits):
            if i % 2 == 0:
                d *= 2
                if d > 9:
                    d -= 9
            total += d
        return total % 10 == 0
    
    def _validate_iban(self, iban: str) -> bool:
        """Validation IBAN avec checksum ISO 13616."""
        iban = re.sub(r"\s", "", iban).upper()
        if len(iban) < 15 or not iban.startswith("FR"):
            return False
        
        # Réarranger IBAN
        rearranged = iban[4:] + iban[:4]
        
        # Convertir lettres en chiffres
        numeric = ""
        for c in rearranged:
            if c.isdigit():
                numeric += c
            elif c.isalpha():
                numeric += str(ord(c) - 55)
            else:
                return False
        
        return int(numeric) % 97 == 1


# Instance globale
llm_extractor = LLMExtractor()
