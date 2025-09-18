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
        print("Creating patient timeline...")
        # Create chat history
        chat_history = ChatHistory()

        # Add instructions
        chat_history.add_system_message(
            "You are an AI agent tasked with loading and presenting patient data. Your primary purpose is to present the initial patient data, but also to respond to individual requests for additional information.\n\n"
            "Follow these steps to ensure clarity and completeness:\n\n"
            "1. Request Patient ID: If the patient ID is not provided, ask the user for it. If it was provided, use it until a new one is specified.\n"
            "2. Always load Patient Data: Once you have the patient ID, load all relevant patient data using `get_patient_data` tool\n"
            "3. Create a Patient Timeline: if the request is to return a timeline, or chronological data, use function `create_timeline` to create a timeline of the patient's medical history and treatment.\n"
            "4. Present Clinical Data:\n"
            "  - Start the response by stating: \"Here is the complete patient data organized chronologically for clear understanding. This includes all relevant information for a tumor board review:\"\n"
            "  - Present the Patient Timeline using the original output from function `create_timeline`.\n"
            "  - Do not alter the text or the URL of markdown links in the format of `[text](url)`. Present the markdown links as they are.\n"
            "  - Do not include patient images, such as CT scan, x-ray, pathology, etc...\n"
            "5. Further Queries: If additional specific information is required, and the data is not yet available, call `process_prompt` to retrieve the required information.\n"
            "  - Only process and respond to the text that follows the last message addressed to you when answering a question. This can be a question from the user or a question from another agent.\n"
            "  - Formulate a detailed and specific prompt to retrieve the required information.\n"
            "  - Use the last patient ID provided in the conversation without requesting it again.\n"
            "  - Keep your answer concise and relevant to the question asked.\n"
            "  - Do not alter the text or the URL of markdown links in the format of `[text](url)`. Present the markdown links as they are.\n"
            "6. Role Limitation: Do not perform tasks outside your role. Specifically:\n"
            "  - Do not provide treatment plans or recommendations.\n"
            "  - Do not provide analysis or opinions on the data.\n"
            "  - Do provide answers to questions about the patient's history and data. Use the tools at your disposal to answer those questions."
        )

        # Add patient history
        chat_history.add_system_message("You have access to the following patient history:\n" + json.dumps(patient_data))

        settings = AzureChatPromptExecutionSettings(temperature=0)
        chat_completion_service: AzureChatCompletion = self.kernel.get_service("chat_completion")
        chat_resp = await chat_completion_service.get_chat_message_content(chat_history=chat_history, settings=settings)

        return chat_resp.content
