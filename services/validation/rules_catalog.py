"""
Catalogue des règles de validation pour les documents administratifs.
"""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Rule:
    """Définition d'une règle de validation."""
    id: str
    name: str
    description: str
    severity: Literal["ERROR", "WARNING", "INFO"]
    document_types_concerned: list[str] = field(default_factory=list)


RULES: dict[str, Rule] = {
    "SIRET_MISMATCH": Rule(
        id="SIRET_MISMATCH",
        name="Incohérence SIRET inter-documents",
        description="Le SIRET présent sur un document diffère de celui d'un autre document du même fournisseur.",
        severity="ERROR",
        document_types_concerned=["facture", "urssaf", "siret", "kbis", "rib"],
    ),
    "TVA_CALCUL_ERROR": Rule(
        id="TVA_CALCUL_ERROR",
        name="Erreur de calcul TVA",
        description="Le montant de TVA ne correspond pas au taux appliqué sur le montant HT.",
        severity="ERROR",
        document_types_concerned=["facture", "devis"],
    ),
    "TTC_CALCUL_ERROR": Rule(
        id="TTC_CALCUL_ERROR",
        name="Erreur de calcul TTC",
        description="Le montant TTC ne correspond pas à la somme HT + TVA.",
        severity="ERROR",
        document_types_concerned=["facture", "devis"],
    ),
    "ATTESTATION_EXPIREE": Rule(
        id="ATTESTATION_EXPIREE",
        name="Attestation URSSAF expirée",
        description="L'attestation de vigilance URSSAF a dépassé sa date d'expiration.",
        severity="ERROR",
        document_types_concerned=["urssaf"],
    ),
    "KBIS_PERIME": Rule(
        id="KBIS_PERIME",
        name="Kbis périmé (> 90 jours)",
        description="L'extrait Kbis date de plus de 90 jours.",
        severity="WARNING",
        document_types_concerned=["kbis"],
    ),
    "DEVIS_EXPIRE": Rule(
        id="DEVIS_EXPIRE",
        name="Devis expiré",
        description="La date de validité du devis est dépassée.",
        severity="WARNING",
        document_types_concerned=["devis"],
    ),
    "RAISON_SOCIALE_MISMATCH": Rule(
        id="RAISON_SOCIALE_MISMATCH",
        name="Incohérence raison sociale",
        description="La raison sociale diffère entre deux documents du même fournisseur.",
        severity="WARNING",
        document_types_concerned=["facture", "urssaf", "siret", "kbis"],
    ),
    "IBAN_MISMATCH": Rule(
        id="IBAN_MISMATCH",
        name="Incohérence IBAN",
        description="L'IBAN du RIB diffère de l'IBAN présent sur la facture.",
        severity="WARNING",
        document_types_concerned=["facture", "rib"],
    ),
    "MONTANT_ANORMAL": Rule(
        id="MONTANT_ANORMAL",
        name="Montant statistiquement anormal",
        description="Le montant de la facture est statistiquement anormal (détecté par IsolationForest).",
        severity="INFO",
        document_types_concerned=["facture"],
    ),
    "SIRET_FORMAT_INVALIDE": Rule(
        id="SIRET_FORMAT_INVALIDE",
        name="Format SIRET invalide",
        description="Le SIRET extrait ne respecte pas le format à 14 chiffres ou la clé de Luhn.",
        severity="ERROR",
        document_types_concerned=["facture", "devis", "urssaf", "siret", "kbis", "rib"],
    ),
    "IBAN_FORMAT_INVALIDE": Rule(
        id="IBAN_FORMAT_INVALIDE",
        name="Format IBAN invalide",
        description="L'IBAN extrait ne respecte pas le checksum ISO 13616.",
        severity="ERROR",
        document_types_concerned=["facture", "rib"],
    ),
    "TVA_INTRA_INVALIDE": Rule(
        id="TVA_INTRA_INVALIDE",
        name="TVA intracommunautaire invalide",
        description="Le numéro de TVA intracommunautaire ne respecte pas le format FR + clé + SIREN.",
        severity="WARNING",
        document_types_concerned=["facture", "kbis"],
    ),
}
