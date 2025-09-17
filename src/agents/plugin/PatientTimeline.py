from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
import json


class PatientTimeline:
    @kernel_function(
        name="create_patient_timeline",
        description="Creates a patient timeline document given the patient's medical history.",
    )
    async def create_patient_timeline(self, kernel: Kernel, patient_data: str) -> str:
        print(f">>>>Patient Data: {patient_data}")
        return "PATIENT TIMELINE"
        # prompt = (
        #     "Given the following patient medical history, create a chronological timeline of key events:\n"
        #     f"{patient_data}\n"
        #     "Timeline:"
        # )
        # chat_service = kernel.get_service("chat_completion")
        # response = await chat_service.complete(prompt)
        # return response
