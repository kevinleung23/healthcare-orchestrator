from semantic_kernel.functions import kernel_function


class PatientStatus:
    @kernel_function(
        name="create_patient_status",
        description="Creates a patient status document given the patient's timeline.",
    )
    def create_patient_status(self, patient_timeline: str) -> str:
        print(">>>>>>>>>>>>>>>>>>>>> Creating Patient Status...")
        return "PATIENT STATUS"
