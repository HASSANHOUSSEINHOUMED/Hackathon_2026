"""
Enrichissement léger d'entités avant validation.
Priorité: regex + heuristiques NER-like, sans modèle lourd.
"""
import re
from typing import Any


def _clean(text: str) -> str:
	text = text.replace("\xa0", " ")
	return re.sub(r"\s+", " ", text).strip()


def _to_float(value: str | None) -> float | None:
	if not value:
		return None
	cleaned = value.replace(" ", "").replace(",", ".")
	try:
		return round(float(cleaned), 2)
	except ValueError:
		return None


def _extract_siret(text: str) -> str | None:
	patterns = [
		r"(?:siret|n\s*[o°]\s*siret)\s*[:\-]?\s*(\d[\d\s]{12,16}\d)",
		r"\b(\d{3}\s?\d{3}\s?\d{3}\s?\d{5})\b",
		r"\b(\d{14})\b",
	]
	for p in patterns:
		m = re.search(p, text, re.IGNORECASE)
		if m:
			siret = re.sub(r"\s", "", m.group(1))
			if len(siret) == 14 and siret.isdigit():
				return siret
	return None


def _extract_tva_intra(text: str) -> str | None:
	m = re.search(r"FR\s*(\d{2})\s*(\d{9})", text, re.IGNORECASE)
	if not m:
		return None
	return f"FR{m.group(1)}{m.group(2)}"


def _extract_iban(text: str) -> str | None:
	patterns = [
		r"(?:iban|rib)\s*[:\-]?\s*(FR\s*\d{2}[\s\dA-Z]{18,40})",
		r"\b(FR\d{25,27})\b",
	]
	for p in patterns:
		m = re.search(p, text, re.IGNORECASE)
		if m:
			iban = re.sub(r"\s", "", m.group(1)).upper()
			if 20 <= len(iban) <= 34:
				return iban
	return None


def _extract_amount(label: str, text: str) -> float | None:
	m = re.search(rf"{label}\s*[:\-]?\s*(\d[\d\s]*[\.,]\d{{2}})", text, re.IGNORECASE)
	if not m:
		return None
	return _to_float(m.group(1))


def _extract_date_near(labels: list[str], text: str) -> str | None:
	for label in labels:
		m = re.search(rf"{label}\s*[:\-]?\s*(\d{{2}}[\/\-.]\d{{2}}[\/\-.]\d{{4}})", text, re.IGNORECASE)
		if m:
			return m.group(1).replace("-", "/").replace(".", "/")
	return None


def _extract_raison_sociale(text: str) -> str | None:
	# 1) Regex explicite
	m = re.search(
		r"(?:raison\s*sociale|denomination|soci[eé]t[eé])\s*[:\-]?\s*(.{3,120}?)(?=\bSIRET\b|\bTVA\b|\bIBAN\b|\bDATE\b|$)",
		text,
		re.IGNORECASE,
	)
	if m:
		candidate = m.group(1).strip(" .,:;")
		candidate = re.sub(r"^(facture|attestation(?:\s+de\s+vigilance)?)\s+", "", candidate, flags=re.IGNORECASE)
		if 3 <= len(candidate) <= 80:
			return candidate

	# 2) NER-like heuristique: token se terminant par une forme juridique
	org_pattern = re.compile(
		r"\b([A-Z][A-Z0-9 '&\-]{2,60}\s(?:SASU|SAS|SARL|EURL|SA|SNC|SCI|SOCIETE))\b"
	)
	m = org_pattern.search(text.upper())
	if m:
		candidate = m.group(1).title().strip(" .,:;")
		candidate = re.sub(r"^(Facture|Attestation(?: De Vigilance)?)\s+", "", candidate)
		if 3 <= len(candidate) <= 80:
			return candidate

	return None


def enrich_entities(entities: dict[str, Any] | None, raw_text: str | None, doc_type: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
	"""
	Complète uniquement les champs manquants via extraction regex/NER-like.
	Retourne (entities_enriched, metadata).
	"""
	base = dict(entities or {})
	text = _clean(raw_text or "")
	if not text:
		return base, {"used": False, "filled_fields": []}

	extracted = {
		"siret": _extract_siret(text),
		"tva_intra": _extract_tva_intra(text),
		"iban": _extract_iban(text),
		"montant_ht": _extract_amount(r"(?:total\s*)?h\.?t\.?|hors\s*taxe", text),
		"tva": _extract_amount(r"tva(?:\s*\(\d+(?:[\.,]\d+)?\s*%\))?", text),
		"montant_ttc": _extract_amount(r"(?:total\s*)?t\.?t\.?c\.?|net\s*[àa]\s*payer|montant\s*total", text),
		"date_emission": _extract_date_near([r"date\s*d['eé]mission", r"[eé]mis\s*le", r"date"], text),
		"date_expiration": _extract_date_near([r"date\s*d['eé]xpiration", r"expire\s*le", r"valable\s*jusqu"], text),
		"date_validite": _extract_date_near([r"validit[eé]", r"valable\s*jusqu"], text),
		"raison_sociale": _extract_raison_sociale(text),
	}

	# Contexte doc: sur URSSAF on favorise date_expiration, sur devis date_validite.
	if (doc_type or "").lower() == "urssaf" and not extracted["date_expiration"]:
		extracted["date_expiration"] = extracted["date_validite"]
	if (doc_type or "").lower() == "devis" and not extracted["date_validite"]:
		extracted["date_validite"] = extracted["date_expiration"]

	filled_fields = []
	for key, value in extracted.items():
		current = base.get(key)
		if (current is None or str(current).strip() == "") and value not in (None, ""):
			base[key] = value
			filled_fields.append(key)

	return base, {
		"used": True,
		"filled_fields": filled_fields,
		"filled_count": len(filled_fields),
	}

