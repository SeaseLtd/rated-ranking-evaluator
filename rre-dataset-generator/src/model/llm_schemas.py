"""
Pydantic models for the LLM service.
"""

import json
from typing import List
from pydantic import BaseModel, Field, model_validator

# Typing the LLM query service output 
class LLMQueryResponse(BaseModel):
    """Output model for LLM service responses."""
    content: str = Field(..., description="The generated response content as JSON string")
    content_list: List[str] = Field(default_factory=list, description="Parsed content as a list of strings")

    # model: str = Field(..., description="The name of the model used for the response")
    # usage: Dict[str, int] = Field(..., description="Token usage for the request")
    # finish_reason: str = Field(
    #     ...,
    #     description="Reason why the generation stopped (e.g., 'stop', 'length', 'content_filter')"
    # )
    # content_json: Optional[str] = Field(None, description="The generated response content as a JSON string")

    # FIELD VALIDATOR doesn't allow to modify values, only make checks, so we use model_validator
    @model_validator(mode="after")
    def validate_and_parse_content(self) -> 'LLMQueryResponse':
        try:
            parsed = json.loads(self.content)
        except json.JSONDecodeError as e:
            raise ValueError(f"`content` is not valid JSON: {e}")

        if not isinstance(parsed, list):
            raise ValueError("`content` must be a JSON list")

        if not all(isinstance(item, str) for item in parsed):
            raise ValueError("All items in `content` must be strings")

        if any(item.strip() == "" for item in parsed):
            raise ValueError("Empty or whitespace-only strings are not allowed in `content`")

        self.content_list = parsed
        return self


## NOT NEEDED YET - WOULD BE USEFUL TO ADD PYDANTIC VALIDATION TO THE LLM Service 
# class LLMRequest(BaseModel):
#     """Input model for LLM service requests."""
#     messages: List[Message] = Field(
#         ...,
#         min_items=1,
#         description="List of messages in the conversation"
#     )

#     @field_validator('messages')
#     def validate_messages(cls, v: List[Message]) -> List[Message]:
#         if not v:
#             raise ValueError("At least one message is required")
#         if len(v) > 1 and v[0].role != MessageRole.SYSTEM:
#             raise ValueError("First message should be a system message when multiple messages are provided")
#         return v


## Could be useful
# class MessageRole(str, Enum):
#     SYSTEM = "system"
#     USER = "user"
#     ASSISTANT = "assistant"

# class Message(BaseModel):
#     """Represents a single message in the conversation."""
#     role: MessageRole = Field(..., description="The role of the message sender")
#     content: str = Field(..., min_length=1, description="The content of the message")
#     name: Optional[str] = Field(
#         None, 
#         min_length=1,
#         description="The name of the message sender (optional)"
#     )