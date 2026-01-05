
import boto3
import logging
from botocore.exceptions import ClientError
from config import get_settings
from io import BytesIO

logger = logging.getLogger(__name__)
settings = get_settings()

class MinIOClient:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=f"http://{settings.MINIO_ENDPOINT}",
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY
        )
        self.bucket = settings.MINIO_BUCKET_RAW
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.s3.head_bucket(Bucket=self.bucket)
        except ClientError:
            try:
                self.s3.create_bucket(Bucket=self.bucket)
                logger.info(f"Created bucket: {self.bucket}")
            except Exception as e:
                logger.error(f"Failed to create bucket: {e}")
                raise

    def put_object(self, key: str, data: bytes) -> str:
        """Uploads data to MinIO and returns the key."""
        try:
            self.s3.upload_fileobj(BytesIO(data), self.bucket, key)
            return key
        except Exception as e:
            logger.error(f"Upload failed for {key}: {e}")
            raise

    def get_object(self, key: str) -> bytes:
        """Downloads data from MinIO."""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as e:
            logger.error(f"Download failed for {key}: {e}")
            raise
            raise

    def get_storage_path(self, cik: str, accession: str, ext: str = "txt") -> str:
        """Returns deterministic path: raw/{cik}/{accession}.{ext}"""
        return f"raw/{cik}/{accession}.{ext}"

    def exists(self, key: str) -> bool:
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
