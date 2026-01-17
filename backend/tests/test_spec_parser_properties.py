"""
Property-Based Tests for Specification Parser Agent

Tests universal properties that must hold for all specification parsing operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.agents.spec_parser import SpecificationParserAgent
from app.agents.base import PipelineContext
from app.clients.groq_client import GroqClient
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
import json


# Strategy for generating specification text
@st.composite
def specification_text(draw):
    """Generate realistic specification text with multiple requirements."""
    num_requirements = draw(st.integers(min_value=1, max_value=5))
    requirements = []
    
    for i in range(num_requirements):
        # Generate requirement with various patterns
        signal1 = draw(st.sampled_from(["valid", "ready", "enable", "data", "req", "ack"]))
        signal2 = draw(st.sampled_from(["ready", "valid", "done", "busy", "grant", "resp"]))
        
        patterns = [
            f"When {signal1} is high, {signal2} must be asserted",
            f"The {signal1} signal must be followed by {signal2}",
            f"{signal1} must remain stable until {signal2} is asserted",
            f"If {signal1} is asserted, then {signal2} must respond within 5 cycles",
        ]
        
        req = draw(st.sampled_from(patterns))
        requirements.append(req)
    
    return "\n\n".join(requirements)


@pytest.mark.asyncio
@given(spec_text=specification_text())
@settings(max_examples=100, deadline=None)
async def test_requirement_segmentation_completeness(spec_text):
    """
    Property 4: Requirement Segmentation Completeness
    
    Universal Property:
    For any specification text with N distinct requirements (separated by blank lines),
    the parser must extract at least N requirements.
    
    Validates: Requirements 3.1
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.specifications = AsyncMock()
    mock_db.specifications.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = SpecificationParserAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Count expected requirements (paragraphs separated by blank lines)
    paragraphs = [p.strip() for p in spec_text.split('\n\n') if p.strip()]
    expected_min_requirements = len(paragraphs)
    
    # Mock LLM response for segmentation
    mock_requirements = paragraphs  # Use the paragraphs as requirements
    mock_segmentation_response = json.dumps({
        "requirements": mock_requirements
    })
    
    # Mock LLM response for categorization
    mock_categorization_response = json.dumps({
        "category": "functional",
        "entities": ["signal1", "signal2"]
    })
    
    # Mock call_groq to return appropriate responses
    call_count = 0
    async def mock_call_groq(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_segmentation_response
        else:
            return mock_categorization_response
    
    agent.call_groq = mock_call_groq
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "specification_text": spec_text,
            "specification_id": str(ObjectId())
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully extract requirements
    assert result.success, f"Agent failed: {result.error}"
    assert "requirements" in result.data
    
    # Property: Must extract at least as many requirements as paragraphs
    extracted_requirements = result.data["requirements"]
    assert len(extracted_requirements) >= expected_min_requirements, \
        f"Expected at least {expected_min_requirements} requirements, got {len(extracted_requirements)}"
    
    # Property: Each requirement must have required fields
    for req in extracted_requirements:
        assert "requirement_id" in req
        assert "text" in req
        assert "category" in req
        assert "temporal_keywords" in req
        assert "entities" in req
        
        # Property: Requirement ID must follow format REQ-XXX
        assert req["requirement_id"].startswith("REQ-")
        
        # Property: Text must not be empty
        assert len(req["text"]) > 0
        
        # Property: Category must be valid
        assert req["category"] in ["functional", "timing", "safety", "liveness"]
        
        # Property: Lists must be lists
        assert isinstance(req["temporal_keywords"], list)
        assert isinstance(req["entities"], list)


if __name__ == "__main__":
    print("Run with: pytest tests/test_spec_parser_properties.py -v")


@pytest.mark.asyncio
@given(
    temporal_keyword=st.sampled_from([
        "within", "before", "after", "until", "always", "eventually",
        "never", "whenever", "immediately", "next", "cycles", "clock"
    ])
)
@settings(max_examples=100, deadline=None)
async def test_temporal_keyword_detection(temporal_keyword):
    """
    Property 5: Temporal Keyword Detection
    
    Universal Property:
    For any requirement text containing a temporal keyword K,
    the parser must detect K in the temporal_keywords list.
    
    Validates: Requirements 3.2
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.specifications = AsyncMock()
    mock_db.specifications.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = SpecificationParserAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Create requirement text with the temporal keyword
    requirement_text = f"The signal must respond {temporal_keyword} 5 cycles"
    spec_text = requirement_text
    
    # Mock LLM response for segmentation
    mock_segmentation_response = json.dumps({
        "requirements": [requirement_text]
    })
    
    # Mock LLM response for categorization
    mock_categorization_response = json.dumps({
        "category": "timing",
        "entities": ["signal"]
    })
    
    # Mock call_groq to return appropriate responses
    call_count = 0
    async def mock_call_groq(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_segmentation_response
        else:
            return mock_categorization_response
    
    agent.call_groq = mock_call_groq
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "specification_text": spec_text,
            "specification_id": str(ObjectId())
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully extract requirements
    assert result.success, f"Agent failed: {result.error}"
    assert "requirements" in result.data
    
    # Property: Must detect the temporal keyword
    extracted_requirements = result.data["requirements"]
    assert len(extracted_requirements) > 0
    
    req = extracted_requirements[0]
    assert "temporal_keywords" in req
    
    # Property: The temporal keyword must be detected
    assert temporal_keyword in req["temporal_keywords"], \
        f"Temporal keyword '{temporal_keyword}' not detected in {req['temporal_keywords']}"


@pytest.mark.asyncio
@given(
    entity_name=st.sampled_from(["valid", "ready", "enable", "data", "req", "ack", "clk", "rst_n"])
)
@settings(max_examples=100, deadline=None)
async def test_entity_extraction_completeness(entity_name):
    """
    Property 7: Entity Extraction Completeness
    
    Universal Property:
    For any requirement text containing an entity name E,
    the parser must extract E in the entities list.
    
    Validates: Requirements 3.4
    """
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.specifications = AsyncMock()
    mock_db.specifications.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = SpecificationParserAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Create requirement text with the entity
    requirement_text = f"When {entity_name} is asserted, the system must respond"
    spec_text = requirement_text
    
    # Mock LLM response for segmentation
    mock_segmentation_response = json.dumps({
        "requirements": [requirement_text]
    })
    
    # Mock LLM response for categorization - include the entity
    mock_categorization_response = json.dumps({
        "category": "functional",
        "entities": [entity_name, "system"]
    })
    
    # Mock call_groq to return appropriate responses
    call_count = 0
    async def mock_call_groq(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return mock_segmentation_response
        else:
            return mock_categorization_response
    
    agent.call_groq = mock_call_groq
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "specification_text": spec_text,
            "specification_id": str(ObjectId())
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully extract requirements
    assert result.success, f"Agent failed: {result.error}"
    assert "requirements" in result.data
    
    # Property: Must extract entities
    extracted_requirements = result.data["requirements"]
    assert len(extracted_requirements) > 0
    
    req = extracted_requirements[0]
    assert "entities" in req
    assert isinstance(req["entities"], list)
    
    # Property: The entity must be extracted
    assert entity_name in req["entities"], \
        f"Entity '{entity_name}' not extracted from requirement. Found: {req['entities']}"
