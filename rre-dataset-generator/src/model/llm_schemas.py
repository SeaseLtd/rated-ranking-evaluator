"""
Pydantic models for the LLM service.
"""

import json
from typing import Dict
from pydantic import BaseModel, Field, field_validator

# Typing the LLM query service output 
class LLMQueryResponse(BaseModel):
    """Output model for LLM service responses."""
    content: str = Field(..., description="The generated response content")
    model: str = Field(..., description="The name of the model used for the response")
    usage: Dict[str, int] = Field(..., description="Token usage for the request")
    finish_reason: str = Field(
        ...,
        description="Reason why the generation stopped (e.g., 'stop', 'length', 'content_filter')"
    )

    @field_validator('content')
    def validate_content_is_json_array_of_strings(cls, v: str) -> str:
        """Validate that the content is a JSON array of strings."""
        try:
            parsed_content = json.loads(v)
            if not isinstance(parsed_content, list):
                raise ValueError("Content is not a JSON list")
            if not all(isinstance(item, str) for item in parsed_content):
                raise ValueError("All items in the list must be strings")
        except json.JSONDecodeError:
            raise ValueError("Content is not a valid JSON string")
        except ValueError as e:
            raise e
        return v


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