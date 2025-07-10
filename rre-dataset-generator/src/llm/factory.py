"""
factory.py

Provides a simple Factory for creating LangChain ChatModel instances
based on a provider name and its configuration.

"""

import os
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from .llm_config import ProviderCfg


def build_openai(cfg: ProviderCfg) -> BaseChatModel:
    key = os.getenv(cfg.api_key_env or "OPENAI_API_KEY")
    if not key:
        raise ValueError("OpenAI API key not set.")
    return ChatOpenAI(
        model=cfg.model,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=key,
    )


def build_gemini(cfg: ProviderCfg) -> BaseChatModel:
    key = os.getenv(cfg.api_key_env or "GOOGLE_API_KEY")
    if not key:
        raise ValueError("Google API key not set.")
    return ChatGoogleGenerativeAI(
        model=cfg.model,
        temperature=cfg.temperature,
        max_output_tokens=cfg.max_tokens,
        google_api_key=key,
    )


PROVIDER_REGISTRY = {
    "openai": build_openai,
    "gemini": build_gemini,
}


def build_chat_model(provider_name: str, cfg: ProviderCfg) -> BaseChatModel:
    if provider_name not in PROVIDER_REGISTRY:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return PROVIDER_REGISTRY[provider_name](cfg)

