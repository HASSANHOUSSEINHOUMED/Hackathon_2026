"""
Fusionneur intelligent d'extraction.
Combine regex + LLM avec validation croisée pour une extraction robuste.
"""
import logging
from typing import Any

from extractor_v2 import EntityExtractor, luhn_check, iban_check
from llm_extractor import llm_extractor

logger = logging.getLogger("ocr-service.smart_extractor")


class SmartExtractor:
    """
    Extracteur intelligent multi-couches.
    
    Pipeline :
    1. Post-traitement OCR (correction erreurs)
    2. Extraction regex v2 (patterns robustes)
    3. Renforcement LLM (si disponible)
    4. Validation croisée et fusion
    5. Score de confiance final
    """
    
    def __init__(self):
        self.regex_extractor = EntityExtractor()
        self.llm = llm_extractor
        
        logger.info(
            "SmartExtractor initialisé (LLM: %s)",
            "activé" if self.llm.is_available else "désactivé"
        )
    
    def extract(self, raw_text: str, doc_type: str = "inconnu") -> dict[str, Any]:
        """
        Extrait les entités avec toutes les couches de traitement.
        
        Note: Le post-traitement OCR est supposé déjà fait par l'appelant (app.py)
        
        Args:
            raw_text: Texte OCR (déjà nettoyé par postprocessor)
            doc_type: Type de document détecté
        
        Returns:
            Dictionnaire des entités avec scores de confiance
        """
        # 1. Extraction regex
        regex_entities = self.regex_extractor.extract_all(raw_text)
        regex_confidence = regex_entities.pop("extraction_confidence", 0.0)
        
        logger.info("Regex extraction: confiance=%.2f", regex_confidence)
        
        # 2. Renforcement LLM (si disponible et si confiance regex < 0.8)
        if self.llm.is_available and regex_confidence < 0.8:
            llm_entities = self.llm.extract_and_validate(
                raw_text, doc_type, regex_entities
            )
            
            # 3. Fusion intelligente
            final_entities = self._merge_extractions(regex_entities, llm_entities)
        else:
            final_entities = regex_entities
        
        # 4. Validation finale
        validated = self._final_validation(final_entities, doc_type)
        
        # 6. Calcul du score de confiance final
        confidence = self._compute_confidence(validated, doc_type)
        validated["extraction_confidence"] = confidence
        
        return validated
    
    def _merge_extractions(
        self,
        regex: dict[str, Any],
        llm: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Fusionne les extractions regex et LLM.
        
        Stratégie de priorité :
        1. Si les deux concordent → garder (confiance max)
        2. Si regex valide et LLM null → garder regex
        3. Si regex null et LLM valide → prendre LLM
        4. Si différents → prendre la valeur valide
        """
        result = {}
        
        for key in regex.keys():
            regex_val = regex.get(key)
            llm_val = llm.get(key)
            
            # Les deux concordent
            if regex_val == llm_val:
                result[key] = regex_val
                continue
            
            # Validation des deux valeurs
            regex_valid = self._is_valid(key, regex_val)
            llm_valid = self._is_valid(key, llm_val)
            
            if regex_valid and llm_valid:
                # Les deux valides mais différentes → privilégier regex (plus fiable pour les formats)
                result[key] = regex_val
                if regex_val != llm_val:
                    logger.debug("Conflit %s: regex=%s vs llm=%s → regex", key, regex_val, llm_val)
            elif regex_valid:
                result[key] = regex_val
            elif llm_valid:
                result[key] = llm_val
                logger.debug("LLM complète %s: %s", key, llm_val)
            else:
                result[key] = None
        
        return result
    
    def _is_valid(self, field: str, value: Any) -> bool:
        """Vérifie si une valeur est valide pour un champ donné."""
        if value is None:
            return False
        
        try:
            if field == "siret":
                return len(str(value)) == 14 and str(value).isdigit() and luhn_check(str(value))
            
            elif field == "siren":
                return len(str(value)) == 9 and str(value).isdigit()
            
            elif field == "tva_intra":
                import re
                return bool(re.match(r"^FR\d{11}$", str(value)))
            
            elif field == "iban":
                return iban_check(str(value))
            
            elif field == "bic":
                import re
                return bool(re.match(r"^[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?$", str(value).upper()))
            
            elif field in ("montant_ht", "tva", "montant_ttc"):
                return isinstance(value, (int, float)) and value >= 0
            
            elif field in ("date_emission", "date_expiration", "date_validite"):
                import re
                return bool(re.match(r"^\d{2}/\d{2}/\d{4}$", str(value)))
            
            elif field == "raison_sociale":
                return isinstance(value, str) and 2 <= len(value) <= 100
            
        except Exception:
            return False
        
        return True
    
    def _final_validation(self, entities: dict[str, Any], doc_type: str) -> dict[str, Any]:
        """
        Validation finale contextuelle selon le type de document.
        """
        result = dict(entities)
        
        # Validation croisée SIRET ↔ TVA
        siret = result.get("siret")
        tva = result.get("tva_intra")
        
        if siret and tva:
            # Le SIREN dans la TVA doit correspondre aux 9 premiers chiffres du SIRET
            siren_from_siret = siret[:9]
            siren_from_tva = tva[4:] if tva.startswith("FR") else None
            
            if siren_from_tva and siren_from_siret != siren_from_tva:
                logger.warning(
                    "Incohérence SIRET/TVA: SIREN SIRET=%s vs TVA=%s",
                    siren_from_siret, siren_from_tva
                )
        
        # Validation contextuelle par type
        if doc_type == "facture":
            # Une facture doit avoir au moins un montant
            if all(result.get(m) is None for m in ["montant_ht", "montant_ttc"]):
                logger.warning("Facture sans montant détecté")
        
        elif doc_type == "urssaf":
            # URSSAF doit avoir date d'expiration
            if result.get("date_expiration") is None:
                logger.warning("Attestation URSSAF sans date d'expiration")
        
        elif doc_type == "rib":
            # RIB doit avoir IBAN
            if result.get("iban") is None:
                logger.warning("RIB sans IBAN détecté")
        
        return result
    
    def _compute_confidence(self, entities: dict[str, Any], doc_type: str) -> float:
        """
        Calcule le score de confiance final.
        Pondéré selon l'importance des champs pour chaque type de document.
        """
        # Poids par type de document
        weights = {
            "facture": {
                "siret": 2.0, "raison_sociale": 1.5, "montant_ttc": 2.0,
                "montant_ht": 1.5, "tva": 1.0, "date_emission": 1.0,
                "iban": 1.0, "tva_intra": 0.5,
            },
            "devis": {
                "siret": 2.0, "raison_sociale": 1.5, "montant_ttc": 2.0,
                "date_emission": 1.0, "date_expiration": 1.5,
            },
            "kbis": {
                "siret": 3.0, "raison_sociale": 2.0, "date_emission": 1.0,
            },
            "urssaf": {
                "siret": 3.0, "raison_sociale": 1.5, "date_emission": 1.0,
                "date_expiration": 2.0,
            },
            "siret": {
                "siret": 3.0, "raison_sociale": 2.0,
            },
            "rib": {
                "iban": 3.0, "bic": 2.0, "raison_sociale": 1.0,
            },
        }
        
        doc_weights = weights.get(doc_type, {
            "siret": 1.0, "raison_sociale": 1.0, "montant_ttc": 1.0,
        })
        
        total_weight = sum(doc_weights.values())
        filled_weight = 0.0
        
        for field, weight in doc_weights.items():
            if entities.get(field) is not None:
                filled_weight += weight
        
        confidence = filled_weight / total_weight if total_weight > 0 else 0.0
        
        return round(min(confidence, 1.0), 4)


# Instance globale
smart_extractor = SmartExtractor()
