import json
import logging
from json import JSONDecodeError
from typing import List, Union

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from src.logger import configure_logging
from src.model.document import Document

configure_logging(level=logging.INFO)
log = logging.getLogger(__name__)


class LLMService:
    def __init__(self, chat_model: BaseChatModel):
        self.chat_model = chat_model

    def generate_queries(self, document: Document, num_queries_generate_per_doc: int) -> Union[List[str], str]:
        """
        Generate queries based on the given document and num_queries_generate_per_doc and
        Returns a list of generated queries or just a generated string in case of LLM hallucination
        """
        system_prompt = (
            f"You are a helpful assistant! Generate {num_queries_generate_per_doc} "
            "keyword-phrase-based queries based on the given document below. "
            "**Output only** a JSON array of strings—nothing else. "
            "Example format: [\"first query\", \"second query\"]"
        )

        doc_json = document.model_dump_json()

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Document:\n{doc_json}")
        ]

        raw = self.chat_model.invoke(messages).content.strip()

        # in case LLM hallucinates
        try:
            return json.loads(raw)
        except JSONDecodeError:
            log.warning("LLM hallucinated and its response: %s", raw)
            return raw
