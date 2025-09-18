import json
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import \
    AzureChatPromptExecutionSettings


class PatientStatus:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    @kernel_function(
        name="create_patient_status",
        description="Creates a patient status given the patient's timeline.",
    )
    async def create_patient_status(self, patient_timeline: str) -> str:
        print("Creating patient status...")
        # Create chat history
        chat_history = ChatHistory()

        # Add instructions
        chat_history.add_system_message(
            "Create a concise summary of the patient's current status based on their timeline."
            "This should not be more than 3-5 sentences."
        )

        # Add patient history
        chat_history.add_system_message("You have access to the following patient timeline:\n" + json.dumps(patient_timeline))

        settings = AzureChatPromptExecutionSettings(temperature=0)
        chat_completion_service: AzureChatCompletion = self.kernel.get_service("chat_completion")
        chat_resp = await chat_completion_service.get_chat_message_content(chat_history=chat_history, settings=settings)

        return chat_resp.content
