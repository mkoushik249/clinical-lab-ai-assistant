from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

class LabTest(BaseModel):
    test_code: str
    test_name: str
    specimen_type: str
    turnaround_hours: int | None
    
class ChatMessage(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )
    
    role: Literal["user","assistant"]
    
    content: str = Field(
        min_length=1,
        max_length=4000,
    )
    
class ChatRequest(BaseModel):
    model_config = ConfigDict(
            str_strip_whitespace=True,
            extra="forbid",
        )
    
    question: str = Field(
        min_length=1,
        max_length=4000,
    )
    history: list[ChatMessage]= Field(
        default_factory=list,
        
    )
    
class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    