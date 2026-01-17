"""
Project data models

Implements Requirements 12.1, 18.1, 18.2, 18.3
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic"""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class ProjectMetadata(BaseModel):
    """Project statistics metadata"""
    total_specs: int = 0
    total_rtl_files: int = 0
    total_assertions: int = 0


class ProjectBase(BaseModel):
    """Base project model for creation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)


class ProjectCreate(ProjectBase):
    """Model for creating a new project"""
    pass


class ProjectUpdate(BaseModel):
    """Model for updating a project"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = Field(None, pattern="^(draft|processing|completed|failed)$")


class Project(ProjectBase):
    """Complete project model with all fields"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    status: str = "draft"
    metadata: ProjectMetadata = Field(default_factory=ProjectMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "name": "AXI Protocol Verification",
                "description": "Generate assertions for AXI4 slave interface",
                "user_id": "user123",
                "status": "draft",
                "metadata": {
                    "total_specs": 2,
                    "total_rtl_files": 3,
                    "total_assertions": 15
                }
            }
        }


class ProjectInDB(Project):
    """Project model as stored in database"""
    pass


class ProjectResponse(BaseModel):
    """Project response model for API"""
    id: str
    name: str
    description: Optional[str]
    user_id: str
    status: str
    metadata: ProjectMetadata
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "name": "AXI Protocol Verification",
                "description": "Generate assertions for AXI4 slave interface",
                "user_id": "user123",
                "status": "draft",
                "metadata": {
                    "total_specs": 2,
                    "total_rtl_files": 3,
                    "total_assertions": 15
                },
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T14:20:00Z"
            }
        }
