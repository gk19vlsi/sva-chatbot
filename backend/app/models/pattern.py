"""
Pattern Library data models

Implements Requirements 11.1, 11.2, 11.3, 11.4, 11.5
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.project import PyObjectId


class PatternBase(BaseModel):
    """Base pattern model"""
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    category: str
    protocol_type: Optional[str] = None


class PatternCreate(PatternBase):
    """Model for creating a pattern"""
    template: str
    parameters: List[str] = Field(default_factory=list)
    example_usage: str
    tags: List[str] = Field(default_factory=list)


class Pattern(PatternBase):
    """Complete pattern model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    template: str
    parameters: List[str] = Field(default_factory=list)
    example_usage: str
    tags: List[str] = Field(default_factory=list)
    embedding_vector: Optional[List[float]] = None
    usage_count: int = 0
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "Handshake Protocol",
                "description": "Basic request-acknowledge handshake pattern",
                "category": "protocol",
                "protocol_type": "handshake",
                "template": "assert property (@(posedge {clock}) {request} |-> ##[1:{max_delay}] {acknowledge});",
                "parameters": ["clock", "request", "acknowledge", "max_delay"],
                "example_usage": "assert property (@(posedge clk) req |-> ##[1:5] ack);",
                "tags": ["handshake", "protocol", "timing"],
                "usage_count": 42,
                "rating": 4.5
            }
        }


class PatternInDB(Pattern):
    """Pattern model as stored in database"""
    pass


class PatternResponse(BaseModel):
    """Pattern response model for API"""
    id: str
    name: str
    description: str
    category: str
    protocol_type: Optional[str]
    template: str
    parameters: List[str]
    example_usage: str
    tags: List[str]
    usage_count: int
    rating: float

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439015",
                "name": "Handshake Protocol",
                "description": "Basic request-acknowledge handshake pattern",
                "category": "protocol",
                "protocol_type": "handshake",
                "template": "assert property (@(posedge {clock}) {request} |-> ##[1:{max_delay}] {acknowledge});",
                "parameters": ["clock", "request", "acknowledge", "max_delay"],
                "example_usage": "assert property (@(posedge clk) req |-> ##[1:5] ack);",
                "tags": ["handshake", "protocol", "timing"],
                "usage_count": 42,
                "rating": 4.5
            }
        }


class PatternSearchQuery(BaseModel):
    """Model for pattern search queries"""
    query_text: str
    category: Optional[str] = None
    protocol_type: Optional[str] = None
    limit: int = Field(default=5, ge=1, le=20)


class PatternSearchResult(BaseModel):
    """Pattern search result with similarity score"""
    pattern: PatternResponse
    similarity_score: float = Field(..., ge=0.0, le=1.0)
