"""
WebSocket routes for real-time updates

Provides WebSocket endpoint for streaming agent status updates, assertions,
and error notifications to the frontend in real-time.

Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import logging
import json
import asyncio
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections and message delivery
    
    Features:
    - Track active connections per project
    - Queue messages for disconnected clients
    - Broadcast messages to all connected clients for a project
    - Handle connection/disconnection gracefully
    
    Validates: Requirements 9.1, 9.2, 9.4
    """
    
    def __init__(self):
        # Active connections: {project_id: [websocket1, websocket2, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Message queue for disconnected clients: {project_id: deque([msg1, msg2, ...])}
        self.message_queues: Dict[str, deque] = {}
        
        # Maximum messages to queue per project
        self.max_queue_size = 100
    
    async def connect(self, websocket: WebSocket, project_id: str):
        """
        Accept and register a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            project_id: Project ID for this connection
        """
        await websocket.accept()
        
        # Add to active connections
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        
        logger.info(f"WebSocket connected for project {project_id}")
        
        # Send queued messages if any
        if project_id in self.message_queues:
            queue = self.message_queues[project_id]
            while queue:
                message = queue.popleft()
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending queued message: {e}")
                    # Re-queue the message
                    queue.appendleft(message)
                    break
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: WebSocket connection to remove
            project_id: Project ID for this connection
        """
        if project_id in self.active_connections:
            if websocket in self.active_connections[project_id]:
                self.active_connections[project_id].remove(websocket)
                
                # Clean up empty connection lists
                if not self.active_connections[project_id]:
                    del self.active_connections[project_id]
        
        logger.info(f"WebSocket disconnected for project {project_id}")
    
    async def send_message(self, project_id: str, message: dict):
        """
        Send a message to all connected clients for a project
        
        If no clients are connected, queue the message for later delivery.
        
        Args:
            project_id: Project ID
            message: Message dictionary to send
            
        Validates: Requirements 9.1, 9.2, 9.4
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        # Check if any clients are connected
        if project_id in self.active_connections and self.active_connections[project_id]:
            # Send to all connected clients
            disconnected = []
            for websocket in self.active_connections[project_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.append(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected:
                self.disconnect(websocket, project_id)
        else:
            # No clients connected - queue the message
            if project_id not in self.message_queues:
                self.message_queues[project_id] = deque(maxlen=self.max_queue_size)
            
            self.message_queues[project_id].append(message)
            logger.info(f"Message queued for project {project_id} (no active connections)")
    
    async def send_status_update(self, project_id: str, agent_name: str, status: str, data: Optional[dict] = None):
        """
        Send agent status update
        
        Args:
            project_id: Project ID
            agent_name: Name of the agent
            status: Status (started, completed, failed)
            data: Optional additional data
            
        Validates: Requirement 9.1, 9.2
        """
        message = {
            "type": "status_update",
            "agent_name": agent_name,
            "status": status,
            "data": data or {}
        }
        await self.send_message(project_id, message)
    
    async def send_assertion(self, project_id: str, assertion: dict):
        """
        Stream a generated assertion to the frontend
        
        Args:
            project_id: Project ID
            assertion: Assertion dictionary
            
        Validates: Requirement 9.4
        """
        message = {
            "type": "assertion",
            "assertion": assertion
        }
        await self.send_message(project_id, message)
    
    async def send_error(self, project_id: str, error: str, agent_name: Optional[str] = None):
        """
        Send error notification
        
        Args:
            project_id: Project ID
            error: Error message
            agent_name: Optional agent name that caused the error
            
        Validates: Requirement 9.5
        """
        message = {
            "type": "error",
            "error": error,
            "agent_name": agent_name
        }
        await self.send_message(project_id, message)
    
    async def send_clarification(self, project_id: str, question: str, context: Optional[dict] = None):
        """
        Send clarification question to user
        
        Args:
            project_id: Project ID
            question: Clarification question
            context: Optional context for the question
            
        Validates: Requirement 9.3
        """
        message = {
            "type": "clarification",
            "question": question,
            "context": context or {}
        }
        await self.send_message(project_id, message)
    
    async def send_completion(self, project_id: str, result: dict):
        """
        Send pipeline completion notification
        
        Args:
            project_id: Project ID
            result: Pipeline result dictionary
        """
        message = {
            "type": "completion",
            "result": result
        }
        await self.send_message(project_id, message)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws/generation/{project_id}")
async def websocket_generation(websocket: WebSocket, project_id: str):
    """
    WebSocket endpoint for real-time generation updates
    
    Streams agent status updates, generated assertions, errors, and
    clarification questions to the frontend in real-time.
    
    Args:
        websocket: WebSocket connection
        project_id: Project ID to monitor
        
    Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5
    """
    # Note: Authentication is handled via query parameter or initial message
    # For production, implement proper WebSocket authentication
    
    await manager.connect(websocket, project_id)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "project_id": project_id,
            "message": "WebSocket connection established"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive messages from client (e.g., responses to clarifications)
                data = await websocket.receive_text()
                
                # Parse and handle client messages
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # Respond to ping with pong
                        await websocket.send_json({"type": "pong"})
                    
                    elif message_type == "clarification_response":
                        # Handle user response to clarification question
                        # This would be processed by the orchestrator
                        logger.info(f"Received clarification response for project {project_id}")
                        # TODO: Forward to orchestrator
                    
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {data}")
            
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
    
    finally:
        manager.disconnect(websocket, project_id)


def get_connection_manager() -> ConnectionManager:
    """
    Get the global connection manager instance
    
    Returns:
        ConnectionManager instance
    """
    return manager
