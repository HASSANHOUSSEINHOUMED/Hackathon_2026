"""
Client Python MongoDB pour les métadonnées et le tracking du pipeline.
"""
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError

load_dotenv()

logger = logging.getLogger("storage.metadata")


class MetadataDB:
    """Gestion des métadonnées documents et fournisseurs dans MongoDB."""

    def __init__(self) -> None:
        self.uri = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe2024!@localhost:27017/hackathon?authSource=admin")
        self.db_name = os.getenv("MONGO_DB_NAME", "hackathon")

        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]
        self.documents = self.db["documents"]
        self.suppliers = self.db["suppliers"]

        logger.info("MetadataDB connecté : %s / %s", self.uri.split("@")[-1], self.db_name)

    # ═══════════════════════════════════════
    # Documents
    # ═══════════════════════════════════════
    def insert_document(self, doc: dict) -> str:
        """Insère un nouveau document et retourne son _id."""
        doc.setdefault("created_at", datetime.utcnow())
        doc.setdefault("pipeline_status", "raw")
        result = self.documents.insert_one(doc)
        logger.info("Document inséré : %s", doc.get("document_id"))
        return str(result.inserted_id)

    def get_document(self, document_id: str) -> dict | None:
        """Récupère un document par son document_id."""
        return self.documents.find_one({"document_id": document_id}, {"_id": 0})

    def update_pipeline_status(self, document_id: str, status: str, data: dict | None = None) -> bool:
        """Met à jour le statut pipeline d'un document."""
        update = {"$set": {"pipeline_status": status, "processed_at": datetime.utcnow()}}
        if data:
            for key, value in data.items():
                update["$set"][key] = value
        result = self.documents.update_one({"document_id": document_id}, update)
        return result.modified_count > 0

    def get_pending_documents(self) -> list[dict]:
        """Retourne les documents en attente de traitement."""
        return list(self.documents.find(
            {"pipeline_status": "raw"},
            {"_id": 0},
        ).sort("created_at", ASCENDING))

    def find_by_type(self, doc_type: str) -> list[dict]:
        """Trouve tous les documents d'un type donné."""
        return list(self.documents.find(
            {"doc_type": doc_type},
            {"_id": 0},
        ).sort("created_at", DESCENDING))

    def find_by_siret(self, siret: str) -> list[dict]:
        """Trouve tous les documents liés à un SIRET."""
        return list(self.documents.find(
            {"entities.siret": siret},
            {"_id": 0},
        ).sort("created_at", DESCENDING))

    def get_anomaly_summary(self) -> dict:
        """Statistiques des anomalies par règle et sévérité."""
        pipeline = [
            {"$unwind": "$anomalies"},
            {"$group": {
                "_id": {"rule": "$anomalies.rule", "severity": "$anomalies.severity"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"count": -1}},
        ]
        results = list(self.documents.aggregate(pipeline))
        summary = {"by_rule": {}, "by_severity": {"ERROR": 0, "WARNING": 0, "INFO": 0}}
        for r in results:
            rule = r["_id"]["rule"]
            severity = r["_id"]["severity"]
            count = r["count"]
            summary["by_rule"][rule] = summary["by_rule"].get(rule, 0) + count
            summary["by_severity"][severity] += count
        return summary

    # ═══════════════════════════════════════
    # Fournisseurs
    # ═══════════════════════════════════════
    def upsert_supplier(self, supplier: dict) -> str:
        """Crée ou met à jour un fournisseur (par SIRET)."""
        siret = supplier.get("siret")
        if not siret:
            raise ValueError("SIRET requis pour un fournisseur")

        supplier["updated_at"] = datetime.utcnow()
        result = self.suppliers.update_one(
            {"siret": siret},
            {"$set": supplier, "$setOnInsert": {"created_at": datetime.utcnow()}},
            upsert=True,
        )
        return siret

    def get_supplier(self, siret: str) -> dict | None:
        """Récupère un fournisseur par SIRET."""
        return self.suppliers.find_one({"siret": siret}, {"_id": 0})

    def list_suppliers(self, status: str | None = None) -> list[dict]:
        """Liste les fournisseurs, filtré optionnellement par statut."""
        query = {}
        if status:
            query["conformity_status"] = status
        return list(self.suppliers.find(query, {"_id": 0}).sort("updated_at", DESCENDING))

    def update_conformity(self, siret: str, status: str) -> bool:
        """Met à jour le statut de conformité d'un fournisseur."""
        result = self.suppliers.update_one(
            {"siret": siret},
            {"$set": {"conformity_status": status, "last_check": datetime.utcnow()}},
        )
        return result.modified_count > 0

    # ═══════════════════════════════════════
    # Utilitaires
    # ═══════════════════════════════════════
    def create_indexes(self) -> None:
        """Crée les index requis pour les performances."""
        self.documents.create_index("document_id", unique=True)
        self.documents.create_index("doc_type")
        self.documents.create_index("pipeline_status")
        self.documents.create_index("created_at")
        self.documents.create_index("entities.siret")
        self.suppliers.create_index("siret", unique=True)
        self.suppliers.create_index("conformity_status")
        logger.info("Index MongoDB créés")

    def get_db_stats(self) -> dict:
        """Statistiques de la base de données."""
        return {
            "documents_count": self.documents.count_documents({}),
            "suppliers_count": self.suppliers.count_documents({}),
            "by_status": {
                status: self.documents.count_documents({"pipeline_status": status})
                for status in ["raw", "ocr_done", "validated", "curated"]
            },
        }


if __name__ == "__main__":
    import json
    db = MetadataDB()
    db.create_indexes()
    print(json.dumps(db.get_db_stats(), indent=2))
