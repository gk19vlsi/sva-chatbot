"""
Chat and conversational refinement routes

Handles conversational interactions for clarifications and assertion refinement.

Validates: Requirements 10.4, 10.5
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

from ..database import Database
from ..utils.auth import get_current_user
from ..utils.authorization import verify_project_ownership
from ..clients.groq_client import GroqClient

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    project_id: str
    message: str
    context: Optional[str] = None  # Optional context (e.g., assertion code, requirement)


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    timestamp: datetime


@router.post("", response_model=ChatResponse)
async def send_chat_message(
    chat_request: ChatRequest,
    current_user_id: str = Depends(get_current_user)
):
    """
    Send a chat message for clarifications or refinement
    
    Uses LLM to provide conversational responses about assertions,
    requirements, and RTL design.
    
    Args:
        chat_request: Chat message and context
        current_user_id: Current authenticated user ID
        
    Returns:
        Assistant response
        
    Validates: Requirements 10.5
    """
    db = Database.get_db()
    
    # Verify project ownership
    await verify_project_ownership(chat_request.project_id, current_user_id)
    
    # Load or create conversation
    conversation = await db.conversations.find_one({
        "project_id": ObjectId(chat_request.project_id),
        "user_id": current_user_id,
        "active": True
    })
    
    if not conversation:
        # Create new conversation
        conversation_doc = {
            "project_id": ObjectId(chat_request.project_id),
            "user_id": current_user_id,
            "messages": [],
            "created_at": datetime.utcnow(),
            "active": True
        }
        result = await db.conversations.insert_one(conversation_doc)
        conversation_id = result.inserted_id
        conversation = conversation_doc
        conversation["_id"] = conversation_id
    else:
        conversation_id = conversation["_id"]
    
    # Add user message to conversation
    user_message = {
        "role": "user",
        "content": chat_request.message,
        "timestamp": datetime.utcnow()
    }
    
    await db.conversations.update_one(
        {"_id": conversation_id},
        {"$push": {"messages": user_message}}
    )
    
    # Build conversation history for LLM
    messages = conversation.get("messages", [])
    messages.append(user_message)
    
    # Create system prompt
    system_prompt = """You are an expert SystemVerilog Assertion (SVA) assistant. 
You help users understand, refine, and improve their assertions. You can:
- Explain assertion syntax and semantics
- Suggest improvements to assertions
- Clarify requirements and their mapping to RTL
- Answer questions about temporal logic and SVA patterns
- Help debug assertion issues

Be concise, technical, and helpful. Provide code examples when relevant."""
    
    # Add context if provided
    if chat_request.context:
        system_prompt += f"\n\nContext:\n{chat_request.context}"
    
    # Prepare messages for LLM
    llm_messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history (last 10 messages)
    for msg in messages[-10:]:
        llm_messages.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    # Get LLM response
    groq_client = GroqClient()
    try:
        response = await groq_client.chat_completion(
            messages=llm_messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        assistant_message_content = response["choices"][0]["message"]["content"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get LLM response: {str(e)}"
        )
    
    # Add assistant message to conversation
    assistant_message = {
        "role": "assistant",
        "content": assistant_message_content,
        "timestamp": datetime.utcnow()
    }
    
    await db.conversations.update_one(
        {"_id": conversation_id},
        {
            "$push": {"messages": assistant_message},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return ChatResponse(
        message=assistant_message_content,
        conversation_id=str(conversation_id),
        timestamp=assistant_message["timestamp"]
    )


@router.get("/{project_id}/history")
async def get_conversation_history(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Get conversation history for a project
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Conversation history
    """
    db = Database.get_db()
    
    # Verify project ownership
    await verify_project_ownership(project_id, current_user_id)
    
    # Load conversation
    conversation = await db.conversations.find_one({
        "project_id": ObjectId(project_id),
        "user_id": current_user_id,
        "active": True
    })
    
    if not conversation:
        return {
            "project_id": project_id,
            "messages": [],
            "conversation_id": None
        }
    
    return {
        "project_id": project_id,
        "conversation_id": str(conversation["_id"]),
        "messages": conversation.get("messages", []),
        "created_at": conversation.get("created_at"),
        "updated_at": conversation.get("updated_at")
    }


@router.delete("/{project_id}/history")
async def clear_conversation_history(
    project_id: str,
    current_user_id: str = Depends(get_current_user)
):
    """
    Clear conversation history for a project
    
    Args:
        project_id: Project ID
        current_user_id: Current authenticated user ID
        
    Returns:
        Success message
    """
    db = Database.get_db()
    
    # Verify project ownership
    await verify_project_ownership(project_id, current_user_id)
    
    # Mark conversation as inactive
    await db.conversations.update_many(
        {
            "project_id": ObjectId(project_id),
            "user_id": current_user_id,
            "active": True
        },
        {"$set": {"active": False}}
    )
    
    return {"message": "Conversation history cleared"}
