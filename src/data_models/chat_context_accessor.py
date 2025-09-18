# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import logging
from azure.storage.blob.aio import BlobServiceClient

logger = logging.getLogger(__name__)


class ChatContextAccessor:
    """Accessor for chat context data stored in blob storage."""
    
    def __init__(self, blob_service_client: BlobServiceClient):
        self.blob_service_client = blob_service_client
        self.container_name = "chat-contexts"
    
    def get_blob_path(self, conversation_id: str, context_file: str) -> str:
        """Get the blob path for a chat context file."""
        return f"{conversation_id}/{context_file}"
    
    async def read(self, conversation_id: str, context_file: str) -> bytes:
        """Read chat context data from blob storage."""
        blob_path = self.get_blob_path(conversation_id, context_file)
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Download blob content
            download_stream = await blob_client.download_blob()
            data = await download_stream.readall()
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to read chat context {blob_path}: {e}")
            raise
    
    async def write(self, conversation_id: str, context_file: str, data: bytes) -> None:
        """Write chat context data to blob storage."""
        blob_path = self.get_blob_path(conversation_id, context_file)
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Upload blob content
            await blob_client.upload_blob(
                data,
                overwrite=True
            )
            
            logger.info(f"Successfully wrote chat context {blob_path}")
            
        except Exception as e:
            logger.error(f"Failed to write chat context {blob_path}: {e}")
            raise
    
    async def exists(self, conversation_id: str, context_file: str) -> bool:
        """Check if a chat context file exists in blob storage."""
        blob_path = self.get_blob_path(conversation_id, context_file)
        
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            return await blob_client.exists()
            
        except Exception as e:
            logger.error(f"Failed to check existence of chat context {blob_path}: {e}")
            return False