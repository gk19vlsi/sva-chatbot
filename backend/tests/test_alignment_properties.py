"""
Property-Based Tests for Alignment Agent

Tests universal properties that must hold for all requirement-RTL alignment operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.agents.alignment import AlignmentAgent
from app.agents.base import PipelineContext
from app.clients.groq_client import GroqClient
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
import json


# Strategy for generating requirements
@st.composite
def requirement_with_entities(draw):
    """Generate a requirement with entities."""
    entities = draw(st.lists(
        st.sampled_from(["valid", "ready", "data", "enable", "clk", "rst_n"]),
        min_size=1,
        max_size=3,
        unique=True
    ))
    
    req_text = f"When {entities[0]} is high, "
    if len(entities) > 1:
        req_text += f"{entities[1]} must be asserted"
    else:
        req_text += "the system must respond"
    
    return {
        "requirement_id": f"REQ-{draw(st.integers(min_value=1, max_value=999)):03d}",
        "text": req_text,
        "entities": entities,
        "category": "functional"
    }


@pytest.mark.asyncio
@given(requirement=requirement_with_entities())
@settings(max_examples=100, deadline=None)
async def test_alignment_confidence_range(requirement):
    """
    Property 12: Requirement-RTL Alignment Confidence
    
    Universal Property:
    For any requirement-RTL alignment, the confidence score must be
    between 0.0 and 1.0, and higher when more entities are mapped.
    
    Validates: Requirements 5.1, 5.2
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.alignments = AsyncMock()
    mock_db.alignments.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = AlignmentAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Create RTL modules with signals matching the entities
    entities = requirement["entities"]
    rtl_modules = [{
        "name": "test_module",
        "signals": [
            {"name": entity, "type": "logic", "direction": "input"}
            for entity in entities
        ],
        "clocks": ["clk"],
        "resets": ["rst_n"]
    }]
    
    # Mock LLM response with good mappings
    mapped_signals = [
        {
            "entity": entity,
            "rtl_signal": entity,
            "module": "test_module",
            "confidence": 0.9
        }
        for entity in entities
    ]
    
    mock_mapping_response = json.dumps({
        "signals": mapped_signals,
        "ambiguities": [],
        "notes": "All entities mapped successfully"
    })
    
    agent.call_groq = AsyncMock(return_value=mock_mapping_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [requirement],
            "rtl_modules": rtl_modules
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully align
    assert result.success, f"Agent failed: {result.error}"
    assert "alignments" in result.data
    
    # Property: Must have alignments
    alignments = result.data["alignments"]
    assert len(alignments) > 0
    
    alignment = alignments[0]
    
    # Property: Confidence must be in valid range [0.0, 1.0]
    assert "confidence" in alignment
    confidence = alignment["confidence"]
    assert 0.0 <= confidence <= 1.0, \
        f"Confidence {confidence} out of range [0.0, 1.0]"
    
    # Property: When all entities are mapped, confidence should be high
    mapped_signals = alignment.get("mapped_signals", [])
    if len(mapped_signals) == len(entities):
        assert confidence >= 0.5, \
            f"Expected high confidence when all entities mapped, got {confidence}"
    
    # Property: Alignment must have required fields
    assert "requirement_id" in alignment
    assert "requirement_text" in alignment
    assert "mapped_signals" in alignment
    assert "entities" in alignment


@pytest.mark.asyncio
async def test_missing_implementation_detection():
    """
    Property 13: Missing Implementation Detection
    
    Universal Property:
    When a requirement has no mapped signals or low confidence,
    it must be flagged as a missing implementation.
    
    Validates: Requirements 5.3
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.alignments = AsyncMock()
    mock_db.alignments.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = AlignmentAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Create requirement with entities
    requirement = {
        "requirement_id": "REQ-001",
        "text": "The system must implement feature X",
        "entities": ["feature_x", "system"],
        "category": "functional"
    }
    
    # Create RTL modules WITHOUT the required signals
    rtl_modules = [{
        "name": "test_module",
        "signals": [
            {"name": "other_signal", "type": "logic", "direction": "input"}
        ],
        "clocks": ["clk"],
        "resets": ["rst_n"]
    }]
    
    # Mock LLM response with no mappings
    mock_mapping_response = json.dumps({
        "signals": [],
        "ambiguities": ["Cannot find signals for feature_x"],
        "notes": "No matching signals found"
    })
    
    agent.call_groq = AsyncMock(return_value=mock_mapping_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [requirement],
            "rtl_modules": rtl_modules
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully execute
    assert result.success
    
    # Property: Must identify missing implementation
    missing = result.data.get("missing_implementations", [])
    assert len(missing) > 0, "Expected missing implementation to be detected"
    
    # Property: Missing implementation must reference the requirement
    missing_item = missing[0]
    assert missing_item["requirement_id"] == "REQ-001"
    assert "reason" in missing_item


@pytest.mark.asyncio
async def test_alignment_persistence():
    """
    Property 14: Alignment Persistence
    
    Universal Property:
    All alignments must be stored in the database with complete information.
    
    Validates: Requirements 5.5
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.alignments = AsyncMock()
    
    # Track what was stored
    stored_alignments = []
    async def mock_update_one(filter_doc, update_doc, **kwargs):
        stored_alignments.append(update_doc["$set"])
        return AsyncMock()
    
    mock_db.alignments.update_one = mock_update_one
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = AlignmentAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Create requirement
    requirement = {
        "requirement_id": "REQ-001",
        "text": "When valid is high, ready must respond",
        "entities": ["valid", "ready"],
        "category": "functional"
    }
    
    # Create RTL modules
    rtl_modules = [{
        "name": "test_module",
        "signals": [
            {"name": "valid", "type": "logic", "direction": "input"},
            {"name": "ready", "type": "logic", "direction": "output"}
        ]
    }]
    
    # Mock LLM response
    mock_mapping_response = json.dumps({
        "signals": [
            {"entity": "valid", "rtl_signal": "valid", "module": "test_module", "confidence": 0.9},
            {"entity": "ready", "rtl_signal": "ready", "module": "test_module", "confidence": 0.9}
        ],
        "ambiguities": [],
        "notes": "Clear mapping"
    })
    
    agent.call_groq = AsyncMock(return_value=mock_mapping_response)
    
    # Create context
    project_id = str(ObjectId())
    context = PipelineContext(
        project_id=project_id,
        data={
            "requirements": [requirement],
            "rtl_modules": rtl_modules
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully execute
    assert result.success
    
    # Property: Must store alignments
    assert len(stored_alignments) > 0, "No alignments were stored"
    
    # Property: Stored alignment must have required fields
    stored = stored_alignments[0]
    assert "project_id" in stored
    assert "requirement_id" in stored
    assert "requirement_text" in stored
    assert "mapped_signals" in stored
    assert "confidence" in stored
    assert "created_at" in stored
    
    # Property: Project ID must match
    assert str(stored["project_id"]) == project_id


if __name__ == "__main__":
    print("Run with: pytest tests/test_alignment_properties.py -v")
