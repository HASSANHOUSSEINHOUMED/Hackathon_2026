import os
import io
import json
import logging
from datetime import datetime
from typing import Any

from minio import Minio          # Client pour interagir avec MinIO (Data Lake)
from pymongo import MongoClient  # Client pour interagir avec MongoDB (métadonnées)
from dotenv import load_dotenv   # Charge les variables depuis le fichier .env

# Chargement des variables d'environnement
load_dotenv()

# Logs en JSON structuré pour faciliter le monitoring et le débogage
logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Noms des 3 zones du Data Lake ─────────────────────────────────────
# Récupérés depuis .env avec des valeurs par défaut si non définis
BUCKET_RAW     = os.getenv("BUCKET_RAW", "raw-zone")
BUCKET_CLEAN   = os.getenv("BUCKET_CLEAN", "clean-zone")
BUCKET_CURATED = os.getenv("BUCKET_CURATED", "curated-zone")

# Dictionnaire utilisé par init_buckets.py pour créer les zones
BUCKETS = {
    BUCKET_RAW:     "Original uploaded documents",
    BUCKET_CLEAN:   "Extracted OCR text (JSON)",
    BUCKET_CURATED: "Final structured data (JSON)",
}


def get_minio_client() -> Minio:
    """Crée et retourne une connexion MinIO depuis les variables d'environnement."""
    return Minio(
        endpoint=os.getenv("MINIO_ENDPOINT", "localhost:9000"),
        access_key=os.getenv("MINIO_ROOT_USER", "admin"),
        secret_key=os.getenv("MINIO_ROOT_PASSWORD", "changeme_minio"),
        # HTTPS activé uniquement en production (false en développement local)
        secure=os.getenv("MINIO_SECURE", "false").lower() == "true",
    )


def get_mongo_collection(collection_name: str):
    """Retourne une collection MongoDB prête à l'emploi."""
    client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    db = client[os.getenv("MONGO_DB", "hackathon2026")]
    return db[collection_name]


# ── Raw zone ──────────────────────────────────────────────────────────

def upload_raw(file_bytes: bytes, filename: str, content_type: str) -> str:
    """
    Dépose le document brut original dans la raw-zone.
    Le chemin inclut la date pour organiser les fichiers par jour.
    """
    client = get_minio_client()
    # Organisation des fichiers par date : 2026/03/16/facture.pdf
    object_name = f"{datetime.utcnow().strftime('%Y/%m/%d')}/{filename}"
    client.put_object(
        bucket_name=BUCKET_RAW,
        object_name=object_name,
        data=io.BytesIO(file_bytes),  # Conversion bytes → flux lisible par MinIO
        length=len(file_bytes),
        content_type=content_type,
    )
    logger.info(f"raw-zone : file uploaded → {object_name}")
    return object_name


def get_raw(object_name: str) -> bytes:
    """Récupère un document brut depuis la raw-zone."""
    client = get_minio_client()
    response = client.get_object(BUCKET_RAW, object_name)
    return response.read()


# ── Clean zone ────────────────────────────────────────────────────────

def upload_clean(doc_id: str, ocr_data: dict[str, Any]) -> str:
    """
    Dépose le résultat OCR (texte extrait) dans la clean-zone au format JSON.
    Appelé par le service OCR après extraction du texte.
    """
    client = get_minio_client()
    object_name = f"{doc_id}/ocr_result.json"
    # Sérialisation du dict Python en JSON encodé en UTF-8
    payload = json.dumps(ocr_data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(
        bucket_name=BUCKET_CLEAN,
        object_name=object_name,
        data=io.BytesIO(payload),
        length=len(payload),
        content_type="application/json",
    )
    logger.info(f"clean-zone : OCR result uploaded → {object_name}")
    return object_name


def get_clean(doc_id: str) -> dict[str, Any]:
    """Récupère le résultat OCR depuis la clean-zone."""
    client = get_minio_client()
    response = client.get_object(BUCKET_CLEAN, f"{doc_id}/ocr_result.json")
    return json.loads(response.read())


# ── Curated zone ──────────────────────────────────────────────────────

def upload_curated(doc_id: str, structured_data: dict[str, Any]) -> str:
    """
    Dépose les données structurées finales dans la curated-zone.
    Appelé après extraction regex + NER par le service d'extraction.
    """
    client = get_minio_client()
    object_name = f"{doc_id}/structured.json"
    payload = json.dumps(structured_data, ensure_ascii=False, indent=2).encode("utf-8")
    client.put_object(
        bucket_name=BUCKET_CURATED,
        object_name=object_name,
        data=io.BytesIO(payload),
        length=len(payload),
        content_type="application/json",
    )
    logger.info(f"curated-zone : structured data uploaded → {object_name}")
    return object_name


def get_curated(doc_id: str) -> dict[str, Any]:
    """Récupère les données structurées depuis la curated-zone."""
    client = get_minio_client()
    response = client.get_object(BUCKET_CURATED, f"{doc_id}/structured.json")
    return json.loads(response.read())


# ── MongoDB : suivi du pipeline ───────────────────────────────────────

def track_document(doc_id: str, metadata: dict[str, Any]) -> None:
    """
    Enregistre ou met à jour le statut d'un document dans MongoDB.
    Utilisé par tous les services pour suivre l'avancement dans le pipeline.
    upsert=True : crée le document s'il n'existe pas, le met à jour sinon.
    """
    col = get_mongo_collection("documents")
    col.update_one(
        {"doc_id": doc_id},
        {"$set": {**metadata, "updated_at": datetime.utcnow()}},
        upsert=True,
    )
    logger.info(f"MongoDB : document tracked → {doc_id}")


def get_document_status(doc_id: str) -> dict[str, Any] | None:
    """
    Retourne le statut complet d'un document depuis MongoDB.
    Retourne None si le document n'existe pas.
    """
    col = get_mongo_collection("documents")
    # _id: 0 exclut l'identifiant interne MongoDB de la réponse
    return col.find_one({"doc_id": doc_id}, {"_id": 0})