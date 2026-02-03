"""
Project management and file upload routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..database import Database
from ..utils.auth import get_current_user
from ..utils.authorization import verify_project_ownership
from ..config import settings
import os
import aiofiles
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    user_id: str
    status: str
    created_at: Optional[datetime] = None
    metadata: dict


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user_id: str = Depends(get_current_user)
):
    """
    Create a new project
    
    Args:
        project_data: Project creation data
        current_user_id: Current authenticated user ID
        
    Returns:
        Created project
    """
    db = Database.get_db()
    
    # Create project document
    project_doc = {
        "name": project_data.name,
        "description": project_data.description,
        "user_id": current_user_id,
        "status": "draft",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "metadata": {
            "total_specs": 0,
            "total_rtl_files": 0,
            "total_assertions": 0
        }
    }
    
    result = await db.projects.insert_one(project_doc)
    project_doc["_id"] = result.inserted_id
    
    return ProjectResponse(
        id=str(project_doc["_id"]),
        name=project_doc["name"],
        description=project_doc["description"],
        user_id=project_doc["user_id"],
        status=project_doc["status"],
        created_at=project_doc["created_at"],
        metadata=project_doc["metadata"]
    )


@router.get("", response_model=List[ProjectResponse])
async def list_projects(current_user_id: str = Depends(get_current_user)):
    """
    List all projects for the current user
    
    Args:
        current_user_id: Current authenticated user ID
        
    Returns:
        List of projects
    """
    db = Database.get_db()
    
    projects = await db.projects.find({"user_id": current_user_id}).to_list(length=100)
    
    return [
        ProjectResponse(
            id=str(p["_id"]),
            name=p["name"],
            description=p.get("description", ""),
            user_id=p["user_id"],
            status=p["status"],
            created_at=p.get("created_at"),
            metadata=p.get("metadata", {})
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get a specific project
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Project details
    """
    project = await verify_project_ownership(project_id, current_user_id)
    
    return ProjectResponse(
        id=str(project["_id"]),
        name=project["name"],
        description=project.get("description", ""),
        user_id=project["user_id"],
        status=project["status"],
        created_at=project.get("created_at"),
        metadata=project.get("metadata", {})
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Delete a project and all associated data
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
    """
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Delete all associated data
    await db.specifications.delete_many({"project_id": ObjectId(project_id)})
    await db.rtl_designs.delete_many({"project_id": ObjectId(project_id)})
    await db.assertions.delete_many({"project_id": ObjectId(project_id)})
    
    # Delete project
    await db.projects.delete_one({"_id": ObjectId(project_id)})


# File upload validation
ALLOWED_SPEC_EXTENSIONS = {".md", ".txt", ".pdf", ".doc", ".docx"}
ALLOWED_RTL_EXTENSIONS = {".sv", ".v"}
MAX_FILE_SIZE = settings.max_file_size_mb * 1024 * 1024  # Convert MB to bytes


def validate_file_type(filename: str, allowed_extensions: set) -> bool:
    """Validate file extension"""
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions


def validate_file_size(file_size: int) -> bool:
    """Validate file size"""
    return file_size <= MAX_FILE_SIZE


@router.post("/{project_id}/upload-spec")
async def upload_specification(
    project_id: str,
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user)
):
    """
    Upload a specification file
    
    Args:
        project_id: Project ID
        file: Uploaded file
        current_user_id: Current authenticated user ID
        
    Returns:
        Uploaded specification details
        
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.6, 20.3
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    
    # Validate file type
    if not validate_file_type(file.filename, ALLOWED_SPEC_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_SPEC_EXTENSIONS)}"
        )
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if not validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.upload_dir, project_id, "specifications")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Determine file type
    ext = os.path.splitext(file.filename)[1].lower()
    file_type_map = {
        ".md": "md",
        ".txt": "txt",
        ".pdf": "pdf",
        ".doc": "docx",
        ".docx": "docx"
    }
    file_type = file_type_map.get(ext, "txt")
    
    # Extract text content for txt and md files
    raw_text = None
    if file_type in ["txt", "md"]:
        raw_text = content.decode('utf-8', errors='ignore')
    
    # Create specification document
    db = Database.get_db()
    spec_doc = {
        "project_id": ObjectId(project_id),
        "filename": file.filename,
        "file_type": file_type,
        "file_path": file_path,
        "file_size": file_size,
        "raw_text": raw_text,
        "parsed_requirements": [],
        "uploaded_at": datetime.utcnow(),
        "processed": False
    }
    
    result = await db.specifications.insert_one(spec_doc)
    
    # Update project metadata
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$inc": {"metadata.total_specs": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "id": str(result.inserted_id),
        "filename": file.filename,
        "file_type": file_type,
        "file_size": file_size,
        "uploaded_at": spec_doc["uploaded_at"],
        "message": "Specification uploaded successfully"
    }



@router.post("/{project_id}/upload-rtl")
async def upload_rtl(
    project_id: str,
    file: UploadFile = File(...),
    current_user_id: str = Depends(get_current_user)
):
    """
    Upload an RTL design file
    
    Args:
        project_id: Project ID
        file: Uploaded file
        current_user_id: Current authenticated user ID
        
    Returns:
        Uploaded RTL details
        
    Validates: Requirements 2.1, 20.3
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    
    # Validate file type
    if not validate_file_type(file.filename, ALLOWED_RTL_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_RTL_EXTENSIONS)}"
        )
    
    # Read file content to check size
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if not validate_file_size(file_size):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(settings.upload_dir, project_id, "rtl")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Decode source code
    source_code = content.decode('utf-8', errors='ignore')
    
    # Create RTL design document
    db = Database.get_db()
    rtl_doc = {
        "project_id": ObjectId(project_id),
        "filename": file.filename,
        "file_path": file_path,
        "file_size": file_size,
        "source_code": source_code,
        "parsed_ast": None,
        "analysis": {
            "modules": [],
            "dependencies": {},
            "complexity_score": 0.0
        },
        "uploaded_at": datetime.utcnow(),
        "processed": False
    }
    
    result = await db.rtl_designs.insert_one(rtl_doc)
    
    # Update project metadata
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$inc": {"metadata.total_rtl_files": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "id": str(result.inserted_id),
        "filename": file.filename,
        "file_size": file_size,
        "uploaded_at": rtl_doc["uploaded_at"],
        "message": "RTL file uploaded successfully"
    }


@router.post("/{project_id}/generate-assertions")
async def generate_assertions(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Generate assertions for a project
    
    Triggers the assertion generation pipeline using uploaded specification
    and RTL files. This endpoint orchestrates the entire generation process.
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Generation job status and initial results
        
    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 2.1, 3.1, 4.1
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Check if project has uploaded files
    specs = await db.specifications.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    rtl_designs = await db.rtl_designs.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    if not specs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No specification files uploaded. Please upload at least one specification file."
        )
    
    if not rtl_designs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No RTL files uploaded. Please upload at least one RTL file."
        )
    
    # Update project status to processing
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"status": "processing", "updated_at": datetime.utcnow()}}
    )
    
    try:
        # Import orchestrator and utilities
        from ..agents.orchestrator import Orchestrator
        from ..utils.text_extraction import extract_text
        
        # Load specification file contents
        spec_texts = []
        for spec in specs:
            if spec.get("raw_text"):
                # Use pre-extracted text for txt/md files
                spec_texts.append(spec["raw_text"])
            elif spec.get("file_path"):
                # Extract text from PDF/DOCX files
                try:
                    text, success = extract_text(spec["file_path"], spec.get("file_type", "txt"))
                    if success and text:
                        spec_texts.append(text)
                    else:
                        logger.warning(f"Failed to extract text from {spec['filename']}")
                except Exception as e:
                    logger.error(f"Failed to extract text from {spec['filename']}: {str(e)}")
        
        if not spec_texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from specification files. The uploaded PDF appears to be image-based or empty. Please upload a text-based specification file (TXT, MD, or DOCX with selectable text) or a PDF with extractable text."
            )
        
        # Combine all specification texts
        combined_spec_text = "\n\n".join(spec_texts)
        
        # Load RTL file contents
        rtl_texts = []
        for rtl in rtl_designs:
            if rtl.get("raw_code"):
                rtl_texts.append(rtl["raw_code"])
            elif rtl.get("file_path"):
                try:
                    async with aiofiles.open(rtl["file_path"], 'r') as f:
                        code = await f.read()
                        rtl_texts.append(code)
                except Exception as e:
                    logger.error(f"Failed to read RTL file {rtl['filename']}: {str(e)}")
        
        if not rtl_texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not read RTL files"
            )
        
        # Combine all RTL code
        combined_rtl_code = "\n\n".join(rtl_texts)
        
        # Prepare initial data for pipeline
        initial_data = {
            "specification_text": combined_spec_text,
            "rtl_code": combined_rtl_code,
            "specification_id": str(specs[0]["_id"]) if specs else None,
            "rtl_design_id": str(rtl_designs[0]["_id"]) if rtl_designs else None
        }
        
        # Create orchestrator instance with required dependencies
        # The orchestrator will create the appropriate LLM client via factory
        orchestrator = Orchestrator(db=db)
        
        # Execute generation pipeline with initial data
        result = await orchestrator.execute_pipeline(project_id, initial_data=initial_data)
        
        if not result.success:
            # Update project status to error
            await db.projects.update_one(
                {"_id": ObjectId(project_id)},
                {"$set": {"status": "error", "updated_at": datetime.utcnow()}}
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Assertion generation failed: {result.error}"
            )
        
        # Extract generated assertions from result
        assertions_data = result.final_data.get("assertions", [])
        
        # Store assertions in database
        stored_assertions = []
        for assertion_data in assertions_data:
            assertion_doc = {
                "project_id": ObjectId(project_id),
                "code": assertion_data.get("assertion_code", ""),
                "type": assertion_data.get("assertion_type", "unknown"),
                "category": assertion_data.get("category", "unknown"),
                "confidence_score": assertion_data.get("confidence_score", 0.0),
                "explanation": assertion_data.get("explanation", ""),
                "traceability": assertion_data.get("traceability", {}),
                "generated_at": datetime.utcnow(),
                "modified": False
            }
            
            insert_result = await db.assertions.insert_one(assertion_doc)
            assertion_doc["_id"] = insert_result.inserted_id
            stored_assertions.append(assertion_doc)
        
        # Update project metadata
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "status": "completed",
                    "updated_at": datetime.utcnow(),
                    "metadata.total_assertions": len(stored_assertions)
                }
            }
        )
        
        # Convert to serializable format
        assertions_response = []
        for assertion in stored_assertions:
            assertions_response.append({
                "id": str(assertion["_id"]),
                "code": assertion["code"],
                "type": assertion["type"],
                "category": assertion["category"],
                "confidence_score": assertion["confidence_score"],
                "explanation": assertion["explanation"],
                "traceability": assertion["traceability"],
                "generated_at": assertion["generated_at"]
            })
        
        return {
            "success": True,
            "project_id": project_id,
            "assertions_generated": len(assertions_response),
            "assertions": assertions_response,
            "message": f"Successfully generated {len(assertions_response)} assertions"
        }
        
    except HTTPException:
        # Re-raise HTTPException without modification (preserves status code)
        raise
    except Exception as e:
        # Update project status to error
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": "error", "updated_at": datetime.utcnow()}}
        )
        
        # Log error
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error generating assertions: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assertion generation failed: {str(e)}"
        )


@router.get("/{project_id}/traceability-matrix")
async def get_traceability_matrix(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Generate traceability matrix for a project
    
    Shows mapping between requirements and assertions with coverage statistics.
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Traceability matrix with coverage statistics
        
    Validates: Requirements 8.5
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Load requirements from specifications
    specs = await db.specifications.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    requirements = []
    for spec in specs:
        parsed_reqs = spec.get("parsed_requirements", [])
        requirements.extend(parsed_reqs)
    
    # Load assertions
    assertions = await db.assertions.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    # Convert ObjectId to string for JSON serialization
    assertions_serializable = []
    for assertion in assertions:
        assertion_dict = dict(assertion)
        assertion_dict["id"] = str(assertion_dict.pop("_id"))
        assertion_dict["project_id"] = str(assertion_dict["project_id"])
        assertions_serializable.append(assertion_dict)
    
    # Build traceability matrix
    from ..utils.traceability import build_traceability_matrix
    matrix = build_traceability_matrix(requirements, assertions_serializable)
    
    return {
        "project_id": project_id,
        "project_name": project["name"],
        "matrix": matrix,
        "generated_at": datetime.utcnow()
    }


@router.get("/{project_id}/traceability-matrix/uncovered")
async def get_uncovered_requirements(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get list of requirements without assertions
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        List of uncovered requirements
        
    Validates: Requirements 8.5
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Load requirements
    specs = await db.specifications.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    requirements = []
    for spec in specs:
        parsed_reqs = spec.get("parsed_requirements", [])
        requirements.extend(parsed_reqs)
    
    # Load assertions
    assertions = await db.assertions.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    # Convert to serializable format
    assertions_serializable = []
    for assertion in assertions:
        assertion_dict = dict(assertion)
        assertion_dict["id"] = str(assertion_dict.pop("_id"))
        assertions_serializable.append(assertion_dict)
    
    # Get uncovered requirements
    from ..utils.traceability import traceability_extractor
    uncovered = traceability_extractor.get_uncovered_requirements(
        requirements, assertions_serializable
    )
    
    return {
        "project_id": project_id,
        "uncovered_requirements": uncovered,
        "count": len(uncovered)
    }


@router.get("/{project_id}/traceability-matrix/by-category")
async def get_coverage_by_category(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get coverage statistics by requirement category
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Coverage statistics grouped by category
        
    Validates: Requirements 8.5
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Load requirements
    specs = await db.specifications.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    requirements = []
    for spec in specs:
        parsed_reqs = spec.get("parsed_requirements", [])
        requirements.extend(parsed_reqs)
    
    # Load assertions
    assertions = await db.assertions.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    # Convert to serializable format
    assertions_serializable = []
    for assertion in assertions:
        assertion_dict = dict(assertion)
        assertion_dict["id"] = str(assertion_dict.pop("_id"))
        assertions_serializable.append(assertion_dict)
    
    # Get coverage by category
    from ..utils.traceability import traceability_extractor
    coverage = traceability_extractor.get_assertion_coverage_by_category(
        requirements, assertions_serializable
    )
    
    return {
        "project_id": project_id,
        "coverage_by_category": coverage
    }


@router.get("/{project_id}/rtl-designs")
async def get_rtl_designs(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all RTL designs for a project
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        List of RTL designs with analysis data
    """
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Load RTL designs
    rtl_designs = await db.rtl_designs.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    # Convert to serializable format
    designs_serializable = []
    for design in rtl_designs:
        design_dict = dict(design)
        design_dict["id"] = str(design_dict.pop("_id"))
        design_dict["project_id"] = str(design_dict["project_id"])
        # Remove large source_code field for list view
        if "source_code" in design_dict:
            design_dict["source_code_length"] = len(design_dict["source_code"])
            del design_dict["source_code"]
        designs_serializable.append(design_dict)
    
    return designs_serializable


@router.get("/{project_id}/export")
async def export_project_assertions(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Export all assertions for a project as a SystemVerilog file
    
    Generates a .sv file containing all assertions with comments,
    traceability information, and integration instructions.
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        SystemVerilog file content with all assertions
        
    Validates: Requirements 15.1, 15.2, 15.5
    """
    from fastapi.responses import Response
    
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Load all assertions for the project
    assertions = await db.assertions.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    if not assertions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assertions found for this project"
        )
    
    # Generate SVA file content
    sva_content = _generate_sva_file(project, assertions)
    
    # Return as downloadable file
    filename = f"{project['name'].replace(' ', '_')}_assertions.sv"
    
    return Response(
        content=sva_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


def _generate_sva_file(project: dict, assertions: list) -> str:
    """
    Generate SystemVerilog file content with all assertions
    
    Args:
        project: Project document
        assertions: List of assertion documents
        
    Returns:
        Complete SVA file content as string
    """
    lines = []
    
    # File header
    lines.append("//=" * 40)
    lines.append(f"// SystemVerilog Assertions for Project: {project['name']}")
    lines.append(f"// Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"// Total Assertions: {len(assertions)}")
    lines.append("//=" * 40)
    lines.append("")
    lines.append("// This file contains automatically generated SystemVerilog Assertions (SVA)")
    lines.append("// created by the SVA-Chatbot system.")
    lines.append("//")
    lines.append("// INTEGRATION INSTRUCTIONS:")
    lines.append("// 1. Review each assertion for correctness and applicability")
    lines.append("// 2. Copy relevant assertions into your RTL module(s)")
    lines.append("// 3. Ensure clock and reset signals match your design")
    lines.append("// 4. Compile with a SystemVerilog-compatible simulator")
    lines.append("// 5. Enable assertion checking during simulation")
    lines.append("//")
    lines.append("// VERIFICATION TOOLS:")
    lines.append("// - Synopsys VCS: Use +assert option")
    lines.append("// - Cadence Xcelium: Use -assert option")
    lines.append("// - Mentor Questa: Use -assertdebug option")
    lines.append("// - Verilator: Use --assert option")
    lines.append("//=" * 40)
    lines.append("")
    lines.append("")
    
    # Group assertions by module
    assertions_by_module = {}
    for assertion in assertions:
        module = assertion.get("traceability", {}).get("rtl_module", "unknown_module")
        if module not in assertions_by_module:
            assertions_by_module[module] = []
        assertions_by_module[module].append(assertion)
    
    # Generate assertions for each module
    for module_name, module_assertions in sorted(assertions_by_module.items()):
        lines.append("//=" * 40)
        lines.append(f"// Module: {module_name}")
        lines.append(f"// Assertions: {len(module_assertions)}")
        lines.append("//=" * 40)
        lines.append("")
        
        # Sort assertions by category
        module_assertions.sort(key=lambda a: a.get("category", "unknown"))
        
        for idx, assertion in enumerate(module_assertions, 1):
            # Assertion header
            lines.append(f"// Assertion {idx}: {assertion.get('category', 'Unknown Category')}")
            lines.append("//")
            
            # Traceability information
            traceability = assertion.get("traceability", {})
            requirement_text = traceability.get("requirement_text", "No requirement text available")
            lines.append(f"// Requirement: {requirement_text}")
            lines.append("//")
            
            # RTL signals
            rtl_signals = traceability.get("rtl_signals", [])
            if rtl_signals:
                lines.append(f"// RTL Signals: {', '.join(rtl_signals)}")
            
            # Line numbers
            line_numbers = traceability.get("line_numbers", [])
            if line_numbers:
                lines.append(f"// RTL Lines: {', '.join(map(str, line_numbers))}")
            
            # Quality metrics
            confidence = assertion.get("confidence_score", 0.0)
            quality = assertion.get("quality_score", 0.0)
            lines.append(f"// Confidence: {confidence:.2f} | Quality: {quality:.2f}")
            lines.append("//")
            
            # Assertion type
            assertion_type = assertion.get("type", "unknown")
            lines.append(f"// Type: {assertion_type}")
            
            # Modification status
            if assertion.get("modified", False):
                lines.append("// Status: MODIFIED BY USER")
                modified_at = assertion.get("modified_at")
                if modified_at:
                    lines.append(f"// Modified: {modified_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            
            # Explanation
            explanation = assertion.get("explanation", "")
            if explanation:
                lines.append("//")
                lines.append(f"// Explanation: {explanation}")
            
            lines.append("//")
            lines.append("//" + "-" * 78)
            lines.append("")
            
            # Assertion code
            code = assertion.get("code", "")
            lines.append(code)
            lines.append("")
            lines.append("")
    
    # Footer
    lines.append("//=" * 40)
    lines.append("// End of Generated Assertions")
    lines.append("//=" * 40)
    lines.append("")
    lines.append("// NOTES:")
    lines.append("// - All assertions include traceability to requirements")
    lines.append("// - Confidence scores indicate generation certainty (0.0-1.0)")
    lines.append("// - Quality scores indicate assertion quality (0.0-1.0)")
    lines.append("// - Modified assertions have been edited by users")
    lines.append("// - Review all assertions before integration")
    lines.append("//")
    lines.append("// For questions or issues, refer to project documentation.")
    lines.append("")
    
    return "\n".join(lines)


@router.get("/{project_id}/export/traceability-report")
async def export_traceability_report(
    project_id: str,
    format: str = "markdown",
    current_user_id: str = Depends(get_current_user)
):
    """
    Export traceability report for a project
    
    Generates a comprehensive report showing requirement-to-assertion mappings,
    coverage statistics, and quality metrics.
    
    Args:
        project_id: Project ID
        format: Report format ('markdown' or 'pdf')
        current_user_id: Current authenticated user ID
        
    Returns:
        Traceability report in requested format
        
    Validates: Requirements 15.3
    """
    from fastapi.responses import Response
    
    # Verify project ownership
    project = await verify_project_ownership(project_id, current_user_id)
    db = Database.get_db()
    
    # Load requirements from specifications
    specs = await db.specifications.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    requirements = []
    for spec in specs:
        parsed_reqs = spec.get("parsed_requirements", [])
        requirements.extend(parsed_reqs)
    
    # Load assertions
    assertions = await db.assertions.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    # Convert to serializable format
    assertions_serializable = []
    for assertion in assertions:
        assertion_dict = dict(assertion)
        assertion_dict["id"] = str(assertion_dict.pop("_id"))
        assertion_dict["project_id"] = str(assertion_dict["project_id"])
        assertions_serializable.append(assertion_dict)
    
    # Build traceability matrix
    from ..utils.traceability import build_traceability_matrix, traceability_extractor
    matrix = build_traceability_matrix(requirements, assertions_serializable)
    
    # Generate report based on format
    if format.lower() == "markdown":
        report_content = _generate_markdown_report(
            project, requirements, assertions_serializable, matrix
        )
        media_type = "text/markdown"
        extension = "md"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}. Supported formats: markdown"
        )
    
    # Return as downloadable file
    filename = f"{project['name'].replace(' ', '_')}_traceability_report.{extension}"
    
    return Response(
        content=report_content,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


def _generate_markdown_report(
    project: dict,
    requirements: list,
    assertions: list,
    matrix: dict
) -> str:
    """
    Generate Markdown traceability report
    
    Args:
        project: Project document
        requirements: List of requirements
        assertions: List of assertions
        matrix: Traceability matrix data
        
    Returns:
        Markdown report content as string
    """
    lines = []
    
    # Report header
    lines.append(f"# Traceability Report: {project['name']}")
    lines.append("")
    lines.append(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    lines.append(f"**Project Description:** {project.get('description', 'N/A')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    
    total_requirements = len(requirements)
    total_assertions = len(assertions)
    
    # Calculate coverage
    covered_requirements = sum(1 for req in requirements if any(
        a.get("requirement_id") == req.get("requirement_id") for a in assertions
    ))
    coverage_percentage = (covered_requirements / total_requirements * 100) if total_requirements > 0 else 0
    
    lines.append(f"- **Total Requirements:** {total_requirements}")
    lines.append(f"- **Total Assertions:** {total_assertions}")
    lines.append(f"- **Covered Requirements:** {covered_requirements}")
    lines.append(f"- **Coverage:** {coverage_percentage:.1f}%")
    lines.append("")
    
    # Calculate average scores
    if assertions:
        avg_confidence = sum(a.get("confidence_score", 0) for a in assertions) / len(assertions)
        avg_quality = sum(a.get("quality_score", 0) for a in assertions if a.get("quality_score")) / len([a for a in assertions if a.get("quality_score")]) if any(a.get("quality_score") for a in assertions) else 0
        lines.append(f"- **Average Confidence Score:** {avg_confidence:.2f}")
        lines.append(f"- **Average Quality Score:** {avg_quality:.2f}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Coverage by Category
    lines.append("## Coverage by Category")
    lines.append("")
    
    # Group requirements by category
    requirements_by_category = {}
    for req in requirements:
        category = req.get("category", "unknown")
        if category not in requirements_by_category:
            requirements_by_category[category] = []
        requirements_by_category[category].append(req)
    
    # Calculate coverage per category
    lines.append("| Category | Total Requirements | Covered | Coverage % |")
    lines.append("|----------|-------------------|---------|------------|")
    
    for category in sorted(requirements_by_category.keys()):
        cat_reqs = requirements_by_category[category]
        cat_covered = sum(1 for req in cat_reqs if any(
            a.get("requirement_id") == req.get("requirement_id") for a in assertions
        ))
        cat_coverage = (cat_covered / len(cat_reqs) * 100) if cat_reqs else 0
        lines.append(f"| {category.capitalize()} | {len(cat_reqs)} | {cat_covered} | {cat_coverage:.1f}% |")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Requirement-Assertion Matrix
    lines.append("## Requirement-Assertion Matrix")
    lines.append("")
    lines.append("This section shows the mapping between requirements and assertions.")
    lines.append("")
    
    for idx, req in enumerate(requirements, 1):
        req_id = req.get("requirement_id", f"REQ-{idx}")
        req_text = req.get("text", "No text available")
        req_category = req.get("category", "unknown")
        
        lines.append(f"### {req_id}: {req_category.capitalize()}")
        lines.append("")
        lines.append(f"**Requirement:** {req_text}")
        lines.append("")
        
        # Find assertions for this requirement
        req_assertions = [a for a in assertions if a.get("requirement_id") == req_id]
        
        if req_assertions:
            lines.append(f"**Assertions ({len(req_assertions)}):**")
            lines.append("")
            
            for assertion in req_assertions:
                assertion_id = assertion.get("id", "unknown")
                assertion_type = assertion.get("type", "unknown")
                confidence = assertion.get("confidence_score", 0.0)
                quality = assertion.get("quality_score", 0.0)
                
                lines.append(f"- **{assertion_id}** ({assertion_type})")
                lines.append(f"  - Confidence: {confidence:.2f} | Quality: {quality:.2f}")
                
                # Show code snippet (first line only)
                code = assertion.get("code", "")
                first_line = code.split('\n')[0] if code else "No code"
                lines.append(f"  - Code: `{first_line}`")
                
                # Show RTL module
                rtl_module = assertion.get("traceability", {}).get("rtl_module", "unknown")
                lines.append(f"  - Module: {rtl_module}")
                lines.append("")
        else:
            lines.append("**Status:** ⚠️ NOT COVERED - No assertions found for this requirement")
            lines.append("")
        
        lines.append("---")
        lines.append("")
    
    # Uncovered Requirements
    uncovered = [req for req in requirements if not any(
        a.get("requirement_id") == req.get("requirement_id") for a in assertions
    )]
    
    if uncovered:
        lines.append("## Uncovered Requirements")
        lines.append("")
        lines.append(f"The following {len(uncovered)} requirement(s) do not have assertions:")
        lines.append("")
        
        for req in uncovered:
            req_id = req.get("requirement_id", "unknown")
            req_text = req.get("text", "No text")
            req_category = req.get("category", "unknown")
            lines.append(f"- **{req_id}** ({req_category}): {req_text}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Assertion Quality Summary
    lines.append("## Assertion Quality Summary")
    lines.append("")
    
    # Group assertions by quality score ranges
    high_quality = [a for a in assertions if a.get("quality_score", 0) >= 0.8]
    medium_quality = [a for a in assertions if 0.5 <= a.get("quality_score", 0) < 0.8]
    low_quality = [a for a in assertions if a.get("quality_score", 0) < 0.5]
    
    lines.append(f"- **High Quality (≥0.8):** {len(high_quality)} assertions")
    lines.append(f"- **Medium Quality (0.5-0.8):** {len(medium_quality)} assertions")
    lines.append(f"- **Low Quality (<0.5):** {len(low_quality)} assertions")
    lines.append("")
    
    if low_quality:
        lines.append("### Low Quality Assertions Requiring Review")
        lines.append("")
        for assertion in low_quality:
            assertion_id = assertion.get("id", "unknown")
            quality = assertion.get("quality_score", 0.0)
            req_id = assertion.get("requirement_id", "unknown")
            lines.append(f"- **{assertion_id}** (Quality: {quality:.2f}) - Requirement: {req_id}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Modified Assertions
    modified = [a for a in assertions if a.get("modified", False)]
    if modified:
        lines.append("## User-Modified Assertions")
        lines.append("")
        lines.append(f"The following {len(modified)} assertion(s) have been modified by users:")
        lines.append("")
        
        for assertion in modified:
            assertion_id = assertion.get("id", "unknown")
            modified_at = assertion.get("modified_at")
            req_id = assertion.get("requirement_id", "unknown")
            modified_date = modified_at.strftime('%Y-%m-%d %H:%M UTC') if modified_at else "unknown"
            lines.append(f"- **{assertion_id}** - Requirement: {req_id} - Modified: {modified_date}")
        
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Footer
    lines.append("## Notes")
    lines.append("")
    lines.append("- This report was automatically generated by the SVA-Chatbot system")
    lines.append("- Confidence scores indicate the system's certainty in the assertion (0.0-1.0)")
    lines.append("- Quality scores indicate assertion quality based on validation checks (0.0-1.0)")
    lines.append("- Review all uncovered requirements and low-quality assertions")
    lines.append("- Modified assertions should be reviewed for correctness")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*")
    lines.append("")
    
    return "\n".join(lines)

