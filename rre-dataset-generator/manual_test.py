from src.llm.factory import build_chat_model
from src.llm.llm_config import LLMConfig
from src.llm.llm_service import LLMService


def main():
    # 1. Make sure LLM API key is set: e.g. export OPENAI_API_KEY=sk-...

    # 2. Load the LLM config
    llm_cfg = LLMConfig.load("llm_config.yaml")
    provider = llm_cfg.default_provider
    model_cfg = llm_cfg.providers[provider]

    # 3. Build the chat model via factory
    chat_model = build_chat_model(provider, model_cfg)

    # 4. Wrap it in LLM service
    llm = LLMService(chat_model=chat_model)

    # 5. Call your test method
    answer = llm.test_connection("Say hello in 5 different languages")
    print("LLM answer:", answer)


if __name__ == "__main__":
    main()
