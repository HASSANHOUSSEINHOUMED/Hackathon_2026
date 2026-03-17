"""
classifier.py — Classification de documents administratifs
Classe : DocumentClassifier
Approche : mots-clés pondérés
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Dictionnaire de mots-clés pondérés par type de document
KEYWORDS: dict[str, list[tuple[str, int]]] = {
    "facture": [
        ("facture", 3),
        ("invoice", 3),
        ("montant ttc", 2),
        ("net à payer", 2),
        ("n° facture", 2),
        ("numéro de facture", 2),
        ("référence facture", 1),
        ("avoir", 1),
    ],
    "devis": [
        ("devis", 3),
        ("quotation", 3),
        ("offre de prix", 2),
        ("bon pour accord", 2),
        ("validité", 1),
        ("proposition commerciale", 2),
        ("estimation", 1),
    ],
    "kbis": [
        ("extrait kbis", 4),
        ("greffe", 2),
        ("rcs", 2),
        ("immatriculation", 2),
        ("tribunal de commerce", 2),
        ("registre du commerce", 2),
        ("inscription au rcs", 2),
    ],
    "urssaf": [
        ("urssaf", 4),
        ("attestation de vigilance", 4),
        ("cotisations sociales", 2),
        ("protection sociale", 1),
        ("recouvrement", 1),
        ("déclaration sociale", 1),
    ],
    "siret": [
        ("avis de situation", 3),
        ("répertoire sirene", 3),
        ("insee", 2),
        ("code ape", 2),
        ("activité principale", 1),
        ("établissement principal", 1),
    ],
    "rib": [
        ("relevé d'identité bancaire", 4),
        ("rib", 3),
        ("iban", 2),
        ("bic", 2),
        ("domiciliation", 2),
        ("titulaire du compte", 1),
        ("code banque", 1),
    ],
}


class DocumentClassifier:
    """Classifie un document administratif par analyse de mots-clés pondérés."""

    def classify(self, text: str) -> dict:
        """
        Détermine le type de document à partir du texte OCR.

        Stratégie : somme des poids des mots-clés trouvés (texte normalisé en minuscules).
        Si aucun mot-clé n'est trouvé → type = "inconnu".

        Args:
            text: Texte brut issu de l'OCR.

        Returns:
            {
                "type": str,          # type de document détecté
                "confidence": float,  # score normalisé entre 0 et 1
                "scores": dict        # scores bruts par type
            }
        """
        # Normalisation : minuscules + suppression des accents redondants conservés
        normalized = self._normalize(text)

        scores: dict[str, int] = {}

        for doc_type, keywords in KEYWORDS.items():
            total = 0
            for keyword, weight in keywords:
                # Recherche du mot-clé comme séquence (pas forcément mot entier
                # pour gérer les abréviations : "ttc", "rib", etc.)
                if keyword in normalized:
                    total += weight
            scores[doc_type] = total

        max_score = max(scores.values())

        if max_score == 0:
            logger.info("Classification : type inconnu (aucun mot-clé trouvé)")
            return {
                "type": "inconnu",
                "confidence": 0.0,
                "scores": scores,
            }

        # Type retenu = celui avec le score le plus élevé
        detected_type = max(scores, key=lambda k: scores[k])

        # Normalisation de la confiance : score max relatif à la somme totale
        total_all_scores = sum(scores.values())
        confidence = round(max_score / total_all_scores, 4) if total_all_scores > 0 else 0.0

        logger.info(
            "Classification : type=%s, confiance=%.3f, score=%d",
            detected_type, confidence, max_score
        )

        return {
            "type": detected_type,
            "confidence": confidence,
            "scores": scores,
        }

    @staticmethod
    def _normalize(text: str) -> str:
        """
        Normalise le texte pour la comparaison :
        - minuscules
        - espaces insécables → espaces normaux
        - apostrophes typographiques → apostrophes simples
        - suppression des caractères de contrôle
        """
        text = text.lower()
        text = text.replace("\xa0", " ").replace("\u202f", " ")
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = re.sub(r"[^\w\sàâäéèêëîïôùûüç'°€.,/-]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
