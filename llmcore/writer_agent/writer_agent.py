from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate as HumanTemplate,
    SystemMessagePromptTemplate as SystemTemplate,
)
from langchain_ollama import ChatOllama
from llmcore.constants import LLMConstants
from llmcore.utils.retry_decorator import retry_llm_call
from llmcore.writer_agent.output_schema import DischargeSummaryOutput
from llmcore.writer_agent.writer_prompts import SYSTEM_PROMPT, USER_PROMPT


class WriterAgent:

    def _get_model(self) -> ChatOllama:
        return ChatOllama(
            model=LLMConstants.WRITER_AGENT_MODEL,
            base_url=LLMConstants.OLLAMA_BASE_URL,
            temperature=LLMConstants.WRITER_AGENT_TEMP,
            format='json',
        )

    def _get_structured_model(self):
        return self._get_model().with_structured_output(DischargeSummaryOutput)

    def _get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_messages(
            [
                SystemTemplate(
                    prompt=PromptTemplate(
                        input_variables=['schema'],
                        template=SYSTEM_PROMPT,
                    )
                ),
                HumanTemplate(
                    prompt=PromptTemplate(
                        input_variables=['structured_plan'],
                        template=USER_PROMPT,
                    )
                ),
            ]
        )

    def _build_prompt(self, structured_plan: str):
        prompt_template = self._get_prompt_template()
        return prompt_template.invoke({
            'schema': DischargeSummaryOutput.model_json_schema(),
            'structured_plan': structured_plan,
        })

    @retry_llm_call()
    def invoke_writer_agent(self, structured_plan: str) -> dict:
        model = self._get_structured_model()
        prompt = self._build_prompt(structured_plan)
        response = model.invoke(prompt)
        return response.model_dump()
