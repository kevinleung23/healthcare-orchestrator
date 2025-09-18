from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function
import os


class TumorBoardReview:
    def __init__(self, kernel: Kernel, output_dir: str = "./outputs"):
        self.kernel = kernel
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @kernel_function(
        name="create_tumor_board_review",
        description="Creates a tumor board review document for a patient.",
    )
    def create_tumor_board_review(self, patient_timeline: str, patient_status: str) -> str:
        print("Creating tumor board review document...")
        return f"""
        Patient Tumor Board Review
        Patient Timeline:
        {patient_timeline}

        Patient Status:
        {patient_status}
        """
