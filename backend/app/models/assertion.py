"""
Assertion data models

Implements Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 7.4, 7.5, 8.1, 8.2, 8.3, 18.3
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from app.models.project import PyObjectId


class Traceability(BaseModel):
    """Traceability information linking assertion to requirements and RTL"""
    spec_reference: str
    requirement_text: str
    rtl_signals: List[str] = Field(default_factory=list)
    rtl_module: str
    line_numbers: List[int] = Field(default_factory=list)


class ValidationResult(BaseModel):
    """Assertion validation results"""
    syntax_valid: bool
    vacuity_check: Optional[str] = None
    over_constraint_check: Optional[str] = None
    quality_score: float = Field(..., ge=0.0, le=1.0)
    suggestions: List[str] = Field(default_factory=list)


class UserFeedback(BaseModel):
    """User feedback on assertion"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    modified: bool = False
    comments: Optional[str] = None
    feedback_at: Optional[datetime] = None


class AssertionBase(BaseModel):
    """Base assertion model"""
    assertion_code: str
    assertion_type: str = Field(..., pattern="^(immediate|concurrent|property|sequence)$")
    category: str


class AssertionCreate(AssertionBase):
    """Model for creating an assertion"""
    project_id: str
    requirement_id: str
    rtl_module: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    traceability: Traceability


class AssertionUpdate(BaseModel):
    """Model for updating an assertion"""
    assertion_code: Optional[str] = None
    user_feedback: Optional[UserFeedback] = None


class Assertion(AssertionBase):
    """Complete assertion model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    project_id: PyObjectId
    requirement_id: str
    rtl_module: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    traceability: Traceability
    validation: Optional[ValidationResult] = None
    user_feedback: UserFeedback = Field(default_factory=UserFeedback)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    agent_version: str = "1.0.0"

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "assertion_code": "assert property (@(posedge clk) AWVALID |-> ##[1:5] AWREADY);",
                "assertion_type": "concurrent",
                "category": "timing",
                "project_id": "507f1f77bcf86cd799439011",
                "requirement_id": "REQ-001",
                "rtl_module": "axi_slave",
                "confidence_score": 0.92,
                "explanation": "Verifies that AWREADY responds within 5 cycles when AWVALID is asserted",
                "traceability": {
                    "spec_reference": "REQ-001",
                    "requirement_text": "When AWVALID is high, AWREADY must be asserted within 5 cycles",
                    "rtl_signals": ["AWVALID", "AWREADY", "clk"],
                    "rtl_module": "axi_slave",
                    "line_numbers": [45, 67]
                },
                "validation": {
                    "syntax_valid": True,
                    "vacuity_check": "passed",
                    "quality_score": 0.88
                }
            }
        }


class AssertionInDB(Assertion):
    """Assertion model as stored in database"""
    pass


class AssertionResponse(BaseModel):
    """Assertion response model for API"""
    id: str
    project_id: str
    requirement_id: str
    assertion_code: str
    assertion_type: str
    category: str
    rtl_module: str
    confidence_score: float
    explanation: str
    traceability: Traceability
    validation: Optional[ValidationResult]
    user_feedback: UserFeedback
    generated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439014",
                "project_id": "507f1f77bcf86cd799439011",
                "requirement_id": "REQ-001",
                "assertion_code": "assert property (@(posedge clk) AWVALID |-> ##[1:5] AWREADY);",
                "assertion_type": "concurrent",
                "category": "timing",
                "rtl_module": "axi_slave",
                "confidence_score": 0.92,
                "explanation": "Verifies that AWREADY responds within 5 cycles when AWVALID is asserted",
                "traceability": {
                    "spec_reference": "REQ-001",
                    "requirement_text": "When AWVALID is high, AWREADY must be asserted within 5 cycles",
                    "rtl_signals": ["AWVALID", "AWREADY", "clk"],
                    "rtl_module": "axi_slave",
                    "line_numbers": [45, 67]
                },
                "validation": {
                    "syntax_valid": True,
                    "vacuity_check": "passed",
                    "quality_score": 0.88
                },
                "user_feedback": {
                    "rating": 5,
                    "modified": False,
                    "comments": "Perfect assertion!"
                },
                "generated_at": "2024-01-15T11:00:00Z"
            }
        }
