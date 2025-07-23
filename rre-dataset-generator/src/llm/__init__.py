from .llm_provider_factory import build_openai, build_gemini
from .llm_config import LLMConfig
from langchain_core.language_models import BaseChatModel
import logging

log = logging.getLogger(__name__)

PROVIDER_REGISTRY = {
    "openai": build_openai,
    "gemini": build_gemini,
}


def build_chat_model(config: LLMConfig) -> BaseChatModel:
    provider_name = config.name
    if provider_name not in PROVIDER_REGISTRY:
        log.error("Unsupported LLM provider requested: %s", provider_name)
        raise ValueError(f"Unsupported provider: {provider_name}")
    log.info("Selected LLM provider: %s", provider_name)
    return PROVIDER_REGISTRY[provider_name](config)
