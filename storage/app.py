import uuid
from flask import Flask, request, jsonify
from storage_client import (
    upload_raw,
    get_raw,
    upload_clean,
    get_clean,
    upload_curated,
    get_curated,
    track_document,
    get_document_status,
)
from health_check import full_health_check

app = Flask(__name__)


# ── Health check ──────────────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    """Vérifie que MinIO et MongoDB sont opérationnels."""
    return jsonify(full_health_check())


# ── Raw zone ──────────────────────────────────────────────────────────

@app.route("/upload/raw", methods=["POST"])
def upload_raw_file():
    """
    Reçoit un fichier (PDF/image) et le dépose dans la raw-zone.
    Appelé par le frontend après l'upload de l'utilisateur.
    """
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    # Génération d'un identifiant unique pour suivre le document dans le pipeline
    doc_id = str(uuid.uuid4())
    file_bytes = file.read()

    raw_path = upload_raw(file_bytes, file.filename, file.content_type)

    # Enregistrement du document dans MongoDB avec statut initial
    track_document(doc_id, {
        "doc_id": doc_id,
        "filename": file.filename,
        "status": "uploaded",
        "raw_path": raw_path,
    })

    return jsonify({"doc_id": doc_id, "raw_path": raw_path}), 201


# ── Clean zone ────────────────────────────────────────────────────────

@app.route("/upload/clean/<doc_id>", methods=["POST"])
def upload_clean_result(doc_id):
    """
    Reçoit le résultat OCR et le dépose dans la clean-zone.
    Appelé par le service OCR après extraction du texte.
    """
    ocr_data = request.get_json()
    if not ocr_data:
        return jsonify({"error": "No data provided"}), 400

    clean_path = upload_clean(doc_id, ocr_data)
    track_document(doc_id, {"status": "ocr_done", "clean_path": clean_path})

    return jsonify({"doc_id": doc_id, "clean_path": clean_path}), 201


@app.route("/get/clean/<doc_id>", methods=["GET"])
def get_clean_result(doc_id):
    """Retourne le résultat OCR depuis la clean-zone."""
    data = get_clean(doc_id)
    return jsonify(data)


# ── Curated zone ──────────────────────────────────────────────────────

@app.route("/upload/curated/<doc_id>", methods=["POST"])
def upload_curated_result(doc_id):
    """
    Reçoit les données structurées et les dépose dans la curated-zone.
    Appelé par le service d'extraction après regex + NER.
    """
    structured_data = request.get_json()
    if not structured_data:
        return jsonify({"error": "No data provided"}), 400

    curated_path = upload_curated(doc_id, structured_data)
    track_document(doc_id, {"status": "extracted", "curated_path": curated_path})

    return jsonify({"doc_id": doc_id, "curated_path": curated_path}), 201


@app.route("/get/curated/<doc_id>", methods=["GET"])
def get_curated_result(doc_id):
    """Retourne les données structurées depuis la curated-zone."""
    data = get_curated(doc_id)
    return jsonify(data)


# ── Statut document ───────────────────────────────────────────────────

@app.route("/status/<doc_id>", methods=["GET"])
def document_status(doc_id):
    """Retourne le statut complet d'un document dans le pipeline."""
    status = get_document_status(doc_id)
    if not status:
        return jsonify({"error": "Document not found"}), 404
    return jsonify(status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)