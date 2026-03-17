"""
app.py — API Flask du service OCR
Port : 5001
Routes : POST /api/ocr | POST /api/ocr/batch | GET /api/health
"""

import json
import logging
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import magic
import pytesseract
from flask import Flask, jsonify, request

from classifier import DocumentClassifier
from extractor import EntityExtractor
from ocr_engine import OCREngine
from preprocess import ImagePreprocessor

# ------------------------------------------------------------------
# Configuration des logs JSON structurés
# ------------------------------------------------------------------

class JsonFormatter(logging.Formatter):
    """Formatteur de logs en JSON structuré."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "service": "ocr-service",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Enrichissement optionnel depuis extra
        for key in ("document_id", "duration_ms", "ocr_engine"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, ensure_ascii=False)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Initialisation Flask et composants OCR
# ------------------------------------------------------------------

app = Flask(__name__)

preprocessor = ImagePreprocessor()
ocr_engine = OCREngine()
extractor = EntityExtractor()
classifier = DocumentClassifier()

UPLOAD_DIR = Path("/tmp/ocr_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Types MIME acceptés
ALLOWED_MIME = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
}


# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

def _process_document(file_path: str, document_id: str) -> dict:
    """
    Pipeline complet de traitement d'un document (PDF ou image).

    Returns:
        JSON de sortie standardisé.
    """
    start_ms = time.time()

    mime_type = magic.from_file(file_path, mime=True)

    # Obtenir la liste d'images selon le type
    if mime_type == "application/pdf":
        images_raw = preprocessor.pdf_to_images(file_path)
    else:
        import cv2
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Impossible de lire l'image : {file_path}")
        images_raw = [img]

    # Prétraitement et OCR de chaque page
    all_texts = []
    all_confidences = []
    all_engines = []
    all_boxes = []

    for img_raw in images_raw:
        img_preprocessed = preprocessor.preprocess_array(img_raw)
        ocr_result = ocr_engine.extract_text(img_preprocessed)
        all_texts.append(ocr_result["text"])
        all_confidences.append(ocr_result["confidence"])
        all_engines.append(ocr_result["ocr_engine_used"])
        all_boxes.extend(ocr_result.get("boxes", []))

    # Agrégation multi-pages
    raw_text = "\n".join(all_texts)
    ocr_confidence = round(sum(all_confidences) / len(all_confidences), 4)
    # Moteur dominant : celui le plus fréquemment utilisé
    ocr_engine_used = max(set(all_engines), key=all_engines.count)

    # Classification
    classification = classifier.classify(raw_text)

    # Extraction d'entités
    entities_raw = extractor.extract_all(raw_text)
    extraction_confidence = entities_raw.pop("extraction_confidence")

    processing_time_ms = round((time.time() - start_ms) * 1000)

    logger.info(
        "Document traité",
        extra={
            "document_id": document_id,
            "duration_ms": processing_time_ms,
            "ocr_engine": ocr_engine_used,
        },
    )

    return {
        "document_id": document_id,
        "type": classification["type"],
        "type_confidence": classification["confidence"],
        "ocr_engine_used": ocr_engine_used,
        "ocr_confidence": ocr_confidence,
        "raw_text": raw_text,
        "entities": entities_raw,
        "extraction_confidence": extraction_confidence,
        "processing_time_ms": processing_time_ms,
    }


def _save_temp_file(file_storage, document_id: str) -> str:
    """Sauvegarde le fichier uploadé dans /tmp/ et retourne son chemin."""
    ext = Path(file_storage.filename).suffix if file_storage.filename else ""
    dest = UPLOAD_DIR / f"{document_id}{ext}"
    file_storage.save(str(dest))
    return str(dest)


def _cleanup(file_path: str) -> None:
    """Supprime le fichier temporaire."""
    try:
        os.remove(file_path)
    except OSError:
        pass


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    """Vérification de l'état du service et des versions des moteurs."""
    try:
        tess_version = pytesseract.get_tesseract_version()
        tess_version_str = str(tess_version)
    except Exception:
        tess_version_str = "unavailable"

    return jsonify({
        "status": "ok",
        "tesseract_version": tess_version_str,
        "models_loaded": True,
    }), 200


@app.route("/api/ocr", methods=["POST"])
def ocr_single():
    """
    Traite un document (PDF ou image) et retourne le JSON structuré.

    Body : multipart/form-data, champ "document".
    """
    if "document" not in request.files:
        return jsonify({"error": "Champ 'document' manquant"}), 400

    file = request.files["document"]
    if not file or not file.filename:
        return jsonify({"error": "Fichier vide ou sans nom"}), 400

    document_id = str(uuid.uuid4())[:8]
    file_path = None

    try:
        file_path = _save_temp_file(file, document_id)

        # Vérification du type MIME
        mime_type = magic.from_file(file_path, mime=True)
        if mime_type not in ALLOWED_MIME:
            return jsonify({
                "error": f"Type de fichier non supporté : {mime_type}"
            }), 415

        result = _process_document(file_path, document_id)
        return jsonify(result), 200

    except Exception as exc:
        logger.error("Erreur traitement document %s : %s", document_id, str(exc))
        return jsonify({"error": str(exc), "document_id": document_id}), 500

    finally:
        if file_path:
            _cleanup(file_path)


@app.route("/api/ocr/batch", methods=["POST"])
def ocr_batch():
    """
    Traite une liste de document_ids en parallèle (prévu pour le Rôle 6 / MinIO).

    Body JSON : {"document_ids": ["id1", "id2", ...]}

    Note : en l'absence du Rôle 4 (MinIO), retourne une réponse simulée.
    """
    body = request.get_json(silent=True)
    if not body or "document_ids" not in body:
        return jsonify({"error": "Body JSON avec 'document_ids' requis"}), 400

    document_ids = body["document_ids"]
    if not isinstance(document_ids, list) or not document_ids:
        return jsonify({"error": "'document_ids' doit être une liste non vide"}), 400

    results = []
    errors = []

    # Traitement parallèle (max 4 workers)
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_id = {
            executor.submit(_fetch_and_process_from_minio, doc_id): doc_id
            for doc_id in document_ids
        }
        for future in as_completed(future_to_id):
            doc_id = future_to_id[future]
            try:
                results.append(future.result())
            except Exception as exc:
                logger.error("Erreur batch doc %s : %s", doc_id, str(exc))
                errors.append({"document_id": doc_id, "error": str(exc)})

    return jsonify({
        "processed": len(results),
        "errors": len(errors),
        "results": results,
        "error_details": errors,
    }), 200


def _fetch_and_process_from_minio(document_id: str) -> dict:
    """
    Récupère un document depuis MinIO et le traite.
    Si MinIO n'est pas disponible, simule le résultat (mode dev).
    """
    minio_endpoint = os.getenv("MINIO_ENDPOINT")

    if not minio_endpoint:
        # Mode développement : simuler un résultat
        logger.info("Mode dev — simulation MinIO pour document_id=%s", document_id)
        return {
            "document_id": document_id,
            "type": "inconnu",
            "type_confidence": 0.0,
            "ocr_engine_used": "simulated",
            "ocr_confidence": 0.0,
            "raw_text": "",
            "entities": {},
            "extraction_confidence": 0.0,
            "processing_time_ms": 0,
            "note": "MinIO non configuré — mode simulation",
        }

    # Intégration MinIO réelle (Rôle 4)
    raise NotImplementedError(
        "L'intégration MinIO sera activée quand MINIO_ENDPOINT sera configuré."
    )


# ------------------------------------------------------------------
# Middleware : log de chaque requête
# ------------------------------------------------------------------

@app.before_request
def _log_request_start():
    request._start_time = time.time()


@app.after_request
def _log_request_end(response):
    duration_ms = round((time.time() - getattr(request, "_start_time", time.time())) * 1000)
    logger.info(
        "%s %s → %d",
        request.method,
        request.path,
        response.status_code,
        extra={"duration_ms": duration_ms},
    )
    return response


# ------------------------------------------------------------------
# Point d'entrée (dev uniquement — prod via gunicorn)
# ------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)
