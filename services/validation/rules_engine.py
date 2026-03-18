"""
Moteur de règles déterministes pour la validation de documents.
"""
import logging
import re
from datetime import date, datetime
from typing import Any

from unidecode import unidecode

from rules_catalog import RULES

logger = logging.getLogger("validation.rules")

# Taux de TVA légaux en France
VALID_TVA_RATES = [0.055, 0.10, 0.20]
TVA_TOLERANCE = 0.02  # Tolérance en euros pour les arrondis


def _parse_date(date_str: str | None) -> date | None:
    """Convertit une chaîne de date en objet date."""
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None


def _luhn_check(number: str) -> bool:
    """Vérifie la clé de Luhn."""
    digits = [int(d) for d in number if d.isdigit()]
    if not digits:
        return False
    odd = digits[-1::-2]
    even = digits[-2::-2]
    total = sum(odd) + sum(sum(divmod(d * 2, 10)) for d in even)
    return total % 10 == 0


def _normalize_raison_sociale(rs: str) -> str:
    """Normalise une raison sociale pour comparaison."""
    rs = unidecode(rs.lower().strip())
    # Supprimer les formes juridiques
    for suffix in ["sarl", "sas", "sa", "eurl", "snc", "srl", "sci"]:
        rs = re.sub(rf"\b{suffix}\b", "", rs)
    rs = re.sub(r"\s+", " ", rs).strip()
    return rs


def _levenshtein_ratio(s1: str, s2: str) -> float:
    """Distance de Levenshtein normalisée (0 = identique, 1 = totalement différent)."""
    if not s1 and not s2:
        return 0.0
    if not s1 or not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    # Implémentation basique
    matrix = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]
    for i in range(len(s1) + 1):
        matrix[i][0] = i
    for j in range(len(s2) + 1):
        matrix[0][j] = j
    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,
                matrix[i][j-1] + 1,
                matrix[i-1][j-1] + cost,
            )
    return matrix[len(s1)][len(s2)] / max_len


class RulesEngine:
    """Applique les règles de validation sur un ensemble de documents."""

    def validate_batch(self, documents: list[dict]) -> list[dict]:
        """
        Valide un lot de documents et retourne toutes les anomalies détectées.

        Args:
            documents: liste de dicts avec {document_id, type, entities}

        Returns:
            Liste des anomalies détectées
        """
        anomalies = []
        anomalies.extend(self._check_siret_consistency(documents))
        anomalies.extend(self._check_tva_calcul(documents))
        anomalies.extend(self._check_ttc_calcul(documents))
        anomalies.extend(self._check_expiration_dates(documents))
        anomalies.extend(self._check_raison_sociale(documents))
        anomalies.extend(self._check_iban_consistency(documents))
        anomalies.extend(self._check_format_validity(documents))

        logger.info("Validation : %d anomalies détectées sur %d documents", len(anomalies), len(documents))
        return anomalies

    def _check_siret_consistency(self, documents: list[dict]) -> list[dict]:
        """Vérifie la cohérence des SIRET entre documents."""
        anomalies = []
        siret_map: dict[str, list[str]] = {}  # siret → [document_ids]

        for doc in documents:
            siret = doc.get("entities", {}).get("siret")
            if siret:
                cleaned = re.sub(r"\s", "", siret)
                siret_map.setdefault(cleaned, []).append(doc.get("document_id", "?"))

        if len(siret_map) > 1:
            pairs = list(siret_map.items())
            for i in range(len(pairs)):
                for j in range(i + 1, len(pairs)):
                    s1, docs1 = pairs[i]
                    s2, docs2 = pairs[j]
                    anomalies.append({
                        "rule_id": "SIRET_MISMATCH",
                        "severity": RULES["SIRET_MISMATCH"].severity,
                        "message": f"SIRET {s1} ({', '.join(docs1)}) ≠ {s2} ({', '.join(docs2)})",
                        "concerned_document_ids": docs1 + docs2,
                        "evidence": {"siret_1": s1, "siret_2": s2},
                    })

        return anomalies

    def _check_tva_calcul(self, documents: list[dict]) -> list[dict]:
        """Vérifie le calcul de la TVA sur les factures et devis."""
        anomalies = []
        for doc in documents:
            if doc.get("type") not in ("facture", "devis"):
                continue
            entities = doc.get("entities", {})
            ht = entities.get("montant_ht")
            tva = entities.get("tva")
            if ht is None or tva is None:
                continue

            ht = float(ht)
            tva = float(tva)
            if ht == 0:
                continue

            ratio = tva / ht
            # Vérifier si le ratio correspond à un taux légal
            valid = any(abs(ratio - rate) < 0.02 for rate in VALID_TVA_RATES)
            if not valid:
                anomalies.append({
                    "rule_id": "TVA_CALCUL_ERROR",
                    "severity": RULES["TVA_CALCUL_ERROR"].severity,
                    "message": f"Taux TVA détecté ({ratio:.2%}) ne correspond à aucun taux légal (5.5%, 10%, 20%)",
                    "concerned_document_ids": [doc.get("document_id", "?")],
                    "evidence": {"montant_ht": ht, "tva": tva, "ratio": round(ratio, 4)},
                })

        return anomalies

    def _check_ttc_calcul(self, documents: list[dict]) -> list[dict]:
        """Vérifie que TTC = HT + TVA."""
        anomalies = []
        for doc in documents:
            if doc.get("type") not in ("facture", "devis"):
                continue
            entities = doc.get("entities", {})
            ht = entities.get("montant_ht")
            tva = entities.get("tva")
            ttc = entities.get("montant_ttc")
            if ht is None or tva is None or ttc is None:
                continue

            expected_ttc = float(ht) + float(tva)
            if abs(float(ttc) - expected_ttc) > TVA_TOLERANCE:
                anomalies.append({
                    "rule_id": "TTC_CALCUL_ERROR",
                    "severity": RULES["TTC_CALCUL_ERROR"].severity,
                    "message": f"TTC ({ttc}) ≠ HT ({ht}) + TVA ({tva}) = {expected_ttc:.2f}",
                    "concerned_document_ids": [doc.get("document_id", "?")],
                    "evidence": {"montant_ht": ht, "tva": tva, "montant_ttc": ttc, "expected_ttc": expected_ttc},
                })

        return anomalies

    def _check_expiration_dates(self, documents: list[dict]) -> list[dict]:
        """Vérifie les dates d'expiration des attestations, devis et Kbis."""
        anomalies = []
        today = date.today()

        for doc in documents:
            doc_type = doc.get("type", "")
            entities = doc.get("entities", {})
            doc_id = doc.get("document_id", "?")

            if doc_type == "urssaf":
                exp = _parse_date(entities.get("date_expiration"))
                if exp and exp < today:
                    delta = (today - exp).days
                    anomalies.append({
                        "rule_id": "ATTESTATION_EXPIREE",
                        "severity": "ERROR",
                        "message": f"Attestation URSSAF expirée depuis {delta} jours (expiration : {exp.strftime('%d/%m/%Y')})",
                        "concerned_document_ids": [doc_id],
                        "evidence": {"date_expiration": str(exp), "jours_depasses": delta},
                    })
                elif exp and (exp - today).days < 30:
                    delta = (exp - today).days
                    anomalies.append({
                        "rule_id": "ATTESTATION_EXPIREE",
                        "severity": "WARNING",
                        "message": f"Attestation URSSAF expire dans {delta} jours ({exp.strftime('%d/%m/%Y')})",
                        "concerned_document_ids": [doc_id],
                        "evidence": {"date_expiration": str(exp), "jours_restants": delta},
                    })

            elif doc_type == "devis":
                val = _parse_date(entities.get("date_validite"))
                if val and val < today:
                    delta = (today - val).days
                    anomalies.append({
                        "rule_id": "DEVIS_EXPIRE",
                        "severity": "WARNING",
                        "message": f"Devis expiré depuis {delta} jours (validité : {val.strftime('%d/%m/%Y')})",
                        "concerned_document_ids": [doc_id],
                        "evidence": {"date_validite": str(val)},
                    })

            elif doc_type == "kbis":
                emission = _parse_date(entities.get("date_emission") or entities.get("date_kbis"))
                if emission and (today - emission).days > 90:
                    delta = (today - emission).days
                    anomalies.append({
                        "rule_id": "KBIS_PERIME",
                        "severity": "WARNING",
                        "message": f"Kbis daté de {delta} jours (> 90 jours)",
                        "concerned_document_ids": [doc_id],
                        "evidence": {"date_emission": str(emission), "jours": delta},
                    })

        return anomalies

    def _check_raison_sociale(self, documents: list[dict]) -> list[dict]:
        """Vérifie la cohérence des raisons sociales entre documents."""
        anomalies = []
        rs_map: dict[str, list[tuple[str, str]]] = {}  # normalized → [(doc_id, original)]

        for doc in documents:
            rs = doc.get("entities", {}).get("raison_sociale")
            if not rs:
                continue
            normalized = _normalize_raison_sociale(rs)
            rs_map.setdefault(normalized, []).append((doc.get("document_id", "?"), rs))

        # Comparer les raisons sociales normalisées entre elles
        keys = list(rs_map.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ratio = _levenshtein_ratio(keys[i], keys[j])
                if ratio > 0.3:
                    docs_i = rs_map[keys[i]]
                    docs_j = rs_map[keys[j]]
                    anomalies.append({
                        "rule_id": "RAISON_SOCIALE_MISMATCH",
                        "severity": "WARNING",
                        "message": f"Raison sociale diffère : '{docs_i[0][1]}' vs '{docs_j[0][1]}'",
                        "concerned_document_ids": [d[0] for d in docs_i + docs_j],
                        "evidence": {"rs_1": docs_i[0][1], "rs_2": docs_j[0][1], "distance": round(ratio, 3)},
                    })

        return anomalies

    def _check_iban_consistency(self, documents: list[dict]) -> list[dict]:
        """Compare l'IBAN entre RIB et factures."""
        anomalies = []
        ribs = [d for d in documents if d.get("type") == "rib"]
        factures = [d for d in documents if d.get("type") == "facture"]

        for rib in ribs:
            rib_iban = rib.get("entities", {}).get("iban", "")
            if not rib_iban:
                continue
            rib_iban_clean = re.sub(r"\s", "", rib_iban).upper()

            for facture in factures:
                fac_iban = facture.get("entities", {}).get("iban", "")
                if not fac_iban:
                    continue
                fac_iban_clean = re.sub(r"\s", "", fac_iban).upper()

                if rib_iban_clean != fac_iban_clean:
                    anomalies.append({
                        "rule_id": "IBAN_MISMATCH",
                        "severity": "WARNING",
                        "message": f"IBAN RIB ({rib_iban_clean[:10]}...) ≠ IBAN facture ({fac_iban_clean[:10]}...)",
                        "concerned_document_ids": [rib.get("document_id", "?"), facture.get("document_id", "?")],
                        "evidence": {"iban_rib": rib_iban_clean, "iban_facture": fac_iban_clean},
                    })

        return anomalies

    def _check_format_validity(self, documents: list[dict]) -> list[dict]:
        """Vérifie la validité des formats SIRET, IBAN, TVA intra."""
        anomalies = []

        for doc in documents:
            entities = doc.get("entities", {})
            doc_id = doc.get("document_id", "?")

            # SIRET
            siret = entities.get("siret")
            if siret:
                cleaned = re.sub(r"\s", "", siret)
                if len(cleaned) != 14 or not cleaned.isdigit() or not _luhn_check(cleaned):
                    anomalies.append({
                        "rule_id": "SIRET_FORMAT_INVALIDE",
                        "severity": "ERROR",
                        "message": f"SIRET invalide : {siret}",
                        "concerned_document_ids": [doc_id],
                        "evidence": {"siret": siret},
                    })

            # IBAN
            iban = entities.get("iban")
            if iban:
                iban_clean = re.sub(r"\s", "", iban).upper()
                if iban_clean.startswith("FR") and len(iban_clean) >= 27:
                    # Vérification ISO 13616
                    rearranged = iban_clean[4:] + iban_clean[:4]
                    numeric = ""
                    for c in rearranged:
                        if c.isdigit():
                            numeric += c
                        elif c.isalpha():
                            numeric += str(ord(c) - 55)
                    try:
                        if int(numeric) % 97 != 1:
                            anomalies.append({
                                "rule_id": "IBAN_FORMAT_INVALIDE",
                                "severity": "ERROR",
                                "message": f"IBAN checksum invalide : {iban_clean[:10]}...",
                                "concerned_document_ids": [doc_id],
                                "evidence": {"iban": iban_clean},
                            })
                    except ValueError:
                        pass

            # TVA intra
            tva_intra = entities.get("tva_intra")
            if tva_intra:
                cleaned = re.sub(r"\s", "", tva_intra).upper()
                if not re.match(r"^FR\d{11}$", cleaned):
                    anomalies.append({
                        "rule_id": "TVA_INTRA_INVALIDE",
                        "severity": "WARNING",
                        "message": f"TVA intra format invalide : {tva_intra}",
                        "concerned_document_ids": [doc_id],
                        "evidence": {"tva_intra": tva_intra},
                    })

        return anomalies
