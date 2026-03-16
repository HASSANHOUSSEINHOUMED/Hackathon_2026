from datetime import datetime


# Schéma d'un document traité dans le pipeline
DOCUMENT_SCHEMA = {
    "doc_id": str,           # Identifiant unique du document
    "filename": str,          # Nom du fichier original
    "doc_type": str,          # Type : facture, devis, kbis, urssaf, siret, rib
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
    "siret": str,             # 14 chiffres
    "tva": str,               # Format FR + 11 chiffres
    "montant_ht": float,      # Montant hors taxes
    "montant_ttc": float,     # Montant toutes taxes comprises
    "date_emission": str,     # Date au format DD/MM/YYYY
    "date_expiration": str,   # Pour les attestations URSSAF
    "iban": str,              # Format FR + 23 chiffres
    "nom_entreprise": str,    # Extrait par spaCy NER
    "adresse": str,           # Extrait par spaCy NER
    "anomalies": list,        # Liste des incohérences détectées
}