import json
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import \
    AzureChatPromptExecutionSettings


class PatientTimeline:
    def __init__(self, kernel: Kernel):
        self.kernel = kernel

    @kernel_function(
        name="create_patient_timeline",
        description="Creates a patient timeline document given the patient's medical history.",
    )
    async def create_patient_timeline(self, patient_data: str) -> str:
        # Create chat history
        chat_history = ChatHistory()

        # Add instructions
        chat_history.add_system_message(
            "Create a chronological timeline of key events from the patient's medical history."
        )

        # Add patient history
        chat_history.add_system_message("You have access to the following patient history:\n" + json.dumps(patient_data))

        settings = AzureChatPromptExecutionSettings(temperature=0)
        chat_completion_service: AzureChatCompletion = self.kernel.get_service("chat_completion")
        chat_resp = await chat_completion_service.get_chat_message_content(chat_history=chat_history, settings=settings)

        return chat_resp.content
