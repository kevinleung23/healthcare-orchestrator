import asyncio

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


async def main():
    # Initialize the kernel
    kernel = Kernel()

    # Add Azure OpenAI chat completion
    load_dotenv()

    chat_completion = AzureChatCompletion(
        deployment_name=os.getenv("AZURE_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_DEPLOYMENT_KEY"),
        base_url=os.getenv("AZURE_DEPLOYMENT_ENDPOINT"),
    )
    kernel.add_service(chat_completion)

    # Add a plugins
    kernel.add_plugin(
        StorageQuery(
            account_url=os.getenv("STORAGE_ACCOUNT_URL"),
            container_name="patient-data",
        ),
        plugin_name="PatientDataStorage",
    )
    kernel.add_plugin(
        TumorBoardReview(),
        plugin_name="TumorBoardReview",
    )
    kernel.add_plugin(
        PatientTimeline(),
        plugin_name="PatientTimeline",
    )
    kernel.add_plugin(
        PatientStatus(),
        plugin_name="PatientStatus",
    )

    # Enable planning
    execution_settings = AzureChatPromptExecutionSettings()
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
