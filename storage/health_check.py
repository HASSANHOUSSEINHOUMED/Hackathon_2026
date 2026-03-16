import logging
from storage_client import get_minio_client, get_mongo_collection, BUCKETS

logger = logging.getLogger(__name__)


def check_minio() -> dict:
    """Vérifie que MinIO est accessible et que les 3 zones existent."""
    try:
        client = get_minio_client()
        missing = []

        for bucket_name in BUCKETS:
            if not client.bucket_exists(bucket_name):
                missing.append(bucket_name)

        if missing:
            return {"status": "error", "missing_buckets": missing}

        return {"status": "ok", "buckets": list(BUCKETS.keys())}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


def check_mongo() -> dict:
    """Vérifie que MongoDB est accessible."""
    try:
        col = get_mongo_collection("documents")
        # Compte le nombre de documents pour tester la connexion
        count = col.count_documents({})
        return {"status": "ok", "documents_count": count}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


def full_health_check() -> dict:
    """Retourne le statut complet du Data Lake (MinIO + MongoDB)."""
    return {
        "minio": check_minio(),
        "mongodb": check_mongo(),
    }


if __name__ == "__main__":
    result = full_health_check()
    print(result)