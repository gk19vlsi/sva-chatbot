"""
Property-Based Tests for WebSocket Real-Time Updates

Tests universal properties that must hold for all WebSocket communication operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.routes.websocket import ConnectionManager
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
import asyncio
from datetime import datetime


@pytest.mark.asyncio
@given(
    project_id=st.text(min_size=24, max_size=24, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))),
    agent_name=st.sampled_from(["spec_parser", "rtl_analyzer", "alignment", "sva_generator", "validation"]),
    status=st.sampled_from(["started", "completed", "failed"])
)
@settings(max_examples=20, deadline=None)
async def test_websocket_status_update_delivery(project_id, agent_name, status):
    """
    Property 22: WebSocket Status Update Delivery
    
    Universal Property:
    For any agent status update, the WebSocket manager should deliver
    the message to all connected clients for that project, or queue it
    if no clients are connected.
    
    Validates: Requirements 9.1, 9.2, 9.4
    """
    # Create connection manager
    manager = ConnectionManager()
    
    # Create mock WebSocket
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    # Connect the WebSocket
    await manager.connect(mock_websocket, project_id)
    
    # Property: WebSocket should be in active connections
    assert project_id in manager.active_connections
    assert mock_websocket in manager.active_connections[project_id]
    
    # Send status update
    await manager.send_status_update(
        project_id=project_id,
        agent_name=agent_name,
        status=status,
        data={"test": "data"}
    )
    
    # Property: Message must be sent to connected client
    assert mock_websocket.send_json.called
    call_args = mock_websocket.send_json.call_args[0][0]
    
    # Property: Message must have correct type
    assert call_args["type"] == "status_update"
    
    # Property: Message must include agent name
    assert call_args["agent_name"] == agent_name
    
    # Property: Message must include status
    assert call_args["status"] == status
    
    # Property: Message must include timestamp
    assert "timestamp" in call_args
    
    # Property: Message must include data
    assert "data" in call_args
    assert call_args["data"]["test"] == "data"


@pytest.mark.asyncio
async def test_websocket_message_queuing():
    """
    Test that messages are queued when no clients are connected.
    
    Part of Property 22: WebSocket Status Update Delivery
    Validates: Requirement 9.4
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Send message without any connected clients
    await manager.send_status_update(
        project_id=project_id,
        agent_name="spec_parser",
        status="started"
    )
    
    # Property: Message must be queued
    assert project_id in manager.message_queues
    assert len(manager.message_queues[project_id]) == 1
    
    # Property: Queued message must have correct structure
    queued_message = manager.message_queues[project_id][0]
    assert queued_message["type"] == "status_update"
    assert queued_message["agent_name"] == "spec_parser"
    assert queued_message["status"] == "started"
    
    # Now connect a client
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    await manager.connect(mock_websocket, project_id)
    
    # Property: Queued message must be sent to newly connected client
    assert mock_websocket.send_json.called
    
    # Property: Queue must be empty after delivery
    assert len(manager.message_queues[project_id]) == 0


@pytest.mark.asyncio
async def test_websocket_multiple_clients():
    """
    Test that messages are broadcast to all connected clients.
    
    Part of Property 22: WebSocket Status Update Delivery
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Connect multiple clients
    mock_websocket1 = AsyncMock()
    mock_websocket1.send_json = AsyncMock()
    
    mock_websocket2 = AsyncMock()
    mock_websocket2.send_json = AsyncMock()
    
    await manager.connect(mock_websocket1, project_id)
    await manager.connect(mock_websocket2, project_id)
    
    # Property: Both clients should be connected
    assert len(manager.active_connections[project_id]) == 2
    
    # Send message
    await manager.send_status_update(
        project_id=project_id,
        agent_name="rtl_analyzer",
        status="completed"
    )
    
    # Property: Message must be sent to all connected clients
    assert mock_websocket1.send_json.called
    assert mock_websocket2.send_json.called
    
    # Property: Both clients receive the same message
    call1 = mock_websocket1.send_json.call_args[0][0]
    call2 = mock_websocket2.send_json.call_args[0][0]
    
    assert call1["type"] == call2["type"]
    assert call1["agent_name"] == call2["agent_name"]
    assert call1["status"] == call2["status"]


@pytest.mark.asyncio
async def test_websocket_assertion_streaming():
    """
    Test that assertions are streamed to connected clients.
    
    Part of Property 22: WebSocket Status Update Delivery
    Validates: Requirement 9.4
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Connect client
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    await manager.connect(mock_websocket, project_id)
    
    # Send assertion
    assertion = {
        "id": str(ObjectId()),
        "assertion_code": "assert property (@(posedge clk) valid |-> ready);",
        "confidence_score": 0.9
    }
    
    await manager.send_assertion(project_id, assertion)
    
    # Property: Assertion must be sent
    assert mock_websocket.send_json.called
    call_args = mock_websocket.send_json.call_args[0][0]
    
    # Property: Message type must be "assertion"
    assert call_args["type"] == "assertion"
    
    # Property: Assertion data must be included
    assert "assertion" in call_args
    assert call_args["assertion"]["id"] == assertion["id"]
    assert call_args["assertion"]["assertion_code"] == assertion["assertion_code"]


@pytest.mark.asyncio
@given(
    project_id=st.text(min_size=24, max_size=24, alphabet=st.characters(whitelist_categories=('Ll', 'Nd'))),
    error_message=st.text(min_size=10, max_size=100),
    agent_name=st.sampled_from(["spec_parser", "rtl_analyzer", "alignment", "sva_generator", "validation", None])
)
@settings(max_examples=20, deadline=None)
async def test_error_notification_immediacy(project_id, error_message, agent_name):
    """
    Property 23: Error Notification Immediacy
    
    Universal Property:
    For any error that occurs during pipeline execution, the WebSocket
    manager should immediately notify all connected clients with error
    details including the agent name (if applicable).
    
    Validates: Requirements 9.5, 19.2
    """
    # Create connection manager
    manager = ConnectionManager()
    
    # Connect client
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    await manager.connect(mock_websocket, project_id)
    
    # Record time before sending error
    start_time = asyncio.get_event_loop().time()
    
    # Send error notification
    await manager.send_error(
        project_id=project_id,
        error=error_message,
        agent_name=agent_name
    )
    
    # Record time after sending error
    end_time = asyncio.get_event_loop().time()
    
    # Property: Error must be sent immediately (within 100ms)
    delivery_time = end_time - start_time
    assert delivery_time < 0.1, f"Error delivery took {delivery_time}s, expected < 0.1s"
    
    # Property: Error message must be sent
    assert mock_websocket.send_json.called
    call_args = mock_websocket.send_json.call_args[0][0]
    
    # Property: Message type must be "error"
    assert call_args["type"] == "error"
    
    # Property: Error message must be included
    assert "error" in call_args
    assert call_args["error"] == error_message
    
    # Property: Agent name must be included if provided
    if agent_name:
        assert call_args["agent_name"] == agent_name
    
    # Property: Timestamp must be included
    assert "timestamp" in call_args


@pytest.mark.asyncio
async def test_error_notification_without_connection():
    """
    Test that errors are queued when no clients are connected.
    
    Part of Property 23: Error Notification Immediacy
    Validates: Requirement 9.5
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Send error without connected clients
    await manager.send_error(
        project_id=project_id,
        error="Test error message",
        agent_name="spec_parser"
    )
    
    # Property: Error must be queued
    assert project_id in manager.message_queues
    assert len(manager.message_queues[project_id]) == 1
    
    # Property: Queued error must have correct structure
    queued_error = manager.message_queues[project_id][0]
    assert queued_error["type"] == "error"
    assert queued_error["error"] == "Test error message"
    assert queued_error["agent_name"] == "spec_parser"


@pytest.mark.asyncio
async def test_clarification_question_delivery():
    """
    Test that clarification questions are delivered to clients.
    
    Validates: Requirement 9.3
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Connect client
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    await manager.connect(mock_websocket, project_id)
    
    # Send clarification question
    question = "Which clock signal should be used for this assertion?"
    context = {"requirement_id": "REQ-001", "signals": ["clk1", "clk2"]}
    
    await manager.send_clarification(
        project_id=project_id,
        question=question,
        context=context
    )
    
    # Property: Clarification must be sent
    assert mock_websocket.send_json.called
    call_args = mock_websocket.send_json.call_args[0][0]
    
    # Property: Message type must be "clarification"
    assert call_args["type"] == "clarification"
    
    # Property: Question must be included
    assert call_args["question"] == question
    
    # Property: Context must be included
    assert call_args["context"] == context


@pytest.mark.asyncio
async def test_websocket_disconnection_cleanup():
    """
    Test that disconnected clients are properly cleaned up.
    
    Part of Property 22: WebSocket Status Update Delivery
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Connect client
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock()
    
    await manager.connect(mock_websocket, project_id)
    
    # Property: Client should be connected
    assert project_id in manager.active_connections
    assert mock_websocket in manager.active_connections[project_id]
    
    # Disconnect client
    manager.disconnect(mock_websocket, project_id)
    
    # Property: Client should be removed from active connections
    assert project_id not in manager.active_connections or \
           mock_websocket not in manager.active_connections.get(project_id, [])


@pytest.mark.asyncio
async def test_websocket_failed_send_cleanup():
    """
    Test that clients with failed sends are automatically disconnected.
    
    Part of Property 22: WebSocket Status Update Delivery
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Connect client that will fail on send
    mock_websocket = AsyncMock()
    mock_websocket.send_json = AsyncMock(side_effect=Exception("Connection lost"))
    
    await manager.connect(mock_websocket, project_id)
    
    # Property: Client should be connected initially
    assert project_id in manager.active_connections
    assert mock_websocket in manager.active_connections[project_id]
    
    # Try to send message (will fail)
    await manager.send_status_update(
        project_id=project_id,
        agent_name="spec_parser",
        status="started"
    )
    
    # Property: Failed client should be automatically disconnected
    assert project_id not in manager.active_connections or \
           mock_websocket not in manager.active_connections.get(project_id, [])


@pytest.mark.asyncio
async def test_message_queue_size_limit():
    """
    Test that message queue respects maximum size limit.
    
    Part of Property 22: WebSocket Status Update Delivery
    """
    # Create connection manager
    manager = ConnectionManager()
    
    project_id = str(ObjectId())
    
    # Send more messages than queue size limit
    for i in range(manager.max_queue_size + 10):
        await manager.send_status_update(
            project_id=project_id,
            agent_name="spec_parser",
            status="started",
            data={"iteration": i}
        )
    
    # Property: Queue size must not exceed maximum
    assert len(manager.message_queues[project_id]) <= manager.max_queue_size
    
    # Property: Oldest messages should be dropped (FIFO with max size)
    # The queue should contain the most recent messages
    queued_messages = list(manager.message_queues[project_id])
    assert len(queued_messages) == manager.max_queue_size


if __name__ == "__main__":
    print("Run with: pytest tests/test_websocket_properties.py -v")
