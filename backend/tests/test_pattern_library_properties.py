"""
Property-Based Tests for Pattern Library

Tests universal properties that must hold for pattern library operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.utils.pattern_library import (
    search_patterns, adapt_pattern, get_pattern_by_id, 
    get_all_patterns, increment_usage
)


@pytest.mark.asyncio
@given(
    keyword=st.sampled_from(["handshake", "valid", "ready", "fifo", "reset", "mutex", "stable"])
)
@settings(max_examples=100, deadline=None)
async def test_pattern_query_execution(keyword):
    """
    Property 27: Pattern Library Query Execution
    
    Universal Property:
    For any valid keyword query, the pattern search must:
    1. Return results without error
    2. Return patterns that contain the keyword
    3. Sort results by relevance
    
    Validates: Requirements 11.1
    """
    # Execute pattern search
    results = search_patterns([keyword])
    
    # Property: Search must return a list
    assert isinstance(results, list)
    
    # Property: If results exist, they must contain the keyword
    for pattern in results:
        assert "keywords" in pattern
        assert "relevance_score" in pattern
        
        # Check if keyword appears in pattern keywords
        pattern_keywords = [kw.lower() for kw in pattern["keywords"]]
        keyword_lower = keyword.lower()
        
        found = any(keyword_lower in pk or pk in keyword_lower for pk in pattern_keywords)
        assert found, f"Keyword '{keyword}' not found in pattern keywords: {pattern['keywords']}"
    
    # Property: Results must be sorted by relevance (descending)
    if len(results) > 1:
        for i in range(len(results) - 1):
            assert results[i]["relevance_score"] >= results[i+1]["relevance_score"], \
                "Results not sorted by relevance score"


@pytest.mark.asyncio
@given(
    category=st.sampled_from(["protocol", "safety", "liveness", "timing", "functional"])
)
@settings(max_examples=100, deadline=None)
async def test_pattern_category_filter(category):
    """
    Test that category filtering works correctly.
    
    Part of Property 27: Pattern Library Query Execution
    """
    # Search with category filter
    results = search_patterns(["signal"], category=category)
    
    # Property: All results must match the category
    for pattern in results:
        assert "category" in pattern
        assert pattern["category"] == category, \
            f"Expected category '{category}', got '{pattern['category']}'"


@pytest.mark.asyncio
async def test_pattern_template_adaptation():
    """
    Property 28: Pattern Template Adaptation
    
    Universal Property:
    For any pattern template with parameters, adaptation must:
    1. Replace all parameter placeholders
    2. Include requirement ID for traceability
    3. Produce valid SVA syntax structure
    
    Validates: Requirements 11.2
    """
    # Get a pattern
    pattern = get_pattern_by_id("handshake_req_ack")
    assert pattern is not None
    
    # Define parameters
    parameters = {
        "clock": "clk",
        "reset": "rst_n",
        "req_signal": "request",
        "ack_signal": "acknowledge",
        "max_cycles": "5"
    }
    
    # Adapt the pattern
    adapted_code = adapt_pattern(
        pattern=pattern,
        parameters=parameters,
        requirement_id="REQ-001",
        description="Test handshake requirement"
    )
    
    # Property: Adapted code must be a string
    assert isinstance(adapted_code, str)
    assert len(adapted_code) > 0
    
    # Property: Must include requirement ID
    assert "REQ-001" in adapted_code
    
    # Property: Must include description
    assert "Test handshake requirement" in adapted_code
    
    # Property: Must replace all parameters
    for param_name, param_value in parameters.items():
        # Check that placeholder is replaced
        assert f"{{{param_name}}}" not in adapted_code, \
            f"Parameter placeholder '{param_name}' not replaced"
        # Check that value appears in code
        assert param_value in adapted_code, \
            f"Parameter value '{param_value}' not found in adapted code"
    
    # Property: Must contain SVA keywords
    assert "assert property" in adapted_code
    assert "@(posedge" in adapted_code


@pytest.mark.asyncio
@given(
    pattern_id=st.sampled_from([
        "handshake_req_ack", "valid_ready_handshake", "mutual_exclusion",
        "eventual_response", "stable_until", "fifo_not_full_on_push"
    ])
)
@settings(max_examples=100, deadline=None)
async def test_pattern_retrieval_by_id(pattern_id):
    """
    Test that patterns can be retrieved by ID.
    
    Part of Property 27: Pattern Library Query Execution
    """
    # Retrieve pattern
    pattern = get_pattern_by_id(pattern_id)
    
    # Property: Must return a pattern
    assert pattern is not None
    assert isinstance(pattern, dict)
    
    # Property: Must have required fields
    assert "pattern_id" in pattern
    assert "name" in pattern
    assert "description" in pattern
    assert "template" in pattern
    assert "parameters" in pattern
    assert "keywords" in pattern
    
    # Property: Pattern ID must match
    assert pattern["pattern_id"] == pattern_id


@pytest.mark.asyncio
async def test_pattern_usage_tracking():
    """
    Property 29: Pattern Usage Tracking
    
    Universal Property:
    When a pattern is used, its usage count must increment.
    
    Validates: Requirements 11.4
    """
    pattern_id = "handshake_req_ack"
    
    # Get initial usage count
    pattern_before = get_pattern_by_id(pattern_id)
    initial_count = pattern_before["usage_count"]
    
    # Increment usage
    increment_usage(pattern_id)
    
    # Get updated usage count
    pattern_after = get_pattern_by_id(pattern_id)
    final_count = pattern_after["usage_count"]
    
    # Property: Usage count must increment by 1
    assert final_count == initial_count + 1, \
        f"Expected usage count to increment from {initial_count} to {initial_count + 1}, got {final_count}"


@pytest.mark.asyncio
async def test_all_patterns_have_required_fields():
    """
    Test that all patterns in the library have required fields.
    """
    patterns = get_all_patterns()
    
    # Property: Must have patterns
    assert len(patterns) > 0
    
    # Property: Each pattern must have required fields
    required_fields = ["pattern_id", "name", "description", "category", 
                      "keywords", "template", "parameters", "usage_count"]
    
    for pattern in patterns:
        for field in required_fields:
            assert field in pattern, \
                f"Pattern '{pattern.get('pattern_id', 'unknown')}' missing field '{field}'"
        
        # Property: Keywords must be a list
        assert isinstance(pattern["keywords"], list)
        assert len(pattern["keywords"]) > 0
        
        # Property: Parameters must be a list
        assert isinstance(pattern["parameters"], list)
        
        # Property: Template must contain placeholders for parameters
        template = pattern["template"]
        for param in pattern["parameters"]:
            # Check if parameter appears in template (as {param})
            assert f"{{{param}}}" in template, \
                f"Parameter '{param}' not found in template for pattern '{pattern['pattern_id']}'"


if __name__ == "__main__":
    print("Run with: pytest tests/test_pattern_library_properties.py -v")
