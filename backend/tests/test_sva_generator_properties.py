"""
Property-based tests for SVA Generator Agent

These tests validate universal correctness properties for assertion generation.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck, assume
from app.agents.sva_generator import SVAGeneratorAgent
from app.agents.base import PipelineContext
from app.clients.groq_client import GroqClient
from app.utils.sva_validator import validate_sva_syntax, extract_clock_signal, extract_reset_signal
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
import json

# Suppress function_scoped_fixture health check
settings.register_profile("default", suppress_health_check=[HealthCheck.function_scoped_fixture])
settings.load_profile("default")


# Strategy for generating valid requirement dictionaries
@st.composite
def requirement_strategy(draw):
    """Generate a valid requirement dictionary"""
    req_id = f"REQ-{draw(st.integers(min_value=1, max_value=999))}"
    
    # Generate requirement text with optional temporal keywords
    temporal_keywords = draw(st.lists(
        st.sampled_from(['after', 'within', 'before', 'eventually', 'always', 'until']),
        max_size=3
    ))
    
    entities = draw(st.lists(
        st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll')), min_size=3, max_size=10),
        min_size=1,
        max_size=5
    ))
    
    categories = ['timing', 'functional', 'protocol', 'safety', 'liveness']
    category = draw(st.sampled_from(categories))
    
    # Build requirement text
    if temporal_keywords:
        req_text = f"When {entities[0]} is asserted, {entities[1] if len(entities) > 1 else 'signal'} must respond {temporal_keywords[0]} 5 cycles"
    else:
        req_text = f"The {entities[0]} signal must be valid when {entities[1] if len(entities) > 1 else 'enable'} is high"
    
    return {
        "requirement_id": req_id,
        "text": req_text,
        "category": category,
        "temporal_keywords": temporal_keywords,
        "entities": entities
    }


@pytest.mark.asyncio
@given(requirement=requirement_strategy())
@settings(max_examples=100, deadline=None)
async def test_property_18_sva_syntax_validity(requirement):
    """
    Feature: sva-chatbot, Property 18: SVA Syntax Validity
    
    For any generated assertion code, parsing it with a SystemVerilog parser
    should succeed without syntax errors.
    
    Validates: Requirements 6.6, 7.1
    """
    # Mock database for property tests - use MagicMock to avoid "assertions" attribute issue
    mock_db = MagicMock()
    mock_assertions_collection = AsyncMock()
    mock_assertions_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=ObjectId()))
    mock_db.assertions = mock_assertions_collection
    mock_db.agent_executions = AsyncMock()
    mock_db.agent_executions.insert_one = AsyncMock()
    
    # Mock LLM response with valid SVA code
    assertion_type = "concurrent" if requirement["temporal_keywords"] else "immediate"
    
    if assertion_type == "concurrent":
        mock_sva_code = f"""// Validates: {requirement['requirement_id']}
assert property (@(posedge clk) disable iff (!rst_n)
    {requirement['entities'][0]} |-> ##[1:5] {requirement['entities'][1] if len(requirement['entities']) > 1 else 'ready'}
);"""
    else:
        mock_sva_code = f"""// Validates: {requirement['requirement_id']}
assert ({requirement['entities'][0]} && enable |-> valid);"""
    
    mock_llm_response = json.dumps({
        "code": mock_sva_code,
        "module": "test_module",
        "signals": requirement["entities"],
        "confidence": 0.85,
        "explanation": f"Verifies {requirement['text']}"
    })
    
    # Mock Groq client
    mock_groq_client = AsyncMock(spec=GroqClient)
    mock_groq_client.chat_completion_with_fallback = AsyncMock(return_value={
        "choices": [{"message": {"content": mock_llm_response}}],
        "usage": {"total_tokens": 100}
    })
    
    # Create agent
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock the call_groq method to return our mock response
    agent.call_groq = AsyncMock(return_value=mock_llm_response)
    
    # Create context with requirement
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [requirement],
            "rtl_context": {
                "modules": [{
                    "name": "test_module",
                    "signals": [{"name": sig} for sig in requirement["entities"]],
                    "clocks": ["clk"],
                    "resets": ["rst_n"]
                }],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Verify execution succeeded
    assert result.success, f"Agent execution should succeed: {result.error}"
    assert "assertions" in result.data, "Result should contain assertions"
    
    # Verify all generated assertions have valid syntax
    for assertion in result.data["assertions"]:
        sva_code = assertion["assertion_code"]
        
        # Validate syntax
        is_valid, error_msg = validate_sva_syntax(sva_code)
        
        assert is_valid, f"Generated assertion should have valid SVA syntax. Error: {error_msg}\nCode: {sva_code}"
        
        # Additional checks
        assert sva_code.strip(), "Assertion code should not be empty"
        assert "assert" in sva_code.lower(), "Assertion should contain 'assert' keyword"


@pytest.mark.asyncio
@given(
    requirement=requirement_strategy(),
    clock_name=st.sampled_from(['clk', 'clock', 'sys_clk', 'axi_clk']),
    reset_name=st.sampled_from(['rst_n', 'reset_n', 'sys_rst_n', 'arst_n'])
)
@settings(max_examples=100, deadline=None)
async def test_property_16_clock_reset_reference_correctness(requirement, clock_name, reset_name):
    """
    Feature: sva-chatbot, Property 16: Clock and Reset Reference Correctness
    
    For any generated concurrent assertion, it should reference a clock signal
    from the target RTL module, and if the module has a reset, the assertion
    should handle reset appropriately.
    
    Validates: Requirements 6.4
    """
    # Only test concurrent assertions (temporal requirements)
    assume(len(requirement["temporal_keywords"]) > 0)
    
    # Mock database for property tests - use MagicMock to avoid "assertions" attribute issue
    mock_db = MagicMock()
    mock_assertions_collection = AsyncMock()
    mock_assertions_collection.insert_one = AsyncMock(return_value=AsyncMock(inserted_id=ObjectId()))
    mock_db.assertions = mock_assertions_collection
    mock_db.agent_executions = AsyncMock()
    mock_db.agent_executions.insert_one = AsyncMock()
    
    # Mock LLM response with clock and reset references
    mock_sva_code = f"""// Validates: {requirement['requirement_id']}
assert property (@(posedge {clock_name}) disable iff (!{reset_name})
    {requirement['entities'][0]} |-> ##[1:5] {requirement['entities'][1] if len(requirement['entities']) > 1 else 'ready'}
);"""
    
    mock_llm_response = json.dumps({
        "code": mock_sva_code,
        "module": "test_module",
        "signals": requirement["entities"] + [clock_name, reset_name],
        "confidence": 0.85,
        "explanation": f"Verifies {requirement['text']}"
    })
    
    # Mock Groq client
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create agent
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock the call_groq method
    agent.call_groq = AsyncMock(return_value=mock_llm_response)
    
    # Create context with specific clock and reset
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [requirement],
            "rtl_context": {
                "modules": [{
                    "name": "test_module",
                    "signals": [{"name": sig} for sig in requirement["entities"]],
                    "clocks": [clock_name],
                    "resets": [reset_name]
                }],
                "default_clock": clock_name,
                "default_reset": reset_name
            }
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Verify execution succeeded
    assert result.success, f"Agent execution should succeed: {result.error}"
    assert "assertions" in result.data, "Result should contain assertions"
    
    # Verify clock and reset references
    for assertion in result.data["assertions"]:
        sva_code = assertion["assertion_code"]
        
        # Check for clock reference
        extracted_clock = extract_clock_signal(sva_code)
        assert extracted_clock, f"Concurrent assertion should reference a clock signal. Code: {sva_code}"
        assert extracted_clock == clock_name, \
            f"Assertion should reference the correct clock signal '{clock_name}', found '{extracted_clock}'"
        
        # Check for reset handling (if reset is present in module)
        extracted_reset = extract_reset_signal(sva_code)
        assert extracted_reset, f"Assertion should handle reset signal. Code: {sva_code}"
        assert reset_name in extracted_reset or extracted_reset in reset_name, \
            f"Assertion should reference the correct reset signal '{reset_name}', found '{extracted_reset}'"


@pytest.mark.asyncio
async def test_sva_generator_basic_functionality(test_db):
    """
    Test basic SVA generator functionality with a simple requirement
    """
    # Await the test_db fixture
    db = await test_db
    
    # Create a simple requirement
    requirement = {
        "requirement_id": "REQ-001",
        "text": "When valid is high, ready must be asserted within 5 cycles",
        "category": "timing",
        "temporal_keywords": ["within"],
        "entities": ["valid", "ready"]
    }
    
    # Mock LLM response
    mock_sva_code = """// Validates: REQ-001
assert property (@(posedge clk) disable iff (!rst_n)
    valid |-> ##[1:5] ready
);"""
    
    mock_llm_response = json.dumps({
        "code": mock_sva_code,
        "module": "handshake",
        "signals": ["valid", "ready", "clk", "rst_n"],
        "confidence": 0.92,
        "explanation": "Verifies that ready responds within 5 cycles when valid is asserted"
    })
    
    # Mock Groq client
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create agent
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=db)
    
    # Mock the call_groq method
    agent.call_groq = AsyncMock(return_value=mock_llm_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [requirement],
            "rtl_context": {
                "modules": [{
                    "name": "handshake",
                    "signals": [
                        {"name": "valid"},
                        {"name": "ready"},
                        {"name": "clk"},
                        {"name": "rst_n"}
                    ],
                    "clocks": ["clk"],
                    "resets": ["rst_n"]
                }],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Verify result
    assert result.success, f"Agent execution should succeed: {result.error}"
    assert result.agent_name == "SVAGenerator"
    assert "assertions" in result.data
    assert result.data["count"] == 1
    
    # Verify assertion details
    assertion = result.data["assertions"][0]
    assert assertion["requirement_id"] == "REQ-001"
    assert assertion["assertion_type"] == "concurrent"
    assert assertion["category"] == "timing"
    assert "valid" in assertion["assertion_code"]
    assert "ready" in assertion["assertion_code"]
    assert assertion["confidence_score"] > 0.0
    assert assertion["confidence_score"] <= 1.0
    
    # Verify traceability
    assert "traceability" in assertion
    assert assertion["traceability"]["requirement_text"] == requirement["text"]
    assert "valid" in assertion["traceability"]["rtl_signals"]
    assert "ready" in assertion["traceability"]["rtl_signals"]


@pytest.mark.asyncio
async def test_sva_generator_immediate_assertion(test_db):
    """
    Test SVA generator creates immediate assertions for non-temporal requirements
    """
    # Await the test_db fixture
    db = await test_db
    
    # Create a non-temporal requirement
    requirement = {
        "requirement_id": "REQ-002",
        "text": "When enable is high, data must be valid",
        "category": "functional",
        "temporal_keywords": [],  # No temporal keywords
        "entities": ["enable", "data", "valid"]
    }
    
    # Mock LLM response with immediate assertion
    mock_sva_code = """// Validates: REQ-002
assert (enable && data |-> valid);"""
    
    mock_llm_response = json.dumps({
        "code": mock_sva_code,
        "module": "data_path",
        "signals": ["enable", "data", "valid"],
        "confidence": 0.88,
        "explanation": "Verifies data validity when enable is high"
    })
    
    # Mock Groq client
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create agent
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=db)
    
    # Mock the call_groq method
    agent.call_groq = AsyncMock(return_value=mock_llm_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [requirement],
            "rtl_context": {
                "modules": [{
                    "name": "data_path",
                    "signals": [
                        {"name": "enable"},
                        {"name": "data"},
                        {"name": "valid"}
                    ],
                    "clocks": ["clk"],
                    "resets": ["rst_n"]
                }],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Verify result
    assert result.success
    assert len(result.data["assertions"]) == 1
    
    # Verify assertion type
    assertion = result.data["assertions"][0]
    assert assertion["assertion_type"] == "immediate", \
        "Non-temporal requirement should generate immediate assertion"
    
    # Verify syntax
    is_valid, error_msg = validate_sva_syntax(assertion["assertion_code"])
    assert is_valid, f"Immediate assertion should have valid syntax: {error_msg}"


@pytest.mark.asyncio
async def test_sva_generator_empty_requirements(test_db):
    """
    Test SVA generator handles empty requirements gracefully
    """
    # Await the test_db fixture
    db = await test_db
    
    # Mock Groq client
    mock_groq_client = AsyncMock(spec=GroqClient)
    
    # Create agent
    agent = SVAGeneratorAgent(groq_client=mock_groq_client, db=db)
    
    # Create context with no requirements
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "requirements": [],
            "rtl_context": {
                "modules": [],
                "default_clock": "clk",
                "default_reset": "rst_n"
            }
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Verify result
    assert result.success, "Agent should succeed even with no requirements"
    assert result.data["assertions"] == []
    # The count field is only added when there are requirements processed
    # For empty requirements, we just check assertions is empty
