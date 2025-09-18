import asyncio
import uuid

from azure.identity.aio import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureChatPromptExecutionSettings,
)
from agents.plugin.PatientStatus import PatientStatus
from agents.plugin.PatientTimeline import PatientTimeline
from agents.plugin.TumorBoardReview import TumorBoardReview
from agents.plugin.StorageQuery import StorageQuery
from dotenv import load_dotenv
import os

from data_models.chat_context import ChatContext
from data_models.data_access import create_data_access
from tools.content_export.content_export import ContentExportPlugin


async def main():
    # Initialize the kernel
    kernel = Kernel()

    # Add Azure OpenAI chat completion
    load_dotenv()

    chat_completion = AzureChatCompletion(
        service_id="chat_completion",
        deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_DEPLOYMENT_KEY"),
        base_url=os.getenv("AZURE_DEPLOYMENT_ENDPOINT"),
    )
    kernel.add_service(chat_completion)

    # Create a chat context with a conversation ID
    conversation_id = str(uuid.uuid4())
    chat_ctx = ChatContext(conversation_id=conversation_id)
    
    # Create blob service client and credential for data access
    credential = DefaultAzureCredential()
    blob_service_client = BlobServiceClient(
        account_url=os.getenv("STORAGE_ACCOUNT_URL"),
        credential=credential
    )
    
    # Create data access using the factory function
    data_access = create_data_access(blob_service_client, credential)
    
    # Create storage plugin
    storage_plugin = StorageQuery(
        account_url=os.getenv("STORAGE_ACCOUNT_URL"),
        container_name="patient-data",
    )
    
    # Add a plugins
    kernel.add_plugin(
        storage_plugin,
        plugin_name="PatientDataStorage",
    )
    # kernel.add_plugin(
    #     TumorBoardReview(
    #         kernel=kernel,
    #     ),
    #     plugin_name="TumorBoardReview",
    # )
    kernel.add_plugin(
        PatientTimeline(
            kernel=kernel,
        ),
        plugin_name="PatientTimeline",
    )
    kernel.add_plugin(
        PatientStatus(
            kernel=kernel,
        ),
        plugin_name="PatientStatus",
    )

    kernel.add_plugin(
        ContentExportPlugin(
            kernel=kernel, 
            chat_ctx=chat_ctx, 
            data_access=data_access),
        plugin_name="ContentExport",
    )

    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings(temperature=0.0)
    execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    # Create a history of the conversation
    history = ChatHistory()

    # Initiate a back-and-forth chat
    userInput = None
    while True:
        # Collect user input
        userInput = input("User > ")

        # Terminate the loop if the user says "exit"
        if userInput == "exit":
            break

        # Add user input to the history
        history.add_user_message(userInput)

        # Get the response from the AI
        result = await chat_completion.get_chat_message_content(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel,
        )

        # Print the results
        print("Assistant > " + str(result))

        # Add the message from the agent to the chat history
        history.add_message(result)

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
