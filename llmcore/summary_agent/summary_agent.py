from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from llmcore.constants import LLMConstants
from llmcore.summary_agent.prompt import SYSTEM_PROMPT, USER_PROMPT
from llmcore.utils.retry_decorator import retry_llm_call


class SummaryAgent:

    def _get_model(self) -> ChatOllama:
        return ChatOllama(
            model=LLMConstants.PREPROCESSOR_MODEL,
            base_url=LLMConstants.OLLAMA_BASE_URL,
            temperature=LLMConstants.PREPROCESSOR_TEMP,
        )

    def _get_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate([
            ('system', SYSTEM_PROMPT),
            ('human', [
                {'type': 'text', 'text': USER_PROMPT},
                {'type': 'image_url', 'image_url': 'data:image/png;base64,{base64_image}'},
            ]),
        ])

    def _clean_response(self, content: str) -> str:
        text = content.strip()
        if not text.startswith('```'):
            return text
        lines = text.split('\n')
        lines = lines[1:]
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        return '\n'.join(lines).strip()

    @retry_llm_call()
    def summarise_page(
        self,
        document_name: str,
        page_number: int,
        total_pages: int,
        base64_image: str,
    ) -> str:
        model = self._get_model()
        prompt = self._get_prompt_template().invoke({
            'document_name': document_name,
            'page_number': page_number,
            'total_pages': total_pages,
            'base64_image': base64_image,
        })
        response = model.invoke(prompt)
        return self._clean_response(response.content)
