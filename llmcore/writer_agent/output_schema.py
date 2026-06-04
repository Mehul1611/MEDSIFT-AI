from pydantic import BaseModel, Field


class DischargeSummaryOutput(BaseModel):
    # Patient Information
    patient_demographics: str = Field(description='Patient age, sex, and other demographic information. Mark absent fields as [MISSING].')
    admission_discharge_dates: str = Field(description='Admission date and discharge date. Mark absent fields as [MISSING].')
    
    # Diagnoses
    principal_diagnosis: str = Field(description='Primary diagnosis for this admission. Mark as [MISSING] if not documented.')
    secondary_diagnoses: str = Field(description='Secondary or comorbid diagnoses. Mark as [MISSING] if not documented.')
    
    # Hospital Course and Procedures
    hospital_course: str = Field(description="Narrative summary of the patient's clinical course during hospitalization.")
    procedures: str = Field(description='Procedures performed during hospitalization with dates where available. Mark as [MISSING] if absent.')
    
    # Medications and Allergies
    discharge_medications: str = Field(description='Complete list of medications at discharge with drug name, dose, frequency, and route.')
    medication_changes: str = Field(description='Medications added, stopped, or changed with documented reasons. Undocumented changes are marked [FLAG: Reason not documented — Clinician Reconciliation Required].')
    allergies: str = Field(description='Known allergies with reactions if documented. Mark as [MISSING] if not documented.')
    
    # Follow-up Instructions
    follow_up_instructions: str = Field(description='Follow-up appointments, monitoring requirements, and patient instructions. Mark as [MISSING] if absent.')
    
    # Pending Results and Discharge Condition
    pending_results: str = Field(description="Laboratory results, cultures, or imaging still pending at discharge. State 'None pending' if all finalized.")
    discharge_condition: str = Field(description="Patient's condition at the time of discharge. Mark as [MISSING] if not documented.")
    
    # Document Conflicts
    document_conflicts: str = Field(description='All unresolved conflicts between source documents, including the conflicting values and the documents they originate from. Each conflict is marked [CONFLICT]. State "None identified" if no conflicts were found.')

    # Safety Flags
    safety_flags: str = Field(description='Safety concerns, drug interaction warnings, escalations, and items requiring urgent clinician attention.')
    
    # Missing Information
    missing_information: str = Field(description='Complete list of required fields not present in the clinical documentation. Each item is marked [MISSING - Clinician Review Required].')
    evidence_references: str = Field(description='Source document references for key clinical facts in the format: Document Name, Page N.')
    writer_activity_log: str = Field(description='Sequential log of how the writer transformed the structured plan into this discharge summary draft.')
