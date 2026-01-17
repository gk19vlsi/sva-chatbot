"""
RTL Design data models

Implements Requirements 2.1, 2.2, 4.1, 4.2, 4.3, 4.4, 4.5, 18.2
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from bson import ObjectId
from app.models.project import PyObjectId


class PortDefinition(BaseModel):
    """RTL port definition"""
    name: str
    direction: str = Field(..., pattern="^(input|output|inout)$")
    width: int = Field(default=1, ge=1)
    type: str = Field(default="wire")


class SignalDefinition(BaseModel):
    """RTL signal definition"""
    name: str
    type: str = Field(..., pattern="^(wire|reg|logic)$")
    width: int = Field(default=1, ge=1)


class StateMachineDefinition(BaseModel):
    """State machine definition"""
    name: str
    states: List[str]
    state_variable: str
    transitions: List[Dict[str, str]] = Field(default_factory=list)


class ModuleDefinition(BaseModel):
    """RTL module definition"""
    name: str
    ports: List[PortDefinition] = Field(default_factory=list)
    signals: List[SignalDefinition] = Field(default_factory=list)
    state_machines: List[StateMachineDefinition] = Field(default_factory=list)
    clocks: List[str] = Field(default_factory=list)
    resets: List[str] = Field(default_factory=list)


class RTLAnalysis(BaseModel):
    """RTL semantic analysis results"""
    modules: List[ModuleDefinition] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    complexity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    protocol_patterns: List[str] = Field(default_factory=list)


class RTLDesignBase(BaseModel):
    """Base RTL design model"""
    filename: str


class RTLDesignCreate(RTLDesignBase):
    """Model for creating RTL design"""
    project_id: str
    file_path: str
    source_code: str


class RTLDesign(RTLDesignBase):
    """Complete RTL design model"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    project_id: PyObjectId
    file_path: str
    source_code: str
    parsed_ast: Optional[Dict[str, Any]] = None
    analysis: Optional[RTLAnalysis] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processed: bool = False
    processing_error: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "filename": "axi_slave.sv",
                "project_id": "507f1f77bcf86cd799439011",
                "file_path": "/uploads/axi_slave.sv",
                "source_code": "module axi_slave(...);",
                "analysis": {
                    "modules": [
                        {
                            "name": "axi_slave",
                            "ports": [
                                {"name": "clk", "direction": "input", "width": 1, "type": "wire"},
                                {"name": "rst_n", "direction": "input", "width": 1, "type": "wire"}
                            ],
                            "clocks": ["clk"],
                            "resets": ["rst_n"]
                        }
                    ],
                    "protocol_patterns": ["AXI4"]
                },
                "processed": True
            }
        }


class RTLDesignInDB(RTLDesign):
    """RTL design model as stored in database"""
    pass


class RTLDesignResponse(BaseModel):
    """RTL design response model for API"""
    id: str
    project_id: str
    filename: str
    analysis: Optional[RTLAnalysis]
    uploaded_at: datetime
    processed: bool
    processing_error: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439013",
                "project_id": "507f1f77bcf86cd799439011",
                "filename": "axi_slave.sv",
                "analysis": {
                    "modules": [
                        {
                            "name": "axi_slave",
                            "ports": [
                                {"name": "clk", "direction": "input", "width": 1, "type": "wire"}
                            ],
                            "clocks": ["clk"],
                            "resets": ["rst_n"]
                        }
                    ],
                    "protocol_patterns": ["AXI4"]
                },
                "uploaded_at": "2024-01-15T10:35:00Z",
                "processed": True
            }
        }
