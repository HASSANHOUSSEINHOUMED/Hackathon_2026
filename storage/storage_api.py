"""
API de monitoring du stockage (MinIO + MongoDB).
Port 5003.
"""
import json
import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","service":"storage-api","level":"%(levelname)s","message":"%(message)s"}',
)

app = Flask(__name__)
STORAGE_API_KEY = os.getenv("STORAGE_API_KEY", "")


@app.before_request
def require_api_key():
    """Protège l'API stockage via clé partagée si configurée."""
    if not STORAGE_API_KEY:
        return None

    provided = (
        request.headers.get("X-API-Key")
        or request.headers.get("x-api-key")
    )
    if provided != STORAGE_API_KEY:
        return jsonify({"error": "unauthorized"}), 401
    return None


def _get_datalake():
    from storage_client import DataLakeClient
    return DataLakeClient()


def _get_db():
    from mongo_client import MetadataDB
    return MetadataDB()


@app.route("/api/storage/stats", methods=["GET"])
def storage_stats():
    """Taille et nombre de fichiers par zone."""
    try:
        dl = _get_datalake()
        stats = dl.get_stats()
        db = _get_db()
        db_stats = db.get_db_stats()
        return jsonify({"minio": stats, "mongodb": db_stats}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/storage/document/<doc_id>", methods=["GET"])
def document_location(doc_id):
    """Localisation d'un document dans les différentes zones."""
    dl = _get_datalake()
    locations = {}
    for zone in dl.ZONES:
        for obj in dl.client.list_objects(zone, recursive=True):
            if doc_id in obj.object_name:
                locations[zone] = obj.object_name
                break
    if not locations:
        return jsonify({"error": "Document non trouvé"}), 404
    return jsonify({"document_id": doc_id, "locations": locations}), 200


@app.route("/api/storage/health", methods=["GET"])
def health():
    """Statut de MinIO et MongoDB."""
    status = {"minio": "unknown", "mongodb": "unknown"}

    try:
        dl = _get_datalake()
        dl.client.list_buckets()
        status["minio"] = "ok"
    except Exception:
        status["minio"] = "error"

    try:
        db = _get_db()
        db.client.admin.command("ping")
        status["mongodb"] = "ok"
    except Exception:
        status["mongodb"] = "error"

    overall = "ok" if all(v == "ok" for v in status.values()) else "degraded"
    return jsonify({"status": overall, "services": status}), 200


@app.route("/api/storage/document/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Supprime un document de toutes les zones (RGPD)."""
    dl = _get_datalake()
    deleted = []
    for zone in dl.ZONES:
        for obj in dl.client.list_objects(zone, recursive=True):
            if doc_id in obj.object_name:
                dl.client.remove_object(zone, obj.object_name)
                deleted.append(f"{zone}/{obj.object_name}")

    # Supprimer aussi de MongoDB
    try:
        db = _get_db()
        db.documents.delete_many({"document_id": doc_id})
    except Exception:
        pass

    if not deleted:
        return jsonify({"error": "Document non trouvé"}), 404
    return jsonify({"status": "deleted", "removed_from": deleted}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
