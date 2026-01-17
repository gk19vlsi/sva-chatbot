"""
Property-Based Tests for Validation Agent

Tests universal properties that must hold for all assertion validation operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.agents.validation import ValidationAgent
from app.agents.base import PipelineContext
from app.clients.groq_client import GroqClient
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
import json


# Strategy for generating assertions
@st.composite
def sva_assertion(draw):
    """Generate a SystemVerilog assertion."""
    signal1 = draw(st.sampled_from(["valid", "ready", "req", "ack"]))
    signal2 = draw(st.sampled_from(["ready", "done", "ack", "grant"]))
    clock = draw(st.sampled_from(["clk", "clock"]))
    reset = draw(st.sampled_from(["rst_n", "reset_n"]))
    
    # Generate valid SVA code
    code = f"""// Validates: REQ-001
assert property (@(posedge {clock}) disable iff (!{reset})
    {signal1} |-> {signal2}
);"""
    
    return {
        "id": str(ObjectId()),
        "assertion_code": code,
        "requirement_id": "REQ-001",
        "confidence_score": 0.9
    }


@pytest.mark.asyncio
@given(assertion=sva_assertion())
@settings(max_examples=100, deadline=None)
async def test_quality_score_range(assertion):
    """
    Property 19: Quality Score Range
    
    Universal Property:
    For any validated assertion, the quality score must be
    between 0.0 and 1.0.
    
    Validates: Requirements 7.4, 7.5
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.assertions = AsyncMock()
    mock_db.assertions.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = ValidationAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response for quality analysis
    mock_quality_response = json.dumps({
        "has_vacuity": False,
        "vacuity_reason": "",
        "has_over_constraint": False,
        "over_constraint_reason": "",
        "complexity": "simple",
        "notes": "Good quality assertion"
    })
    
    agent.call_groq = AsyncMock(return_value=mock_quality_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "assertions": [assertion]
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully validate
    assert result.success, f"Agent failed: {result.error}"
    assert "assertions" in result.data
    
    # Property: Must have validated assertions
    validated_assertions = result.data["assertions"]
    assert len(validated_assertions) > 0
    
    validated = validated_assertions[0]
    
    # Property: Quality score must be in valid range [0.0, 1.0]
    assert "quality_score" in validated
    quality_score = validated["quality_score"]
    assert 0.0 <= quality_score <= 1.0, \
        f"Quality score {quality_score} out of range [0.0, 1.0]"
    
    # Property: Must have validation metadata
    assert "syntax_valid" in validated
    assert "validated_at" in validated
    
    # Property: Syntax validation must be boolean
    assert isinstance(validated["syntax_valid"], bool)


@pytest.mark.asyncio
async def test_syntax_validation():
    """
    Test that syntax validation correctly identifies valid and invalid assertions.
    
    Part of Property 19: Quality Score Range
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.assertions = AsyncMock()
    mock_db.assertions.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = ValidationAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response
    mock_quality_response = json.dumps({
        "has_vacuity": False,
        "has_over_constraint": False,
        "complexity": "simple",
        "notes": "Good"
    })
    agent.call_groq = AsyncMock(return_value=mock_quality_response)
    
    # Test with valid assertion
    valid_assertion = {
        "id": str(ObjectId()),
        "assertion_code": "assert property (@(posedge clk) valid |-> ready);",
        "requirement_id": "REQ-001"
    }
    
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={"assertions": [valid_assertion]}
    )
    
    result = await agent.execute(context)
    
    # Property: Valid assertion should pass syntax check
    assert result.success
    validated = result.data["assertions"][0]
    assert validated["syntax_valid"] == True
    
    # Property: Quality score should be high for valid syntax
    assert validated["quality_score"] >= 0.5


@pytest.mark.asyncio
async def test_vacuity_detection():
    """
    Test that vacuity is detected and affects quality score.
    
    Part of Property 19: Quality Score Range
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.assertions = AsyncMock()
    mock_db.assertions.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = ValidationAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response indicating vacuity
    mock_quality_response = json.dumps({
        "has_vacuity": True,
        "vacuity_reason": "Assertion is always true",
        "has_over_constraint": False,
        "complexity": "simple",
        "notes": "Vacuous assertion detected"
    })
    agent.call_groq = AsyncMock(return_value=mock_quality_response)
    
    # Test assertion
    assertion = {
        "id": str(ObjectId()),
        "assertion_code": "assert property (@(posedge clk) 1'b1);",
        "requirement_id": "REQ-001"
    }
    
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={"assertions": [assertion]}
    )
    
    result = await agent.execute(context)
    
    # Property: Vacuity must be detected
    assert result.success
    validated = result.data["assertions"][0]
    assert validated["vacuity_detected"] == True
    
    # Property: Quality score must be lower when vacuity detected
    assert validated["quality_score"] < 0.8


@pytest.mark.asyncio
async def test_over_constraint_detection():
    """
    Test that over-constraints are detected and affect quality score.
    
    Part of Property 19: Quality Score Range
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.assertions = AsyncMock()
    mock_db.assertions.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = ValidationAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response indicating over-constraint
    mock_quality_response = json.dumps({
        "has_vacuity": False,
        "has_over_constraint": True,
        "over_constraint_reason": "Assertion is too restrictive",
        "complexity": "complex",
        "notes": "Over-constrained assertion"
    })
    agent.call_groq = AsyncMock(return_value=mock_quality_response)
    
    # Test assertion
    assertion = {
        "id": str(ObjectId()),
        "assertion_code": "assert property (@(posedge clk) valid && ready && done);",
        "requirement_id": "REQ-001"
    }
    
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={"assertions": [assertion]}
    )
    
    result = await agent.execute(context)
    
    # Property: Over-constraint must be detected
    assert result.success
    validated = result.data["assertions"][0]
    assert validated["over_constraint_detected"] == True
    
    # Property: Quality score must be lower when over-constraint detected
    assert validated["quality_score"] < 0.9


@pytest.mark.asyncio
async def test_multiple_assertions_validation():
    """
    Test that multiple assertions can be validated in one execution.
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.assertions = AsyncMock()
    mock_db.assertions.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = ValidationAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response
    mock_quality_response = json.dumps({
        "has_vacuity": False,
        "has_over_constraint": False,
        "complexity": "simple",
        "notes": "Good"
    })
    agent.call_groq = AsyncMock(return_value=mock_quality_response)
    
    # Multiple assertions
    assertions = [
        {
            "id": str(ObjectId()),
            "assertion_code": "assert property (@(posedge clk) req |-> ack);",
            "requirement_id": "REQ-001"
        },
        {
            "id": str(ObjectId()),
            "assertion_code": "assert property (@(posedge clk) valid |-> ready);",
            "requirement_id": "REQ-002"
        }
    ]
    
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={"assertions": assertions}
    )
    
    result = await agent.execute(context)
    
    # Property: All assertions must be validated
    assert result.success
    validated_assertions = result.data["assertions"]
    assert len(validated_assertions) == 2
    
    # Property: Each assertion must have quality score
    for validated in validated_assertions:
        assert "quality_score" in validated
        assert 0.0 <= validated["quality_score"] <= 1.0


if __name__ == "__main__":
    print("Run with: pytest tests/test_validation_properties.py -v")
