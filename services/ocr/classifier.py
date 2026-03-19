"""
Classificateur de documents administratifs par mots-clés pondérés.
"""
import logging
import re

logger = logging.getLogger("ocr-service.classifier")

# Dictionnaire de mots-clés pondérés par type de document
KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "facture": [
        ("facture", 5), ("invoice", 5), ("montant ttc", 3),
        ("bon de paiement", 3), ("n° facture", 4), ("net à payer", 3),
        ("total ht", 3), ("total ttc", 3), ("fac-", 3),
        ("règlement", 1), ("échéance", 2), ("date facture", 4),
        ("numéro de facture", 4), ("facture n°", 4),
        # IBAN/BIC présents sur factures pour paiement (faible poids)
        ("iban", 1), ("bic", 1),
    ],
    "devis": [
        ("devis", 5), ("quotation", 5), ("offre de prix", 3),
        ("bon pour accord", 3), ("validité", 2), ("dev-", 3),
        ("proposition commerciale", 3), ("devis n°", 4),
    ],
    "kbis": [
        ("extrait kbis", 5), ("extrait k-bis", 5), ("k-bis", 4), ("kbis", 4),
        ("greffe", 3), ("rcs", 3), ("immatriculation", 3), 
        ("tribunal de commerce", 3), ("capital social", 2), ("objet social", 2),
        ("personne morale", 2), ("forme juridique", 2),
    ],
    "urssaf": [
        ("urssaf", 5), ("attestation de vigilance", 5),
        ("cotisations sociales", 3), ("régime général", 2),
        ("sécurité sociale", 2), ("art. l.243", 2),
    ],
    "siret": [
        ("avis de situation", 4), ("répertoire sirene", 4),
        ("insee", 3), ("code ape", 3), ("établissement", 1),
        ("nic", 2), ("avis de situation au répertoire", 5),
    ],
    "rib": [
        ("relevé d'identité bancaire", 6), ("identité bancaire", 5),
        # RIB nécessite ces mots-clés spécifiques, pas juste IBAN/BIC
        ("rib", 4), ("domiciliation", 3),
        ("code banque", 3), ("code guichet", 3), ("clé rib", 3),
        ("titulaire du compte", 4), ("coordonnées bancaires", 4),
        # IBAN/BIC seuls ne suffisent pas (présents aussi sur factures)
        ("iban", 1), ("bic", 1), ("swift", 1),
    ],
}

# Mots-clés exclusifs : si présent, exclure certains types
EXCLUSIVE_KEYWORDS: dict[str, list[str]] = {
    "facture": ["rib"],      # Si "facture" trouvé, ne pas classifier comme RIB
    "devis": ["rib"],        # Si "devis" trouvé, ne pas classifier comme RIB
    "kbis": ["rib", "siret"],
    "urssaf": ["rib"],
}


class DocumentClassifier:
    """Classifie un document à partir de son texte OCR via mots-clés pondérés."""

    def classify(self, text: str) -> dict:
        """
        Classifie le document en analysant les mots-clés pondérés.

        Args:
            text: texte extrait par OCR

        Returns:
            {
                "type": str,
                "confidence": float (0.0 à 1.0),
                "scores": dict (score brut par type)
            }
        """
        text_lower = text.lower()
        scores: dict[str, int] = {}
        types_to_exclude: set[str] = set()

        # Phase 1: Calculer les scores et détecter les exclusions
        for doc_type, keywords in KEYWORDS.items():
            score = 0
            for keyword, weight in keywords:
                # Chercher le mot-clé (insensible à la casse, tolère les accents manquants)
                pattern = re.escape(keyword)
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += len(matches) * weight
                    # Vérifier si ce type exclut d'autres types
                    if doc_type in EXCLUSIVE_KEYWORDS:
                        types_to_exclude.update(EXCLUSIVE_KEYWORDS[doc_type])
            scores[doc_type] = score

        # Phase 2: Appliquer les exclusions (mettre le score à 0)
        for excluded_type in types_to_exclude:
            if excluded_type in scores:
                logger.debug("Type '%s' exclu car mot-clé exclusif détecté", excluded_type)
                scores[excluded_type] = 0

        # Trouver le type avec le score maximum
        total_score = sum(scores.values())
        if total_score == 0:
            logger.warning("Aucun mot-clé détecté — classification impossible")
            return {
                "type": "inconnu",
                "confidence": 0.0,
                "scores": scores,
            }

        best_type = max(scores, key=scores.get)  # type: ignore[arg-type]
        confidence = scores[best_type] / total_score if total_score > 0 else 0.0

        logger.info(
            "Classification : type=%s, confiance=%.2f, scores=%s",
            best_type, confidence, scores,
        )

        return {
            "type": best_type,
            "confidence": round(confidence, 4),
            "scores": scores,
        }
