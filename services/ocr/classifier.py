"""
Classificateur de documents administratifs par mots-clés pondérés.
"""
import logging
import re

logger = logging.getLogger("ocr-service.classifier")

# Dictionnaire de mots-clés pondérés par type de document
KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "facture": [
        ("facture", 3), ("invoice", 3), ("montant ttc", 2),
        ("bon de paiement", 2), ("n° facture", 2), ("net à payer", 2),
        ("total ht", 2), ("total ttc", 2), ("fac-", 2),
        ("règlement", 1), ("échéance", 1),
    ],
    "devis": [
        ("devis", 3), ("quotation", 3), ("offre de prix", 2),
        ("bon pour accord", 2), ("validité", 1), ("dev-", 2),
        ("proposition commerciale", 2),
    ],
    "kbis": [
        ("extrait kbis", 4), ("greffe", 2), ("rcs", 2),
        ("immatriculation", 2), ("tribunal de commerce", 2),
        ("capital social", 1), ("objet social", 1),
    ],
    "urssaf": [
        ("urssaf", 4), ("attestation de vigilance", 4),
        ("cotisations sociales", 2), ("régime général", 1),
        ("sécurité sociale", 1), ("art. l.243", 1),
    ],
    "siret": [
        ("avis de situation", 3), ("répertoire sirene", 3),
        ("insee", 2), ("code ape", 2), ("établissement", 1),
        ("nic", 1), ("avis de situation au répertoire", 4),
    ],
    "rib": [
        ("relevé d'identité bancaire", 4), ("rib", 3),
        ("iban", 2), ("bic", 2), ("domiciliation", 1),
        ("code banque", 2), ("code guichet", 2), ("clé rib", 2),
        ("swift", 1),
    ],
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

        for doc_type, keywords in KEYWORDS.items():
            score = 0
            for keyword, weight in keywords:
                # Chercher le mot-clé (insensible à la casse, tolère les accents manquants)
                pattern = re.escape(keyword)
                matches = re.findall(pattern, text_lower)
                score += len(matches) * weight
            scores[doc_type] = score

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
