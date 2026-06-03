from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from llmcore.constants import LLMConstants

def retry_llm_call():
    return retry(stop=stop_after_attempt(LLMConstants.RetryConfig.MAX_RETRY_ATTEMPTS), wait=wait_exponential(multiplier=LLMConstants.RetryConfig.EXPONENTIAL_WAIT_MULTIPLIER, min=LLMConstants.RetryConfig.EXPONENTIAL_WAIT_MIN, max=LLMConstants.RetryConfig.EXPONENTIAL_WAIT_MAX), retry=retry_if_exception_type(LLMConstants.RetryConfig.LLM_EXCEPTIONS_TYPES))
