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
            "You are an AI agent that provides the patient's current status. "
            "Make sure to explicitly mention these characteristics before presenting the patient's current status.\n"
            "  'age':\n"
            "  'patient_gender':\n"
            "  'staging':\n"
            "  'primary site':\n"
            "  'histology':\n"
            "  'biomarkers'\n"
            "  'treatment history':\n"
            "  'ecog performance status':\n\n"
            "Don't proceed unless you have all of this information.\n"
            "You may infer this information from the conversation if it is available.\n"
            "If this information is not available, ask PatientHistory specifically for the missing information.\n"
            "DO:\n"
            "  Ask PatientHistory. EXAMPLE: \"*PatientHistory*, can you provide me with the patient's #BLANK?. Try to infer the information if not available\"."
        )

        # Add patient history
        chat_history.add_system_message("You have access to the following patient timeline:\n" + json.dumps(patient_timeline))

        settings = AzureChatPromptExecutionSettings(temperature=0)
        chat_completion_service: AzureChatCompletion = self.kernel.get_service("chat_completion")
        chat_resp = await chat_completion_service.get_chat_message_content(chat_history=chat_history, settings=settings)

        return chat_resp.content
