"""
Azure Blob Storage service for document file operations.

Handles file uploads, downloads, and SAS URL generation.
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import BinaryIO, Optional

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob import BlobSasPermissions, ContentSettings, generate_blob_sas
from azure.storage.blob.aio import BlobServiceClient, ContainerClient

from src.api.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for Azure Blob Storage operations."""

    _instance: Optional["StorageService"] = None
    _client: Optional[BlobServiceClient] = None
    _container: Optional[ContainerClient] = None
    _credential: Optional[DefaultAzureCredential] = None

    def __new__(cls) -> "StorageService":
        """Ensure single instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def initialize(self, settings: Optional[Settings] = None) -> None:
        """Initialize the Blob Storage client."""
        if self._client is not None:
            logger.debug("Blob Storage client already initialized")
            return

        settings = settings or get_settings()
        logger.info("Initializing Blob Storage client...")
        logger.info(f"  BLOB_ACCOUNT_URL: {settings.blob_account_url}")
        logger.info(f"  BLOB_CONTAINER_NAME: {settings.blob_container_name}")
        logger.info(f"  BLOB_CONNECTION_STRING present: {bool(settings.blob_connection_string)}")

        # Prefer Azure AD authentication (works with subscription policies that disable key access)
        if settings.blob_account_url:
            # Use Azure AD authentication via DefaultAzureCredential
            # This uses Azure CLI login for local dev, Managed Identity in Azure
            logger.info("Attempting Azure AD authentication for Blob Storage...")
            self._credential = DefaultAzureCredential(
                logging_enable=True,
                exclude_environment_credential=False,
                exclude_managed_identity_credential=False,
            )
            
            # Try to get a token to verify identity
            try:
                token = await self._credential.get_token("https://storage.azure.com/.default")
                logger.info(f"Successfully acquired token for storage, expires: {token.expires_on}")
                # Decode token to see which identity is used (without logging sensitive info)
                import base64
                import json
                try:
                    # JWT tokens have 3 parts separated by dots
                    parts = token.token.split('.')
                    if len(parts) >= 2:
                        # Decode the payload (second part)
                        payload = parts[1]
                        # Add padding if needed
                        padding = 4 - len(payload) % 4
                        if padding != 4:
                            payload += '=' * padding
                        decoded = base64.b64decode(payload)
                        claims = json.loads(decoded)
                        logger.info(f"Token identity - oid: {claims.get('oid', 'N/A')}, appid: {claims.get('appid', 'N/A')}, sub: {claims.get('sub', 'N/A')}")
                except Exception as decode_err:
                    logger.warning(f"Could not decode token claims: {decode_err}")
            except Exception as token_err:
                logger.error(f"Failed to acquire storage token: {token_err}", exc_info=True)
            
            self._client = BlobServiceClient(
                account_url=settings.blob_account_url,
                credential=self._credential,
            )
            logger.info("Using Azure AD authentication for Blob Storage")
        elif settings.blob_connection_string:
            # Fallback to connection string (if key access is enabled)
            self._client = BlobServiceClient.from_connection_string(
                settings.blob_connection_string
            )
            logger.info("Using connection string for Blob Storage")
        else:
            raise ValueError("BLOB_ACCOUNT_URL or BLOB_CONNECTION_STRING is required")

        self._container = self._client.get_container_client(settings.blob_container_name)
        logger.info(f"Blob Storage client initialized for container: {settings.blob_container_name}")

    async def close(self) -> None:
        """Close the Blob Storage client."""
        if self._client:
            await self._client.close()
            self._client = None
            self._container = None
        if self._credential:
            await self._credential.close()
            self._credential = None
        logger.info("Blob Storage client closed")

    @property
    def container(self) -> ContainerClient:
        """Get the container client."""
        if self._container is None:
            raise RuntimeError("Storage service not initialized. Call initialize() first.")
        return self._container

    def _build_blob_path(
        self, case_id: str, document_id: str, filename: str
    ) -> str:
        """
        Build the blob path for a document.

        Format: cases/{case_id}/documents/{document_id}/{filename}
        """
        # Sanitize filename to prevent path traversal
        safe_filename = filename.replace("/", "_").replace("\\", "_")
        return f"cases/{case_id}/documents/{document_id}/{safe_filename}"

    async def download_blob(self, blob_path: str) -> bytes:
        """
        Download blob content as bytes.

        Args:
            blob_path: The full path for the blob

        Returns:
            File content as bytes
        """
        blob_client = self.container.get_blob_client(blob_path)
        download_stream = await blob_client.download_blob()
        content = await download_stream.readall()
        logger.debug(f"Downloaded blob from: {blob_path} ({len(content)} bytes)")
        return content

    async def upload_blob(
        self,
        blob_path: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload raw bytes to a blob path.

        Args:
            blob_path: The full path for the blob (e.g., "case_id/main/filename.pdf")
            content: File content as bytes
            content_type: MIME type of the file

        Returns:
            The blob path where the content was uploaded
        """
        blob_client = self.container.get_blob_client(blob_path)

        await blob_client.upload_blob(
            content,
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True,
        )

        logger.info(f"Uploaded blob to: {blob_path} ({len(content)} bytes)")
        return blob_path

    async def upload_document(
        self,
        case_id: str,
        document_id: str,
        filename: str,
        content: BinaryIO,
        content_type: str,
        content_length: int,
    ) -> tuple[str, str]:
        """
        Upload a document to Blob Storage.

        Args:
            case_id: The parent case identifier
            document_id: The document identifier
            filename: Original filename
            content: File content as binary stream
            content_type: MIME type of the file
            content_length: Size of the file in bytes

        Returns:
            Tuple of (blob_path, md5_checksum)
        """
        blob_path = self._build_blob_path(case_id, document_id, filename)
        blob_client = self.container.get_blob_client(blob_path)

        # Calculate MD5 checksum while uploading
        hasher = hashlib.md5()
        chunks = []
        while chunk := content.read(8192):
            hasher.update(chunk)
            chunks.append(chunk)

        content_bytes = b"".join(chunks)
        md5_checksum = hasher.hexdigest()

        await blob_client.upload_blob(
            content_bytes,
            content_settings=ContentSettings(content_type=content_type),
            overwrite=True,
        )

        logger.info(f"Uploaded document to: {blob_path}")
        return blob_path, md5_checksum

    async def delete_document(self, blob_path: str) -> bool:
        """
        Delete a document from Blob Storage.

        Args:
            blob_path: The path to the blob

        Returns:
            True if deleted, False if not found
        """
        blob_client = self.container.get_blob_client(blob_path)
        try:
            await blob_client.delete_blob()
            logger.info(f"Deleted document: {blob_path}")
            return True
        except Exception as e:
            logger.warning(f"Failed to delete blob {blob_path}: {e}")
            return False

    async def get_download_url(
        self,
        blob_path: str,
        expiry_hours: Optional[int] = None,
    ) -> tuple[str, datetime]:
        """
        Generate a SAS URL for downloading a document.

        Args:
            blob_path: The path to the blob
            expiry_hours: Hours until URL expires (default from settings)

        Returns:
            Tuple of (download_url, expiry_datetime)
        """
        settings = get_settings()
        expiry_hours = expiry_hours or settings.sas_token_expiry_hours

        expiry = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

        # Get account name from URL
        if self._client and self._client.account_name:
            account_name = self._client.account_name
        else:
            raise RuntimeError("Cannot determine storage account name")

        # Generate SAS token
        if self._credential:
            # Use user delegation key for better security
            user_delegation_key = await self._client.get_user_delegation_key(
                key_start_time=datetime.now(timezone.utc),
                key_expiry_time=expiry,
            )
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=settings.blob_container_name,
                blob_name=blob_path,
                permission=BlobSasPermissions(read=True),
                expiry=expiry,
                user_delegation_key=user_delegation_key,
            )
        else:
            # Fallback to account key SAS
            sas_token = generate_blob_sas(
                account_name=account_name,
                container_name=settings.blob_container_name,
                blob_name=blob_path,
                permission=BlobSasPermissions(read=True),
                expiry=expiry,
                account_key=settings.cosmos_key,  # Note: In production, use separate storage key
            )

        download_url = f"{settings.blob_account_url}/{settings.blob_container_name}/{blob_path}?{sas_token}"

        logger.debug(f"Generated download URL for: {blob_path}, expires: {expiry}")
        return download_url, expiry

    async def check_health(self) -> bool:
        """
        Check if Blob Storage is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get container properties
            await self.container.get_container_properties()
            return True
        except Exception as e:
            logger.error(f"Blob Storage health check failed: {e}")
            return False


# Global service instance
storage_service = StorageService()
