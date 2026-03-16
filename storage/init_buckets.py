import logging
import sys
from storage_client import get_minio_client, BUCKETS

# Logs en JSON structuré
logging.basicConfig(
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}',
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def init_buckets() -> None:
    """
    Crée les 3 zones du Data Lake dans MinIO si elles n'existent pas.
    Ce script est exécuté une seule fois au démarrage via Docker.
    """
    client = get_minio_client()

    for bucket_name, description in BUCKETS.items():
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Bucket created : {bucket_name} — {description}")
        else:
            logger.info(f"Bucket already exists : {bucket_name} — {description}")

    logger.info("Data Lake ready — 3 zones operational")


if __name__ == "__main__":
    init_buckets()