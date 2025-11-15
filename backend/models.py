from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Request Models
class TopicCreate(BaseModel):
    question: str = Field(..., description="The debate question")
    created_by: str = Field(..., description="Username of the creator")

class ArgumentCreate(BaseModel):
    side: str = Field(..., description="Either 'pro' or 'con'")
    title: str = Field(..., description="Title of the argument")
    content: str = Field(..., description="Content of the argument")
    sources: Optional[str] = Field(None, description="Sources for the argument")
    author: str = Field(..., description="Author of the argument")

# Response Models
class TopicResponse(BaseModel):
    topic_id: int
    question: str
    created_by: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class TopicListItem(BaseModel):
    id: int
    question: str
    pro_count: int
    con_count: int
    created_by: Optional[str] = None
    created_at: Optional[str] = None

    class Config:
        from_attributes = True

class ArgumentResponse(BaseModel):
    id: int
    topic_id: int
    side: str
    title: str
    content: str
    sources: Optional[str] = None
    author: str
    created_at: str

    class Config:
        from_attributes = True

class TopicDetailResponse(BaseModel):
    id: int
    question: str
    pro_arguments: List[ArgumentResponse]
    con_arguments: List[ArgumentResponse]
    overall_summary: Optional[str] = None
    consensus_view: Optional[str] = None
    timeline_view: Optional[List[dict]] = None

    class Config:
        from_attributes = True

class ArgumentCreateResponse(BaseModel):
    argument_id: int

class SummaryResponse(BaseModel):
    overall_summary: str
    consensus_view: str
    timeline_view: List[dict]

