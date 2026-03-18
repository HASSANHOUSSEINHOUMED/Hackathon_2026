"""
Service OCR Flask — Point d'entrée principal.
Routes : /api/ocr, /api/ocr/batch, /api/health
"""
import hashlib
import json
import logging
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from flask import Flask, jsonify, request

from classifier import DocumentClassifier
from extractor import EntityExtractor
from ocr_engine import OCREngine
from preprocess import ImagePreprocessor

# ── Configuration du logger JSON ──
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","service":"ocr-service","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger("ocr-service")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB max

# ── Initialisation des composants ──
preprocessor = ImagePreprocessor()
ocr_engine = OCREngine()
extractor = EntityExtractor()
classifier = DocumentClassifier()

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _process_document(file_path: str) -> dict:
    """
    Traite un document unique (PDF ou image) :
    1. Prétraitement
    2. OCR
    3. Classification
    4. Extraction d'entités
    """
    start = time.time()

    # Hash du fichier comme identifiant
    with open(file_path, "rb") as f:
        file_hash = hashlib.md5(f.read()).hexdigest()

    ext = Path(file_path).suffix.lower()

    # Convertir en images
    if ext == ".pdf":
        images = preprocessor.pdf_to_images(file_path)
    else:
        import cv2
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Impossible de charger l'image : {file_path}")
        images = [img]

    # Traiter chaque page
    all_text = []
    total_confidence = 0.0
    engine_used = "tesseract"

    for img in images:
        preprocessed = preprocessor.preprocess_from_array(img)
        ocr_result = ocr_engine.extract_text(preprocessed)
        all_text.append(ocr_result["text"])
        total_confidence += ocr_result["confidence"]
        engine_used = ocr_result["engine"]

    full_text = "\n".join(all_text)
    avg_confidence = total_confidence / len(images) if images else 0.0

    # Classification
    classification = classifier.classify(full_text)

    # Extraction d'entités
    entities = extractor.extract_all(full_text)
    extraction_confidence = entities.pop("extraction_confidence", 0.0)

    processing_time = int((time.time() - start) * 1000)

    result = {
        "document_id": file_hash,
        "type": classification["type"],
        "type_confidence": classification["confidence"],
        "ocr_engine_used": engine_used,
        "ocr_confidence": round(avg_confidence, 4),
        "raw_text": full_text,
        "entities": entities,
        "extraction_confidence": extraction_confidence,
        "processing_time_ms": processing_time,
    }

    logger.info(
        "Document traité : id=%s type=%s ocr_conf=%.2f extr_conf=%.2f durée=%dms",
        file_hash, classification["type"], avg_confidence,
        extraction_confidence, processing_time,
    )

    return result


@app.route("/api/ocr", methods=["POST"])
def ocr_single():
    """Traite un document unique (PDF ou image) via upload multipart."""
    if "document" not in request.files:
        return jsonify({"error": "Champ 'document' requis"}), 400

    file = request.files["document"]
    if not file.filename or not _allowed_file(file.filename):
        return jsonify({"error": "Type de fichier non supporté (PDF, PNG, JPG)"}), 400

    # Sauvegarder le fichier temporairement
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = _process_document(tmp_path)
        return jsonify(result), 200
    except Exception as e:
        logger.error("Erreur OCR : %s", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        os.unlink(tmp_path)


@app.route("/api/ocr/batch", methods=["POST"])
def ocr_batch():
    """Traite plusieurs documents en parallèle."""
    data = request.get_json()
    if not data or "file_paths" not in data:
        return jsonify({"error": "Champ 'file_paths' requis (liste de chemins)"}), 400

    file_paths = data["file_paths"]
    max_workers = min(4, len(file_paths))
    results = []
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(_process_document, path): path
            for path in file_paths
            if os.path.exists(path)
        }
        for future in as_completed(future_to_path):
            path = future_to_path[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                errors.append({"file": path, "error": str(e)})
                logger.error("Erreur batch OCR %s : %s", path, str(e))

    return jsonify({
        "results": results,
        "errors": errors,
        "total": len(file_paths),
        "success": len(results),
        "failed": len(errors),
    }), 200


@app.route("/api/health", methods=["GET"])
def health():
    """Vérifie le statut du service OCR."""
    try:
        import pytesseract
        tess_version = pytesseract.get_tesseract_version().vstring
    except Exception:
        tess_version = "non disponible"

    return jsonify({
        "status": "ok",
        "service": "ocr-service",
        "tesseract_version": tess_version,
        "models_loaded": True,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
