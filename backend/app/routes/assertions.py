"""
Assertion management routes

Handles assertion CRUD operations including editing and modification tracking.

Validates: Requirements 10.1, 10.2
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

from ..database import Database
from ..utils.auth import get_current_user
from ..utils.authorization import verify_project_ownership
from ..utils.sva_validator import validate_sva_syntax

router = APIRouter(prefix="/api/assertions", tags=["assertions"])


class AssertionUpdate(BaseModel):
    code: str


class FeedbackSubmission(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, description="Optional feedback comment")


class AssertionResponse(BaseModel):
    id: str
    code: str
    type: str
    category: str
    confidence_score: float
    quality_score: Optional[float] = None
    modified: bool
    modified_at: Optional[datetime] = None
    original_code: Optional[str] = None


@router.put("/{assertion_id}", response_model=AssertionResponse)
async def update_assertion(
    assertion_id: str,
    update_data: AssertionUpdate,
    current_user_id: str = Depends(get_current_user)
):
    """
    Update an assertion's code
    
    Validates syntax before saving and marks assertion as modified.
    
    Args:
        assertion_id: Assertion ID
        update_data: Updated assertion code
        current_user_id: Current authenticated user ID
        
    Returns:
        Updated assertion
        
    Validates: Requirements 10.1, 10.2
    """
    db = Database.get_db()
    
    # Load assertion
    assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    if not assertion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assertion not found"
        )
    
    # Verify project ownership
    project_id = str(assertion["project_id"])
    await verify_project_ownership(project_id, current_user_id)
    
    # Validate syntax
    is_valid, error_message = validate_sva_syntax(update_data.code)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Syntax validation failed: {error_message}"
        )
    
    # Store original code if this is the first modification
    original_code = assertion.get("original_code")
    if not assertion.get("modified", False):
        original_code = assertion["code"]
    
    # Update assertion
    update_fields = {
        "code": update_data.code,
        "modified": True,
        "modified_at": datetime.utcnow(),
        "original_code": original_code
    }
    
    await db.assertions.update_one(
        {"_id": ObjectId(assertion_id)},
        {"$set": update_fields}
    )
    
    # Reload assertion
    updated_assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    
    return AssertionResponse(
        id=str(updated_assertion["_id"]),
        code=updated_assertion["code"],
        type=updated_assertion.get("type", "unknown"),
        category=updated_assertion.get("category", "unknown"),
        confidence_score=updated_assertion.get("confidence_score", 0.0),
        quality_score=updated_assertion.get("quality_score"),
        modified=updated_assertion.get("modified", False),
        modified_at=updated_assertion.get("modified_at"),
        original_code=updated_assertion.get("original_code")
    )


@router.get("/{assertion_id}", response_model=AssertionResponse)
async def get_assertion(
    assertion_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get a specific assertion
    
    Args:
        assertion_id: Assertion ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Assertion details
    """
    db = Database.get_db()
    
    # Load assertion
    assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    if not assertion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assertion not found"
        )
    
    # Verify project ownership
    project_id = str(assertion["project_id"])
    await verify_project_ownership(project_id, current_user_id)
    
    return AssertionResponse(
        id=str(assertion["_id"]),
        code=assertion["code"],
        type=assertion.get("type", "unknown"),
        category=assertion.get("category", "unknown"),
        confidence_score=assertion.get("confidence_score", 0.0),
        quality_score=assertion.get("quality_score"),
        modified=assertion.get("modified", False),
        modified_at=assertion.get("modified_at"),
        original_code=assertion.get("original_code")
    )


@router.get("/project/{project_id}")
async def get_project_assertions(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all assertions for a project
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        List of assertions for the project
    """
    db = Database.get_db()
    
    # Verify project ownership
    await verify_project_ownership(project_id, current_user_id)
    
    # Get all assertions for the project
    assertions = await db.assertions.find(
        {"project_id": ObjectId(project_id)}
    ).to_list(length=None)
    
    # Convert to response format
    assertions_list = []
    for assertion in assertions:
        assertions_list.append({
            "id": str(assertion["_id"]),
            "code": assertion.get("code", assertion.get("assertion_code", "")),
            "type": assertion.get("type", "unknown"),
            "category": assertion.get("category", "unknown"),
            "confidence_score": assertion.get("confidence_score", 0.0),
            "quality_score": assertion.get("quality_score"),
            "modified": assertion.get("modified", False),
            "modified_at": assertion.get("modified_at"),
            "original_code": assertion.get("original_code"),
            "traceability": assertion.get("traceability", {}),
            "generated_at": assertion.get("generated_at")
        })
    
    return {
        "project_id": project_id,
        "assertions": assertions_list,
        "total": len(assertions_list)
    }


@router.post("/{assertion_id}/revert")
async def revert_assertion(
    assertion_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Revert an assertion to its original code
    
    Args:
        assertion_id: Assertion ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Reverted assertion
    """
    db = Database.get_db()
    
    # Load assertion
    assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    if not assertion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assertion not found"
        )
    
    # Verify project ownership
    project_id = str(assertion["project_id"])
    await verify_project_ownership(project_id, current_user_id)
    
    # Check if assertion has been modified
    if not assertion.get("modified", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assertion has not been modified"
        )
    
    # Revert to original code
    original_code = assertion.get("original_code")
    if not original_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Original code not found"
        )
    
    await db.assertions.update_one(
        {"_id": ObjectId(assertion_id)},
        {
            "$set": {
                "code": original_code,
                "modified": False,
                "modified_at": None
            },
            "$unset": {"original_code": ""}
        }
    )
    
    # Reload assertion
    reverted_assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    
    return AssertionResponse(
        id=str(reverted_assertion["_id"]),
        code=reverted_assertion["code"],
        type=reverted_assertion.get("type", "unknown"),
        category=reverted_assertion.get("category", "unknown"),
        confidence_score=reverted_assertion.get("confidence_score", 0.0),
        quality_score=reverted_assertion.get("quality_score"),
        modified=False,
        modified_at=None,
        original_code=None
    )



@router.post("/{assertion_id}/feedback")
async def submit_feedback(
    assertion_id: str,
    feedback: FeedbackSubmission,
    current_user_id: str = Depends(get_current_user)
):
    """
    Submit feedback for an assertion
    
    Stores user feedback and updates pattern usage counts for positive ratings.
    
    Args:
        assertion_id: Assertion ID
        feedback: Feedback data (rating and optional comment)
        current_user_id: Current authenticated user ID
        
    Returns:
        Success message
        
    Validates: Requirements 10.3, 11.4
    """
    db = Database.get_db()
    
    # Load assertion
    assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    if not assertion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assertion not found"
        )
    
    # Verify project ownership
    project_id = str(assertion["project_id"])
    await verify_project_ownership(project_id, current_user_id)
    
    # Store feedback
    feedback_doc = {
        "assertion_id": ObjectId(assertion_id),
        "project_id": ObjectId(project_id),
        "user_id": current_user_id,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "submitted_at": datetime.utcnow()
    }
    
    await db.feedback.insert_one(feedback_doc)
    
    # Update assertion with feedback
    await db.assertions.update_one(
        {"_id": ObjectId(assertion_id)},
        {
            "$push": {
                "feedback": {
                    "rating": feedback.rating,
                    "comment": feedback.comment,
                    "submitted_at": datetime.utcnow()
                }
            }
        }
    )
    
    # Update pattern usage counts for positive feedback (rating >= 4)
    if feedback.rating >= 4:
        pattern_id = assertion.get("pattern_id")
        if pattern_id:
            # Increment usage count for the pattern
            await db.pattern_library.update_one(
                {"_id": ObjectId(pattern_id)},
                {
                    "$inc": {"usage_count": 1, "positive_feedback_count": 1},
                    "$set": {"last_used": datetime.utcnow()}
                }
            )
    
    # Update pattern usage counts for negative feedback (rating <= 2)
    if feedback.rating <= 2:
        pattern_id = assertion.get("pattern_id")
        if pattern_id:
            # Increment negative feedback count
            await db.pattern_library.update_one(
                {"_id": ObjectId(pattern_id)},
                {"$inc": {"negative_feedback_count": 1}}
            )
    
    return {
        "message": "Feedback submitted successfully",
        "feedback_id": str(feedback_doc["_id"]) if "_id" in feedback_doc else None
    }


@router.get("/{assertion_id}/feedback")
async def get_assertion_feedback(
    assertion_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get all feedback for an assertion
    
    Args:
        assertion_id: Assertion ID
        current_user_id: Current authenticated user ID
        
    Returns:
        List of feedback entries
    """
    db = Database.get_db()
    
    # Load assertion
    assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    if not assertion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assertion not found"
        )
    
    # Verify project ownership
    project_id = str(assertion["project_id"])
    await verify_project_ownership(project_id, current_user_id)
    
    # Get feedback
    feedback_list = await db.feedback.find(
        {"assertion_id": ObjectId(assertion_id)}
    ).to_list(length=None)
    
    # Convert to serializable format
    feedback_serializable = []
    for fb in feedback_list:
        feedback_serializable.append({
            "id": str(fb["_id"]),
            "rating": fb["rating"],
            "comment": fb.get("comment"),
            "submitted_at": fb["submitted_at"]
        })
    
    return {
        "assertion_id": assertion_id,
        "feedback": feedback_serializable,
        "average_rating": sum(fb["rating"] for fb in feedback_serializable) / len(feedback_serializable) if feedback_serializable else 0
    }



@router.post("/{assertion_id}/regenerate")
async def regenerate_assertion(
    assertion_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Regenerate an assertion based on previous feedback
    
    Uses feedback history to improve the assertion generation.
    Includes previous feedback in LLM context to generate better assertions.
    
    Args:
        assertion_id: Assertion ID to regenerate
        current_user_id: Current authenticated user ID
        
    Returns:
        Newly generated assertion
        
    Validates: Requirements 10.4
    """
    db = Database.get_db()
    
    # Load assertion
    assertion = await db.assertions.find_one({"_id": ObjectId(assertion_id)})
    if not assertion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assertion not found"
        )
    
    # Verify project ownership
    project_id = str(assertion["project_id"])
    await verify_project_ownership(project_id, current_user_id)
    
    # Load feedback for this assertion
    feedback_list = await db.feedback.find(
        {"assertion_id": ObjectId(assertion_id)}
    ).to_list(length=None)
    
    # Load requirement and RTL context
    requirement_text = assertion.get("traceability", {}).get("requirement_text", "")
    rtl_signals = assertion.get("traceability", {}).get("rtl_signals", [])
    rtl_module = assertion.get("traceability", {}).get("rtl_module", "")
    
    # Build feedback summary
    feedback_summary = ""
    if feedback_list:
        avg_rating = sum(fb["rating"] for fb in feedback_list) / len(feedback_list)
        feedback_summary = f"Previous assertion received {len(feedback_list)} feedback(s) with average rating {avg_rating:.1f}/5.\n\n"
        
        # Include comments from low-rated feedback
        low_rated_comments = [
            fb["comment"] for fb in feedback_list 
            if fb.get("comment") and fb["rating"] <= 3
        ]
        
        if low_rated_comments:
            feedback_summary += "Issues identified:\n"
            for comment in low_rated_comments:
                feedback_summary += f"- {comment}\n"
    
    # Create regeneration prompt
    from ..agents.prompt_templates import SVAGeneratorPrompts
    from ..clients.groq_client import GroqClient
    
    system_prompt = SVAGeneratorPrompts.get_system_prompt()
    
    user_prompt = f"""Regenerate an improved SystemVerilog Assertion based on the following:

Requirement: {requirement_text}

RTL Context:
- Module: {rtl_module}
- Signals: {', '.join(rtl_signals)}

Previous Assertion:
{assertion['code']}

{feedback_summary}

Please generate an improved assertion that addresses the feedback and better captures the requirement.
Provide the assertion code in a JSON format with the following structure:
{{
    "code": "the assertion code",
    "explanation": "explanation of improvements made",
    "type": "immediate or concurrent"
}}"""
    
    # Call LLM
    groq_client = GroqClient()
    try:
        response = await groq_client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        response_content = response["choices"][0]["message"]["content"]
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', response_content)
        if json_match:
            result = json.loads(json_match.group())
        else:
            raise ValueError("No JSON found in response")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate assertion: {str(e)}"
        )
    
    # Validate syntax
    is_valid, error_message = validate_sva_syntax(result["code"])
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Generated assertion has syntax errors: {error_message}"
        )
    
    # Create new assertion
    new_assertion_doc = {
        "project_id": ObjectId(project_id),
        "code": result["code"],
        "type": result.get("type", "unknown"),
        "category": assertion.get("category", "unknown"),
        "confidence_score": 0.8,  # Slightly lower since it's regenerated
        "explanation": result.get("explanation", ""),
        "traceability": assertion.get("traceability", {}),
        "generated_at": datetime.utcnow(),
        "regenerated_from": ObjectId(assertion_id),
        "feedback_incorporated": len(feedback_list)
    }
    
    result_insert = await db.assertions.insert_one(new_assertion_doc)
    new_assertion_id = result_insert.inserted_id
    
    # Mark old assertion as superseded
    await db.assertions.update_one(
        {"_id": ObjectId(assertion_id)},
        {"$set": {"superseded_by": new_assertion_id, "superseded_at": datetime.utcnow()}}
    )
    
    return {
        "new_assertion_id": str(new_assertion_id),
        "code": result["code"],
        "explanation": result.get("explanation", ""),
        "type": result.get("type", "unknown"),
        "feedback_incorporated": len(feedback_list),
        "message": "Assertion regenerated successfully"
    }
