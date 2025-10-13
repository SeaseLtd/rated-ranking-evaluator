"""
llm_provider_factory.py

Provides a simple Factory for creating LangChain ChatModel instances
and currently only 2 LLMs - openai and gemini are supported in the factory.

"""

import logging
import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from rre_tools.dataset_generator.llm.llm_config import LLMConfig

log = logging.getLogger(__name__)


def build_openai(config: LLMConfig) -> BaseChatModel:
    load_dotenv()  # load .env file
    key = os.getenv(config.api_key_env or "OPENAI_API_KEY")
    if not key:
        log.error("OpenAI API key not set %s in the env", config.api_key_env)
        raise ValueError("OpenAI API key not set.")
    log.debug("Building OpenAI ChatModel using model=%s", config.model)
    return ChatOpenAI(
        model=config.model,
        max_tokens=config.max_tokens, # type: ignore[arg-type]
        api_key=SecretStr(key),
    )


def build_gemini(config: LLMConfig) -> BaseChatModel:
    load_dotenv()  # load .env file
    key = os.getenv(config.api_key_env or "GOOGLE_API_KEY")
    if not key:
        log.error("Google API key not set %s in the env", config.api_key_env)
        raise ValueError("Google API key not set.")
    log.debug("Building Google Gemini ChatModel using model=%s", config.model)
    return ChatGoogleGenerativeAI(
        model=config.model,
        max_output_tokens=config.max_tokens,
        google_api_key=key,
    )

class LLMServiceFactory:
    PROVIDER_REGISTRY = {
        "openai": build_openai,
        "gemini": build_gemini,
    }

    @classmethod
    def build(cls, config: LLMConfig) -> BaseChatModel:
        provider_name = config.name
        if provider_name not in cls.PROVIDER_REGISTRY:
            log.error("Unsupported LLM provider requested: %s", provider_name)
            raise ValueError(f"Unsupported provider: {provider_name}")
        log.info("Selected LLM provider: %s", provider_name)
        return cls.PROVIDER_REGISTRY[provider_name](config)
