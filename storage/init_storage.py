"""
Script d'initialisation du stockage (MinIO + MongoDB).
Attend la disponibilité des services, crée les buckets et les index.
"""
import json
import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init-storage")


def wait_for_minio(max_retries: int = 30, delay: float = 2.0) -> None:
    """Attend que MinIO soit disponible avec backoff."""
    from minio import Minio
    import os

    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ROOT_USER", os.getenv("MINIO_ACCESS_KEY", "admin"))
    secret_key = os.getenv("MINIO_ROOT_PASSWORD", os.getenv("MINIO_SECRET_KEY", "ChangeMe2024!"))

    for attempt in range(1, max_retries + 1):
        try:
            client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
            client.list_buckets()
            logger.info("✅ MinIO disponible (%s)", endpoint)
            return
        except Exception as e:
            logger.warning("⏳ MinIO non disponible (tentative %d/%d) : %s", attempt, max_retries, e)
            time.sleep(delay)

    logger.error("❌ MinIO non disponible après %d tentatives", max_retries)
    sys.exit(1)


def wait_for_mongodb(max_retries: int = 30, delay: float = 2.0) -> None:
    """Attend que MongoDB soit disponible."""
    from pymongo import MongoClient
    import os

    uri = os.getenv("MONGO_URI", "mongodb://admin:ChangeMe2024!@localhost:27017/hackathon?authSource=admin")

    for attempt in range(1, max_retries + 1):
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=3000)
            client.admin.command("ping")
            logger.info("✅ MongoDB disponible")
            client.close()
            return
        except Exception as e:
            logger.warning("⏳ MongoDB non disponible (tentative %d/%d) : %s", attempt, max_retries, e)
            time.sleep(delay)

    logger.error("❌ MongoDB non disponible après %d tentatives", max_retries)
    sys.exit(1)


def create_buckets() -> None:
    """Crée les 3 buckets MinIO si inexistants."""
    from storage_client import DataLakeClient

    client = DataLakeClient()
    for bucket in DataLakeClient.ZONES:
        client._ensure_bucket(bucket)
        logger.info("  Bucket %-15s : OK", bucket)


def create_indexes() -> None:
    """Crée les index MongoDB."""
    from mongo_client import MetadataDB

    db = MetadataDB()
    db.create_indexes()


def print_report() -> None:
    """Affiche un rapport de l'état du stockage."""
    from storage_client import DataLakeClient
    from mongo_client import MetadataDB

    dl = DataLakeClient()
    db = MetadataDB()

    minio_stats = dl.get_stats()
    db_stats = db.get_db_stats()

    print("\n" + "═" * 55)
    print("  📦 RAPPORT DE STOCKAGE — DOCUFLOW")
    print("═" * 55)
    print("\n  MinIO (Data Lake) :")
    for zone, stats in minio_stats.items():
        print(f"    {zone:20s} : {stats['count']} fichiers, {stats.get('total_size_mb', 0)} MB")

    print(f"\n  MongoDB :")
    print(f"    Documents    : {db_stats['documents_count']}")
    print(f"    Fournisseurs : {db_stats['suppliers_count']}")
    print(f"    Par statut   : {json.dumps(db_stats['by_status'])}")

    print("\n" + "═" * 55)


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()

    logger.info("Initialisation du stockage DocuFlow...")

    # 1. Attendre les services
    wait_for_minio()
    wait_for_mongodb()

    # 2. Créer les buckets
    logger.info("Création des buckets MinIO...")
    create_buckets()

    # 3. Créer les index MongoDB
    logger.info("Création des index MongoDB...")
    create_indexes()

    # 4. Rapport
    print_report()

    logger.info("✅ Initialisation terminée avec succès")


if __name__ == "__main__":
    main()
