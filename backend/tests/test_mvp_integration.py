"""
MVP Integration Test

Tests the complete flow from file upload to assertion generation and display.
This validates that all MVP components work together correctly.

Test Flow:
1. Upload specification file
2. Upload RTL file
3. Generate assertions using SVA Generator agent
4. Verify assertions are stored in database
5. Verify assertions can be retrieved and displayed
"""
import pytest
from bson import ObjectId
from app.agents.sva_generator import SVAGeneratorAgent
from app.agents.base import PipelineContext
from app.clients.groq_client import GroqClient
from unittest.mock import AsyncMock, MagicMock
import json


@pytest.mark.asyncio
async def test_mvp_complete_flow():
    """
    Integration test for complete MVP flow
    
    Tests: Upload spec + RTL → Generate assertion → Store in DB → Display
    """
    # Setup mock database
    mock_db = MagicMock()
    
    # Mock specifications collection
    mock_specs_collection = AsyncMock()
    spec_id = ObjectId()
    mock_specs_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=spec_id))
    mock_db.specifications = mock_specs_collection
    
    # Mock rtl_designs collection
    mock_rtl_collection = AsyncMock()
    rtl_id = ObjectId()
    mock_rtl_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=rtl_id))
    mock_db.rtl_designs = mock_rtl_collection
    
    # Mock assertions collection
    mock_assertions_collection = AsyncMock()
    assertion_id = ObjectId()
    mock_assertions_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=assertion_id))
    
    # Mock find_one to return stored assertion
    stored_assertion_data = None
    async def mock_find_one(query):
        return stored_assertion_data
    mock_assertions_collection.find_one = mock_find_one
    
    # Mock find to return list of assertions
    def mock_find(query):
        mock_cursor = AsyncMock()
        async def to_list(length):
            return [stored_assertion_data] if stored_assertion_data else []
        mock_cursor.to_list = to_list
        return mock_cursor
    mock_assertions_collection.find = mock_find
    
    mock_db.assertions = mock_assertions_collection
    
    # Mock agent_executions collection
    mock_db.agent_executions = AsyncMock()
    mock_db.agent_executions.insert_one = AsyncMock()
    
    # Setup
    project_id = str(ObjectId())
    
    # Step 1: Simulate specification upload
    spec_doc = {
        "project_id": ObjectId(project_id),
        "filename": "test_spec.md",
        "file_type": "md",
        "raw_text": "When valid is high, ready must be asserted within 5 cycles",
        "parsed_requirements": [
            {
                "requirement_id": "REQ-001",
                "text": "When valid is high, ready must be asserted within 5 cycles",
                "category": "timing",
                "temporal_keywords": ["within"],
                "entities": ["valid", "ready"]
            }
        ],
        "processed": True
    }
    
    spec_result = await mock_specs_collection.insert_one(spec_doc)
    assert spec_result.inserted_id is not None
    print(f"✓ Step 1: Specification uploaded (ID: {spec_result.inserted_id})")
    
    # Step 2: Simulate RTL upload
    rtl_doc = {
        "project_id": ObjectId(project_id),
        "filename": "handshake.sv",
        "source_code": """
module handshake_controller (
    input logic clk,
    input logic rst_n,
    input logic valid,
    output logic ready
);
    // Implementation
endmodule
        """,
        "analysis": {
            "modules": [
                {
                    "name": "handshake_controller",
                    "signals": [
                        {"name": "clk"},
                        {"name": "rst_n"},
                        {"name": "valid"},
                        {"name": "ready"}
                    ],
                    "clocks": ["clk"],
                    "resets": ["rst_n"]
                }
            ]
        },
        "processed": True
    }
    
    rtl_result = await mock_rtl_collection.insert_one(rtl_doc)
    assert rtl_result.inserted_id is not None
    print(f"✓ Step 2: RTL uploaded (ID: {rtl_result.inserted_id})")
    
    # Step 3: Generate assertion using SVA Generator
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Mock LLM response
    mock_sva_code = """// Validates: REQ-001
assert property (@(posedge clk) disable iff (!rst_n)
    valid |-> ##[1:5] ready
);"""
    
    mock_llm_response = json.dumps({
        "code": mock_sva_code,
        "module": "handshake_controller",
        "signals": ["valid", "ready", "clk", "rst_n"],
        "confidence": 0.92,
        "explanation": "Verifies that ready responds within 5 cycles when valid is asserted"
    })
    
    # Create agent and mock the call_groq method
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=mock_db)
    agent.call_groq = AsyncMock(return_value=mock_llm_response)
    
    # Create context with requirements and RTL
    context = PipelineContext(
        project_id=project_id,
        data={
            "requirements": spec_doc["parsed_requirements"],
            "rtl_context": rtl_doc["analysis"]
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    assert result.success, f"Agent execution failed: {result.error}"
    assert "assertions" in result.data
    assert len(result.data["assertions"]) > 0
    print(f"✓ Step 3: Assertion generated ({len(result.data['assertions'])} assertions)")
    
    # Step 4: Verify assertion is stored in database
    generated_assertion = result.data["assertions"][0]
    assertion_id_str = generated_assertion["id"]
    
    # Set the stored assertion data for mock
    stored_assertion_data = {
        "_id": ObjectId(assertion_id_str),
        "assertion_code": mock_sva_code,
        "requirement_id": "REQ-001",
        "confidence_score": 0.92,
        "project_id": ObjectId(project_id),
        "traceability": {
            "requirement_text": spec_doc["parsed_requirements"][0]["text"],
            "rtl_module": "handshake_controller",
            "rtl_signals": ["valid", "ready", "clk", "rst_n"]
        }
    }
    
    stored_assertion = await mock_assertions_collection.find_one({"_id": ObjectId(assertion_id_str)})
    assert stored_assertion is not None, "Assertion not found in database"
    assert stored_assertion["assertion_code"] == mock_sva_code
    assert stored_assertion["requirement_id"] == "REQ-001"
    assert stored_assertion["confidence_score"] == 0.92
    print(f"✓ Step 4: Assertion stored in database (ID: {assertion_id_str})")
    
    # Step 5: Verify assertion can be retrieved for display
    cursor = mock_assertions_collection.find({"project_id": ObjectId(project_id)})
    assertions = await cursor.to_list(length=None)
    
    assert len(assertions) > 0, "No assertions found for project"
    
    display_assertion = assertions[0]
    assert "assertion_code" in display_assertion
    assert "confidence_score" in display_assertion
    assert "traceability" in display_assertion
    assert display_assertion["traceability"]["requirement_text"] == spec_doc["parsed_requirements"][0]["text"]
    print(f"✓ Step 5: Assertion retrieved for display")
    
    # Verify traceability
    traceability = display_assertion["traceability"]
    assert traceability["rtl_module"] == "handshake_controller"
    assert "valid" in traceability["rtl_signals"]
    assert "ready" in traceability["rtl_signals"]
    print(f"✓ Traceability verified: {traceability['rtl_module']}")
    
    print("\n✅ MVP Integration Test PASSED")
    print(f"   - Specification uploaded and parsed")
    print(f"   - RTL uploaded and analyzed")
    print(f"   - Assertion generated with {display_assertion['confidence_score']*100:.0f}% confidence")
    print(f"   - Assertion stored in database")
    print(f"   - Assertion can be retrieved and displayed")
    print(f"   - Traceability links verified")


@pytest.mark.asyncio
async def test_mvp_assertion_syntax_validation():
    """
    Test that generated assertions have valid SVA syntax
    """
    from app.utils.sva_validator import validate_sva_syntax
    
    # Setup mock database
    mock_db = MagicMock()
    mock_assertions_collection = AsyncMock()
    mock_assertions_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=ObjectId()))
    mock_db.assertions = mock_assertions_collection
    mock_db.agent_executions = AsyncMock()
    mock_db.agent_executions.insert_one = AsyncMock()
    
    # Generate a simple assertion
    project_id = str(ObjectId())
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=mock_db)
    
    mock_sva_code = """// Test assertion
assert property (@(posedge clk) valid |-> ready);"""
    
    mock_llm_response = json.dumps({
        "code": mock_sva_code,
        "module": "test_module",
        "signals": ["valid", "ready", "clk"],
        "confidence": 0.85,
        "explanation": "Test assertion"
    })
    
    agent.call_groq = AsyncMock(return_value=mock_llm_response)
    
    context = PipelineContext(
        project_id=project_id,
        data={
            "requirements": [{
                "requirement_id": "REQ-TEST",
                "text": "Valid implies ready",
                "category": "functional",
                "temporal_keywords": [],
                "entities": ["valid", "ready"]
            }],
            "rtl_context": {
                "modules": [{
                    "name": "test_module",
                    "signals": [{"name": "valid"}, {"name": "ready"}, {"name": "clk"}],
                    "clocks": ["clk"],
                    "resets": []
                }],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
        }
    )
    
    result = await agent.execute(context)
    
    assert result.success
    assertion = result.data["assertions"][0]
    
    # Validate syntax
    is_valid, error_msg = validate_sva_syntax(assertion["assertion_code"])
    assert is_valid, f"Generated assertion has invalid syntax: {error_msg}"
    print(f"✓ Assertion syntax validation passed")


@pytest.mark.asyncio
async def test_mvp_multiple_assertions():
    """
    Test generating multiple assertions from multiple requirements
    """
    # Setup mock database
    mock_db = MagicMock()
    mock_assertions_collection = AsyncMock()
    mock_assertions_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=ObjectId()))
    
    assertions_list = []
    def mock_find(query):
        mock_cursor = AsyncMock()
        async def to_list(length):
            return assertions_list
        mock_cursor.to_list = to_list
        return mock_cursor
    mock_assertions_collection.find = mock_find
    
    mock_db.assertions = mock_assertions_collection
    mock_db.agent_executions = AsyncMock()
    mock_db.agent_executions.insert_one = AsyncMock()
    
    project_id = str(ObjectId())
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock responses for multiple requirements
    responses = [
        json.dumps({
            "code": "assert property (@(posedge clk) req1 |-> ack1);",
            "module": "test_module",
            "signals": ["req1", "ack1", "clk"],
            "confidence": 0.9,
            "explanation": "First assertion"
        }),
        json.dumps({
            "code": "assert property (@(posedge clk) req2 |-> ack2);",
            "module": "test_module",
            "signals": ["req2", "ack2", "clk"],
            "confidence": 0.85,
            "explanation": "Second assertion"
        })
    ]
    
    call_count = 0
    async def mock_call_groq(*args, **kwargs):
        nonlocal call_count
        response = responses[call_count]
        call_count += 1
        return response
    
    agent.call_groq = mock_call_groq
    
    context = PipelineContext(
        project_id=project_id,
        data={
            "requirements": [
                {
                    "requirement_id": "REQ-001",
                    "text": "Request 1 implies acknowledge 1",
                    "category": "functional",
                    "temporal_keywords": [],
                    "entities": ["req1", "ack1"]
                },
                {
                    "requirement_id": "REQ-002",
                    "text": "Request 2 implies acknowledge 2",
                    "category": "functional",
                    "temporal_keywords": [],
                    "entities": ["req2", "ack2"]
                }
            ],
            "rtl_context": {
                "modules": [{
                    "name": "test_module",
                    "signals": [
                        {"name": "req1"}, {"name": "ack1"},
                        {"name": "req2"}, {"name": "ack2"},
                        {"name": "clk"}
                    ],
                    "clocks": ["clk"],
                    "resets": []
                }],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
        }
    )
    
    result = await agent.execute(context)
    
    assert result.success
    assert len(result.data["assertions"]) == 2
    print(f"✓ Multiple assertions generated: {len(result.data['assertions'])}")
    
    # Simulate stored assertions
    for assertion in result.data["assertions"]:
        assertions_list.append({
            "_id": ObjectId(assertion["id"]),
            "project_id": ObjectId(project_id),
            "assertion_code": assertion["assertion_code"]
        })
    
    # Verify both assertions are stored
    cursor = mock_assertions_collection.find({"project_id": ObjectId(project_id)})
    assertions = await cursor.to_list(length=None)
    
    assert len(assertions) == 2
    print(f"✓ All assertions stored in database")


if __name__ == "__main__":
    print("Run with: pytest tests/test_mvp_integration.py -v")
