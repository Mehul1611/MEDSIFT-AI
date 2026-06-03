import json
import os
import httpx


class LLMConstants:
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
    OUTPUT_BASE_DIR = 'output/discharge_summaries'

    PREPROCESSOR_MODEL = 'llama3.2-vision'
    PLANNING_AGENT_MODEL = 'llama3.2'
    WRITER_AGENT_MODEL = 'llama3.2'

    PREPROCESSOR_TEMP = 0
    PLANNING_AGENT_TEMP = 0
    WRITER_AGENT_TEMP = 0
    PLANNING_MAX_ITERATIONS = 20

    class RetryConfig:
        LLM_EXCEPTIONS_TYPES = (
            json.JSONDecodeError,
            ConnectionError,
            TimeoutError,
            ValueError,
            TypeError,
            KeyError,
            httpx.ConnectError,
            httpx.ReadTimeout,
            httpx.ConnectTimeout,
        )
        MAX_RETRY_ATTEMPTS = 3
        EXPONENTIAL_WAIT_MULTIPLIER = 2
        EXPONENTIAL_WAIT_MIN = 1
        EXPONENTIAL_WAIT_MAX = 32
