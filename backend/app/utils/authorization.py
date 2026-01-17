"""
Authorization utilities for project ownership
"""
from fastapi import Depends, HTTPException, status
from bson import ObjectId
from ..database import Database
from .auth import get_current_user


async def verify_project_ownership(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
) -> dict:
    """
    Verify that the current user owns the specified project
    
    Args:
        project_id: Project ID to check
        current_user_id: Current authenticated user ID
        
    Returns:
        Project document if user owns it
        
    Raises:
        HTTPException: 404 if project not found or user doesn't own it
    """
    db = Database.get_db()
    
    # Find project
    try:
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify ownership
    if str(project.get("user_id")) != current_user_id:
        # Return 404 instead of 403 to not reveal project existence
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project
