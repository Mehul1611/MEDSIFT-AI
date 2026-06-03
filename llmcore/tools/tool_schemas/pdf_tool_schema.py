from pydantic import BaseModel, Field

class ReadPdfSchema(BaseModel):
    document_name: str = Field(description="Name of the PDF document file (e.g. 'admission_note.pdf')")
    start_page: int = Field(description='Page number to start reading from (1-indexed)')
    end_page: int = Field(description='Page number to end reading at (1-indexed, inclusive)')

class DrugInteractionSchema(BaseModel):
    medications: str = Field(description='Comma-separated list of medication names to check for interactions')

class EscalateCliniciianSchema(BaseModel):
    concern: str = Field(description='Clinical concern or safety flag to escalate for clinician review')
    severity: str = Field(description='Severity level: HIGH, MEDIUM, or LOW')
