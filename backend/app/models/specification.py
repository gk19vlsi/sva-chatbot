"""
Specification data models

Implements Requirements 1.1, 1.2, 1.3, 1.4, 3.1, 3.2, 3.3, 3.4, 18.1
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.project import PyObjectId


class ParsedRequirement(BaseModel):
    """Individual requirement extracted from specification"""
    requirement_id: str
    text: str
    category: str = Field(..., pattern="^(timing|functional|protocol|safety|liveness)$")
    temporal_keywords: List[str] = Field(default_factory=list)
    entities: List[str] = Field(default_factory=list)
    priority: int = Field(default=1, ge=1, le=5)
    ambiguous: bool = False
    clarification_needed: Optional[str] = None


class SpecificationBase(BaseModel):
    """Base specification model"""
    filename: str
    file_type: str = Field(..., pattern="^(pdf|docx|md|txt)$")


class SpecificationCreate(SpecificationBase):
    """Model for creating a specification"""
    project_id: str
    file_path: str
    raw_text: Optional[str] = None


class Specification(SpecificationBase):
    """Complete specification model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    project_id: PyObjectId
    file_path: str
    raw_text: Optional[str] = None
    parsed_requirements: List[ParsedRequirement] = Field(default_factory=list)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processing_error: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "filename": "axi_protocol_spec.pdf",
                "file_type": "pdf",
                "project_id": "507f1f77bcf86cd799439011",
                "file_path": "/uploads/axi_protocol_spec.pdf",
                "parsed_requirements": [
                    {
                        "requirement_id": "REQ-001",
                        "text": "When AWVALID is high, AWREADY must be asserted within 5 cycles",
                        "category": "timing",
                        "temporal_keywords": ["within"],
                        "entities": ["AWVALID", "AWREADY"],
                        "priority": 1
                    }
                ],
                "processed": True
            }
        }


class SpecificationInDB(Specification):
    """Specification model as stored in database"""
    pass


class SpecificationResponse(BaseModel):
    """Specification response model for API"""
    id: str
    project_id: str
    filename: str
    file_type: str
    parsed_requirements: List[ParsedRequirement]
    uploaded_at: datetime
    processed: bool
    processing_error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439012",
                "project_id": "507f1f77bcf86cd799439011",
                "filename": "axi_protocol_spec.pdf",
                "file_type": "pdf",
                "parsed_requirements": [
                    {
                        "requirement_id": "REQ-001",
                        "text": "When AWVALID is high, AWREADY must be asserted within 5 cycles",
                        "category": "timing",
                        "temporal_keywords": ["within"],
                        "entities": ["AWVALID", "AWREADY"],
                        "priority": 1
                    }
                ],
                "uploaded_at": "2024-01-15T10:30:00Z",
                "processed": True
            }
        }
