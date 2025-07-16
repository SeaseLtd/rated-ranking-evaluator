"""
Pydantic models for the LLM service.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    """Represents a single message in the conversation."""
    role: MessageRole = Field(..., description="The role of the message sender")
    content: str = Field(..., min_length=1, description="The content of the message")
    name: Optional[str] = Field(
        None, 
        min_length=1,
        description="The name of the message sender (optional)"
    )

class LLMRequest(BaseModel):
    """Input model for LLM service requests."""
    messages: List[Message] = Field(
        ...,
        min_items=1,
        description="List of messages in the conversation"
    )
    # temperature: Optional[float] = Field(
    #     None,
    #     ge=0.0,
    #     le=2.0,
    #     description="Controls randomness in the response generation"
    # )
    # max_tokens: Optional[int] = Field(
    #     None,
    #     gt=0,
    #     description="Maximum number of tokens to generate"
    # )

    @field_validator('messages')
    def validate_messages(cls, v: List[Message]) -> List[Message]:
        if not v:
            raise ValueError("At least one message is required")
        # Ensure the first message is from the system if there are multiple messages
        if len(v) > 1 and v[0].role != MessageRole.SYSTEM:
            raise ValueError("First message should be a system message when multiple messages are provided")
        return v

class LLMResponse(BaseModel):
    """Output model for LLM service responses."""
    content: str = Field(..., description="The generated response content")
    model: str = Field(..., description="The model used for generation")
    usage: Dict[str, int] = Field(
        ...,
        description="Token usage information (prompt_tokens, completion_tokens, total_tokens)"
    )
    finish_reason: str = Field(
        ...,
        description="Reason why the generation stopped (e.g., 'stop', 'length', 'content_filter')"
    )


"""
USAGE:
# E.g: In the main orchestrator (e.g., dataset_generator.py ??)
from src.model.llm_response import LLMRequest, Message, MessageRole
from src.llm.llm_service import LLMService

# 1. Define the instructions (System Message)
system_prompt = "Hey!"
# 2. Create the Message objects
messages = [
    Message(role=MessageRole.SYSTEM, content=system_prompt),
    Message(role=MessageRole.USER, content=doc_content)
]

# 3. Create the LLMRequest object
request_payload = LLMRequest(messages=messages)

# 4. Call the LLM service (the method doesn't exist yet, but we can imagine it)
llm_response = llm_service.generate_queries(request=request_payload) 
# This internal method will call self.chat_model.invoke(...)

# 5. Process the LLMResponse
generated_queries_text = llm_response.content
list_of_queries = generated_queries_text.strip().split('\n')

# Optional: Log token usage for cost control
print(f"Token usage for query generation: {llm_response.usage}")
"""