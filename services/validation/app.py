"""
Service Flask de validation — Point d'entrée principal.
Routes : /api/validate, /api/rules, /api/health
"""
import logging
import time
import uuid

from flask import Flask, jsonify, request

from entity_enricher import enrich_entities
from rules_catalog import RULES
from rules_engine import RulesEngine
from statistical_detector import StatDetector

logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp":"%(asctime)s","service":"validation-service","level":"%(levelname)s","message":"%(message)s"}',
)
logger = logging.getLogger("validation-service")

app = Flask(__name__)

# Initialisation
rules_engine = RulesEngine()
stat_detector = StatDetector()
stat_detector.load_or_train()


@app.route("/api/validate", methods=["POST"])
def validate():
    """
    Valide un ensemble de documents et retourne les anomalies.

    Body JSON :
        {
            "documents": [{"document_id": "...", "type": "facture", "entities": {...}}],
            "supplier_id": "optional"
        }
    """
    data = request.get_json()
    if not data or "documents" not in data:
        return jsonify({"error": "Champ 'documents' requis"}), 400

    documents = data["documents"]
    start = time.time()

    # 0. Enrichissement prioritaire regex/NER léger (avant tout modèle IA)
    enriched_docs = []
    enrichment_notes = []
    for doc in documents:
        entities = doc.get("entities", {})
        raw_text = doc.get("raw_text", "")
        enriched_entities, meta = enrich_entities(entities, raw_text, doc.get("type"))
        enriched_doc = {**doc, "entities": enriched_entities}
        enriched_docs.append(enriched_doc)
        if meta.get("filled_count", 0) > 0:
            enrichment_notes.append({
                "document_id": doc.get("document_id", "?"),
                "filled_fields": meta.get("filled_fields", []),
            })

    # 1. Règles déterministes
    anomalies = rules_engine.validate_batch(enriched_docs)

    # 2. Mini-modèle de détection d'anomalies (léger, sans entraînement)
    anomalies.extend(stat_detector.detect_lightweight_batch(enriched_docs))

    # 3. Détection statistique entraînée (optionnelle)
    for doc in enriched_docs:
        if doc.get("type") == "facture" and stat_detector.trained:
            result = stat_detector.predict(doc)
            if result["is_anomaly"]:
                anomalies.append({
                    "rule_id": "MONTANT_ANORMAL",
                    "severity": RULES["MONTANT_ANORMAL"].severity,
                    "message": result["explanation"],
                    "concerned_document_ids": [doc.get("document_id", "?")],
                    "evidence": {"anomaly_score": result["anomaly_score"]},
                })

    # 3. Calculer le statut global
    severities = [a["severity"] for a in anomalies]
    if "ERROR" in severities:
        status = "ERROR"
    elif "WARNING" in severities:
        status = "WARNING"
    else:
        status = "OK"

    anomaly_count = {
        "ERROR": severities.count("ERROR"),
        "WARNING": severities.count("WARNING"),
        "INFO": severities.count("INFO"),
    }

    duration_ms = int((time.time() - start) * 1000)

    response = {
        "validation_id": str(uuid.uuid4()),
        "status": status,
        "anomaly_count": anomaly_count,
        "anomalies": anomalies,
        "enrichment": {
            "strategy": "regex_ner_light_first",
            "documents_enriched": len(enrichment_notes),
            "details": enrichment_notes,
        },
        "documents_checked": len(documents),
        "validation_time_ms": duration_ms,
    }

    logger.info(
        "Validation : %d docs, statut=%s, anomalies=%s, durée=%dms",
        len(documents), status, anomaly_count, duration_ms,
    )

    return jsonify(response), 200


@app.route("/api/rules", methods=["GET"])
def list_rules():
    """Liste toutes les règles de validation disponibles."""
    rules_list = []
    for rule_id, rule in RULES.items():
        rules_list.append({
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "severity": rule.severity,
            "document_types_concerned": rule.document_types_concerned,
        })
    return jsonify({"rules": rules_list, "total": len(rules_list)}), 200


@app.route("/api/health", methods=["GET"])
def health():
    """Statut du service de validation."""
    return jsonify({
        "status": "ok",
        "service": "validation-service",
        "rules_count": len(RULES),
        "statistical_model_trained": stat_detector.trained,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
