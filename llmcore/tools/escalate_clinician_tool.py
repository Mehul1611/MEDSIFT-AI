from functools import partial
from langchain.tools import StructuredTool
from llmcore.tools.tool_schemas.pdf_tool_schema import EscalateCliniciianSchema

_ESCALATE_CLINICIAN_TOOL_NAME = 'ESCALATE_CLINICIAN_TOOL'
_ESCALATE_CLINICIAN_TOOL_DESCRIPTION = 'Use this tool to formally escalate a clinical safety concern for clinician review. Use it when you identify: medication errors, high-risk drug interactions, missing critical safety information, documentation conflicts in safety-relevant fields, or any finding that requires urgent clinical attention. The escalation is recorded and surfaced in the SAFETY FLAGS section of the plan.'


def _escalate(patient_id: str, concern: str, severity: str) -> str:
    print(f'[ESCALATION] Patient {patient_id} | {severity} | {concern}')
    return f'[ESCALATION RECORDED]\nSeverity: {severity}\nConcern: {concern}\nAction: Flagged for clinician review. Record this in the SAFETY FLAGS section of your plan.'


def get_escalate_clinician_tool(patient_id: str) -> StructuredTool:
    configured_fn = partial(_escalate, patient_id)
    return StructuredTool.from_function(func=configured_fn, name=_ESCALATE_CLINICIAN_TOOL_NAME, description=_ESCALATE_CLINICIAN_TOOL_DESCRIPTION, args_schema=EscalateCliniciianSchema)
