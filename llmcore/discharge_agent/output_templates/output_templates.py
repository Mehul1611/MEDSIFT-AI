from typing import Any


def format_field(value: str) -> str:
    return value.strip() if value and value.strip() else '_Not documented_'


def render_header() -> list[str]:
    return [
        '# DISCHARGE SUMMARY — DRAFT FOR CLINICIAN REVIEW',
        '',
        '> **This is an AI-generated draft. It must be reviewed and verified by a qualified clinician',
        '> before use in any clinical context. Do not use as a finalized clinical document.**',
        '',
        '---',
        '',
    ]


def render_clinical_sections(writer_output: dict[str, Any]) -> list[str]:
    field = format_field
    return [
        '## Patient Demographics',
        field(writer_output.get('patient_demographics', '')),
        '',
        '## Admission & Discharge Dates',
        field(writer_output.get('admission_discharge_dates', '')),
        '',
        '---',
        '',
        '## Principal Diagnosis',
        field(writer_output.get('principal_diagnosis', '')),
        '',
        '## Secondary Diagnoses',
        field(writer_output.get('secondary_diagnoses', '')),
        '',
        '---',
        '',
        '## Hospital Course',
        field(writer_output.get('hospital_course', '')),
        '',
        '## Procedures',
        field(writer_output.get('procedures', '')),
        '',
        '---',
        '',
        '## Allergies',
        field(writer_output.get('allergies', '')),
        '',
        '## Discharge Medications',
        field(writer_output.get('discharge_medications', '')),
        '',
        '## Medication Changes',
        field(writer_output.get('medication_changes', '')),
    ]


def render_follow_up_sections(writer_output: dict[str, Any]) -> list[str]:
    field = format_field
    return [
        '---',
        '',
        '## Follow-up Instructions',
        field(writer_output.get('follow_up_instructions', '')),
        '',
        '## Pending Results',
        field(writer_output.get('pending_results', '')),
        '',
        '## Discharge Condition',
        field(writer_output.get('discharge_condition', '')),
        '',
        '---',
        '',
        '## Safety Flags',
        field(writer_output.get('safety_flags', '')),
        '',
        '## Missing Information',
        field(writer_output.get('missing_information', '')),
    ]


def render_footer_sections(writer_output: dict[str, Any]) -> list[str]:
    field = format_field
    return [
        '---',
        '',
        '## Evidence References',
        field(writer_output.get('evidence_references', '')),
        '',
        '---',
        '',
        '## Writer Activity Log',
        field(writer_output.get('writer_activity_log', '')),
    ]


def render_markdown(writer_output: dict[str, Any]) -> str:
    lines = render_header()
    lines.extend(render_clinical_sections(writer_output))
    lines.extend(render_follow_up_sections(writer_output))
    lines.extend(render_footer_sections(writer_output))
    return '\n'.join(lines)
