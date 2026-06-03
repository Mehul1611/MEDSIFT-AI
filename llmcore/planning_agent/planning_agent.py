import json
from typing import List, Tuple
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate as HumanTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate as SystemTemplate,
)
from langchain_ollama import ChatOllama
from llmcore.constants import LLMConstants
from llmcore.planning_agent.planning_prompts import SYSTEM_PROMPT, USER_PROMPT
from llmcore.tools.drug_interaction_tool import get_drug_interaction_tool
from llmcore.tools.escalate_clinician_tool import get_escalate_clinician_tool
from llmcore.tools.read_pdf_tool import get_read_pdf_tool
from llmcore.utils.retry_decorator import retry_llm_call


class PlanningAgent:

    def __init__(self, patient_id: str, notes_dir: str) -> None:
        self.patient_id = patient_id
        self.notes_dir = notes_dir

    def _get_model(self) -> ChatOllama:
        return ChatOllama(
            model=LLMConstants.PLANNING_AGENT_MODEL,
            base_url=LLMConstants.OLLAMA_BASE_URL,
            temperature=LLMConstants.PLANNING_AGENT_TEMP,
        )

    def _get_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages([
            SystemTemplate(prompt=PromptTemplate(input_variables=[''], template=SYSTEM_PROMPT)),
            HumanTemplate(prompt=PromptTemplate(input_variables=['document_context'], template='{document_context}')),
            HumanTemplate(prompt=PromptTemplate(
                input_variables=['patient_id', 'available_documents'],
                template=USER_PROMPT,
            )),
            MessagesPlaceholder(variable_name='agent_scratchpad'),
        ])

    def _get_tools(self) -> list:
        return [
            get_read_pdf_tool(notes_dir=self.notes_dir),
            get_drug_interaction_tool(patient_id=self.patient_id),
            get_escalate_clinician_tool(patient_id=self.patient_id),
        ]

    def _get_agent_executor(self) -> AgentExecutor:
        model = self._get_model()
        tools = self._get_tools()
        prompt = self._get_prompt()
        agent = create_tool_calling_agent(llm=model, tools=tools, prompt=prompt)
        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=LLMConstants.PLANNING_MAX_ITERATIONS,
            handle_parsing_errors=True,
            return_intermediate_steps=True,
        )

    def _format_trace(self, intermediate_steps: list) -> str:
        lines = ['# Planning Agent Trace', '']
        for i, (action, observation) in enumerate(intermediate_steps, start=1):
            lines.append(f'## Step {i}')
            lines.append('')
            reasoning = getattr(action, 'log', '').strip()
            if reasoning:
                lines.append(f'**Reasoning:** {reasoning}')
                lines.append('')
            tool_name = getattr(action, 'tool', 'unknown')
            tool_input = getattr(action, 'tool_input', {})
            lines.append(f'**Tool:** {tool_name}')
            lines.append('')
            lines.append(f'**Input:**')
            lines.append('```json')
            lines.append(json.dumps(tool_input, indent=2) if isinstance(tool_input, dict) else str(tool_input))
            lines.append('```')
            lines.append('')
            lines.append(f'**Result:** {observation}')
            lines.append('')
        return '\n'.join(lines).strip() + '\n'

    @retry_llm_call()
    def invoke_planning_agent(self, document_context: str, available_documents: List[str]) -> Tuple[str, str]:
        agent_executor = self._get_agent_executor()
        available_docs_str = '\n'.join(f'- {d}' for d in available_documents)
        print(f'Generating clinical plan for patient {self.patient_id}')

        response = agent_executor.invoke({
            'document_context': document_context,
            'patient_id': self.patient_id,
            'available_documents': available_docs_str,
        })

        structured_plan = response.get('output')
        trace = self._format_trace(response.get('intermediate_steps', []))
        print(f'Planning complete for patient {self.patient_id}')
        return structured_plan, trace
