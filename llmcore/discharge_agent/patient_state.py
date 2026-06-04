from typing_extensions import NotRequired, TypedDict


class DischargeOutput(TypedDict):
    patient_demographics: NotRequired[str]
    admission_discharge_dates: NotRequired[str]
    principal_diagnosis: NotRequired[str]
    secondary_diagnoses: NotRequired[str]
    hospital_course: NotRequired[str]
    procedures: NotRequired[str]
    discharge_medications: NotRequired[str]
    medication_changes: NotRequired[str]
    allergies: NotRequired[str]
    follow_up_instructions: NotRequired[str]
    pending_results: NotRequired[str]
    discharge_condition: NotRequired[str]
    safety_flags: NotRequired[str]
    missing_information: NotRequired[str]
    evidence_references: NotRequired[str]
    writer_activity_log: NotRequired[str]


class PatientState(TypedDict):
    patient_id: NotRequired[str]
    source_notes_dir: NotRequired[str]
    status: NotRequired[str]
    document_context: NotRequired[str]
    structured_plan: NotRequired[str]
    output: NotRequired[DischargeOutput]
    output_dir: NotRequired[str]
