from functools import partial
from langchain.tools import StructuredTool
from llmcore.tools.tool_schemas.pdf_tool_schema import DrugInteractionSchema

_DRUG_INTERACTION_TOOL_NAME = 'DRUG_INTERACTION_TOOL'
_DRUG_INTERACTION_TOOL_DESCRIPTION = "Use this tool to check for known drug-drug interactions between medications identified in the patient's discharge medication list. Input a comma-separated list of medication names. If the tool returns a warning, record it in the SAFETY FLAGS section of your plan."


def _check_interactions(patient_id: str, medications: str) -> str:
    print(f'Drug interaction check for patient {patient_id}: {medications}')
    return f'[MOCK — Drug Interaction Check]\nMedications checked: {medications}\nResult: No critical interactions automatically detected. This is a mock check — flag for pharmacist review before discharge.'


def get_drug_interaction_tool(patient_id: str) -> StructuredTool:
    configured_fn = partial(_check_interactions, patient_id)
    return StructuredTool.from_function(func=configured_fn, name=_DRUG_INTERACTION_TOOL_NAME, description=_DRUG_INTERACTION_TOOL_DESCRIPTION, args_schema=DrugInteractionSchema)
