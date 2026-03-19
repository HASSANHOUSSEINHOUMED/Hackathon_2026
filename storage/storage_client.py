"""
Client Python pour le Data Lake MinIO (3 zones : raw, clean, curated).
"""
import io
import json
import logging
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

logger = logging.getLogger("storage.datalake")


class DataLakeClient:
    """Client pour le stockage Data Lake sur MinIO."""

    ZONES = ["raw-zone", "clean-zone", "curated-zone"]

    def __init__(self) -> None:
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ROOT_USER", os.getenv("MINIO_ACCESS_KEY", "admin"))
        self.secret_key = os.getenv("MINIO_ROOT_PASSWORD", os.getenv("MINIO_SECRET_KEY", "ChangeMe2024!"))
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )
        logger.info("DataLakeClient connecté à MinIO : %s", self.endpoint)

    def _ensure_bucket(self, bucket: str) -> None:
        """Crée le bucket s'il n'existe pas."""
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)
            logger.info("Bucket créé : %s", bucket)

    def _date_prefix(self) -> str:
        """Retourne le préfixe date du jour (YYYY-MM-DD)."""
        return datetime.now().strftime("%Y-%m-%d")

    def upload_raw(self, file_path: str, document_id: str, metadata: dict | None = None) -> str:
        """
        Upload un fichier brut dans raw-zone.

        Args:
            file_path: chemin local du fichier
            document_id: identifiant unique du document
            metadata: métadonnées additionnelles

        Returns:
            URL presigned d'accès (valable 24h)
        """
        bucket = "raw-zone"
        self._ensure_bucket(bucket)

        ext = os.path.splitext(file_path)[1]
        object_name = f"{self._date_prefix()}/{document_id}{ext}"

        meta = {"uploader": "api", "original_name": os.path.basename(file_path)}
        if metadata:
            meta.update({k: str(v) for k, v in metadata.items()})

        self.client.fput_object(bucket, object_name, file_path, metadata=meta)
        logger.info("Upload raw : %s/%s", bucket, object_name)

        url = self.client.presigned_get_object(bucket, object_name, expires=timedelta(hours=24))
        return url

    def upload_clean(self, document_id: str, ocr_result: dict) -> str:
        """
        Upload le résultat OCR (JSON) dans clean-zone.

        Args:
            document_id: identifiant du document
            ocr_result: dictionnaire des résultats OCR

        Returns:
            Chemin MinIO de l'objet
        """
        bucket = "clean-zone"
        self._ensure_bucket(bucket)

        object_name = f"{self._date_prefix()}/{document_id}.json"
        data = json.dumps(ocr_result, ensure_ascii=False, indent=2).encode("utf-8")
        data_stream = io.BytesIO(data)

        self.client.put_object(
            bucket, object_name, data_stream, len(data),
            content_type="application/json",
        )
        logger.info("Upload clean : %s/%s", bucket, object_name)
        return f"{bucket}/{object_name}"

    def upload_curated(self, document_id: str, structured_data: dict) -> str:
        """
        Upload les données structurées dans curated-zone.
        Si le document existe déjà, archive l'ancienne version.

        Args:
            document_id: identifiant du document
            structured_data: données structurées finales

        Returns:
            Chemin MinIO de l'objet
        """
        bucket = "curated-zone"
        self._ensure_bucket(bucket)

        object_name = f"{self._date_prefix()}/{document_id}.json"

        # Versionning : archiver l'existant
        try:
            self.client.stat_object(bucket, object_name)
            archive_name = f"archive/{document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.client.copy_object(
                bucket, archive_name,
                f"/{bucket}/{object_name}",
            )
            logger.info("Version archivée : %s/%s", bucket, archive_name)
        except S3Error:
            pass  # L'objet n'existe pas encore

        data = json.dumps(structured_data, ensure_ascii=False, indent=2).encode("utf-8")
        data_stream = io.BytesIO(data)

        self.client.put_object(
            bucket, object_name, data_stream, len(data),
            content_type="application/json",
        )
        logger.info("Upload curated : %s/%s", bucket, object_name)
        return f"{bucket}/{object_name}"

    def get_raw_url(self, document_id: str) -> str | None:
        """Génère une presigned URL pour télécharger un fichier raw (valable 1h)."""
        bucket = "raw-zone"
        # Chercher le fichier dans le bucket
        for obj in self.client.list_objects(bucket, recursive=True):
            if document_id in obj.object_name:
                return self.client.presigned_get_object(
                    bucket, obj.object_name, expires=timedelta(hours=1),
                )
        return None

    def get_curated(self, document_id: str) -> dict | None:
        """Télécharge et désérialise le JSON depuis curated-zone."""
        bucket = "curated-zone"
        for obj in self.client.list_objects(bucket, recursive=True):
            if document_id in obj.object_name and "archive" not in obj.object_name:
                response = self.client.get_object(bucket, obj.object_name)
                data = json.loads(response.read().decode("utf-8"))
                response.close()
                response.release_conn()
                return data
        return None


    def get_stats(self) -> dict:
        """Retourne les statistiques de stockage par bucket."""
        stats = {}
        for bucket in self.ZONES:
            if not self.client.bucket_exists(bucket):
                stats[bucket] = {"count": 0, "total_size_bytes": 0}
                continue
            count = 0
            total_size = 0
            for obj in self.client.list_objects(bucket, recursive=True):
                count += 1
                total_size += obj.size or 0
            stats[bucket] = {
                "count": count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
            }
        return stats


if __name__ == "__main__":
    client = DataLakeClient()
    print(json.dumps(client.get_stats(), indent=2))
