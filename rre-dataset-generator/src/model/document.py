from typing import Dict, Any
from pydantic import BaseModel, Field

class Document(BaseModel):
    """
    Represents a document with a unique identifier, and fields.
    """
    id: str = Field(..., description="Unique identifier of the document.")
    fields: Dict[str, Any] = Field(..., description="Fields of the document.")
