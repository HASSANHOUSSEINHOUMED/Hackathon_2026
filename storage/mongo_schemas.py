from datetime import datetime


# Schéma d'un document traité dans le pipeline
DOCUMENT_SCHEMA = {
    "doc_id": str,           # Identifiant unique du document
    "filename": str,          # Nom du fichier original
    "status": str,            # Statut : uploaded, ocr_done, extracted, validated, rejected
    "raw_path": str,          # Chemin dans la raw-zone (MinIO)
    "clean_path": str,        # Chemin dans la clean-zone (MinIO)
    "curated_path": str,      # Chemin dans la curated-zone (MinIO)
    "rejection_reason": str,  # Raison du rejet si status = rejected
    "created_at": datetime,   # Date d'upload
    "updated_at": datetime,   # Dernière mise à jour dans le pipeline
}

# Schéma des données extraites (curated-zone)
EXTRACTED_DATA_SCHEMA = {
    "doc_id": str,
    "doc_type": str,          # Type : facture, devis, kbis, urssaf, siret, rib
    "siret": str,             # 14 chiffres — identifiant unique entreprise
    "tva_intra": str,         # Format FR + 11 chiffres — numéro TVA intracommunautaire
    "montant_ht": float,      # Montant hors taxes
    "montant_tva": float,     # Montant de la TVA
    "montant_ttc": float,     # Montant toutes taxes comprises
    "date_emission": str,     # Date au format DD/MM/YYYY
    "date_expiration": str,   # Pour les attestations URSSAF
    "iban": str,              # Format FR + 23 chiffres
    "bic": str,               # Code banque international (ex: BNPAFRPP)
    "nom_entreprise": str,    # Extrait par spaCy NER
    "adresse": str,           # Extrait par spaCy NER
    "anomalies": list,        # Liste des incohérences détectées par Wael
}