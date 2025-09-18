from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from semantic_kernel.functions import kernel_function
import json
import os


class StorageQuery:
    def __init__(self, account_url: str, container_name: str):
        self.account_url = account_url
        self.container_name = container_name
        connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
        if connection_string:
            self.client = BlobServiceClient.from_connection_string(connection_string)
        else:
            # Fallback to DefaultAzureCredential if connection string is not set
            self.client = BlobServiceClient(account_url=self.account_url, credential=DefaultAzureCredential())
        self.container_client = self.client.get_container_client(self.container_name)

    @kernel_function(
        name="get_patient_data",
        description="Gets patient data from the storage",
    )
    def get_patient_data(self, patient_id: str) -> dict:
        """
        Fetch the first JSON file found in the specified blob folder and return its contents as a dict.
        """
        print(f"Looking for blobs with prefix: {patient_id}")
        blob_list = self.container_client.list_blobs(name_starts_with=patient_id)
        for blob in blob_list:
            print(f"Found blob: {blob.name}")
            if blob.name.endswith('.json'):
                blob_client = self.container_client.get_blob_client(blob)
                data = blob_client.download_blob().readall()
                print(f"Loaded data: {data[:100]}")  # Print first 100 bytes
                return json.loads(data)
        raise FileNotFoundError(f"No JSON file found in folder: {patient_id}")
