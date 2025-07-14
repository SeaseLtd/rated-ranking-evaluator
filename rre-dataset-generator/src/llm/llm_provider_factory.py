"""
llm_provider_factory.py

Provides a simple Factory for creating LangChain ChatModel instances
and currently only 2 LLMs - openai and gemini are supported in the factory.

"""

import os

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from .llm_config import LLMConfig


def build_openai(config: LLMConfig) -> BaseChatModel:
    load_dotenv()  # load .env file
    key = os.getenv(config.api_key_env or "OPENAI_API_KEY")
    if not key:
        raise ValueError("OpenAI API key not set.")
    return ChatOpenAI(
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        api_key=key,
    )


def build_gemini(config: LLMConfig) -> BaseChatModel:
    load_dotenv()  # load .env file
    key = os.getenv(config.api_key_env or "GOOGLE_API_KEY")
    if not key:
        raise ValueError("Google API key not set.")
    return ChatGoogleGenerativeAI(
        model=config.model,
        temperature=config.temperature,
        max_output_tokens=config.max_tokens,
        google_api_key=key,
    )


PROVIDER_REGISTRY = {
    "openai": build_openai,
    "gemini": build_gemini,
}


def build_chat_model(config: LLMConfig) -> BaseChatModel:
    provider_name = config.name
    if provider_name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return PROVIDER_REGISTRY[provider_name](config)
