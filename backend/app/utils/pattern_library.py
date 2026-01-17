"""
Pattern Library Utilities

Manages a library of common SystemVerilog assertion patterns.
Provides pattern matching and template adaptation functionality.
Includes caching for improved performance.
"""
from typing import List, Dict, Any, Optional
import logging
from app.utils.cache import pattern_cache, cached

logger = logging.getLogger(__name__)


# Common assertion patterns
ASSERTION_PATTERNS = [
    {
        "pattern_id": "handshake_req_ack",
        "name": "Request-Acknowledge Handshake",
        "description": "A request signal must be followed by an acknowledge within N cycles",
        "category": "protocol",
        "keywords": ["request", "acknowledge", "handshake", "req", "ack"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {req_signal} |-> ##[1:{max_cycles}] {ack_signal}
);""",
        "parameters": ["clock", "reset", "req_signal", "ack_signal", "max_cycles"],
        "usage_count": 0
    },
    {
        "pattern_id": "valid_ready_handshake",
        "name": "Valid-Ready Handshake",
        "description": "Valid-ready protocol for data transfer",
        "category": "protocol",
        "keywords": ["valid", "ready", "handshake", "transfer"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {valid_signal} && {ready_signal} |-> ##1 $stable({data_signal})
);""",
        "parameters": ["clock", "reset", "valid_signal", "ready_signal", "data_signal"],
        "usage_count": 0
    },
    {
        "pattern_id": "mutual_exclusion",
        "name": "Mutual Exclusion",
        "description": "Two signals must never be high at the same time",
        "category": "safety",
        "keywords": ["mutex", "exclusive", "never", "both"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    not ({signal1} && {signal2})
);""",
        "parameters": ["clock", "reset", "signal1", "signal2"],
        "usage_count": 0
    },
    {
        "pattern_id": "eventual_response",
        "name": "Eventual Response",
        "description": "A trigger signal must eventually cause a response",
        "category": "liveness",
        "keywords": ["eventually", "always", "response", "trigger"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {trigger_signal} |-> ##[1:$] {response_signal}
);""",
        "parameters": ["clock", "reset", "trigger_signal", "response_signal"],
        "usage_count": 0
    },
    {
        "pattern_id": "stable_until",
        "name": "Stable Until",
        "description": "A signal must remain stable until a condition occurs",
        "category": "timing",
        "keywords": ["stable", "until", "hold", "maintain"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {signal} |-> $stable({signal}) until {condition}
);""",
        "parameters": ["clock", "reset", "signal", "condition"],
        "usage_count": 0
    },
    {
        "pattern_id": "fifo_not_full_on_push",
        "name": "FIFO Not Full on Push",
        "description": "FIFO must not be full when pushing data",
        "category": "safety",
        "keywords": ["fifo", "full", "push", "write"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {push_signal} |-> !{full_signal}
);""",
        "parameters": ["clock", "reset", "push_signal", "full_signal"],
        "usage_count": 0
    },
    {
        "pattern_id": "fifo_not_empty_on_pop",
        "name": "FIFO Not Empty on Pop",
        "description": "FIFO must not be empty when popping data",
        "category": "safety",
        "keywords": ["fifo", "empty", "pop", "read"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {pop_signal} |-> !{empty_signal}
);""",
        "parameters": ["clock", "reset", "pop_signal", "empty_signal"],
        "usage_count": 0
    },
    {
        "pattern_id": "reset_behavior",
        "name": "Reset Behavior",
        "description": "Signal must be in known state after reset",
        "category": "functional",
        "keywords": ["reset", "initial", "state"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock})
    !{reset} |-> ##1 {signal} == {reset_value}
);""",
        "parameters": ["clock", "reset", "signal", "reset_value"],
        "usage_count": 0
    },
    {
        "pattern_id": "one_hot_encoding",
        "name": "One-Hot Encoding",
        "description": "Exactly one bit must be high in a one-hot encoded signal",
        "category": "functional",
        "keywords": ["one-hot", "onehot", "encoding"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    $onehot({signal})
);""",
        "parameters": ["clock", "reset", "signal"],
        "usage_count": 0
    },
    {
        "pattern_id": "bounded_response",
        "name": "Bounded Response Time",
        "description": "Response must occur within N cycles of trigger",
        "category": "timing",
        "keywords": ["within", "cycles", "bounded", "timeout"],
        "template": """// Validates: {requirement_id}
// {description}
assert property (@(posedge {clock}) disable iff (!{reset})
    {trigger_signal} |-> ##[1:{max_cycles}] {response_signal}
);""",
        "parameters": ["clock", "reset", "trigger_signal", "response_signal", "max_cycles"],
        "usage_count": 0
    }
]


def get_all_patterns() -> List[Dict[str, Any]]:
    """
    Get all available assertion patterns.
    
    Returns:
        List of pattern dictionaries
    """
    return ASSERTION_PATTERNS.copy()


@cached(pattern_cache, ttl=3600, key_prefix="patterns")
def search_patterns(keywords: List[str], category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for patterns matching keywords and category with caching.
    
    Args:
        keywords: List of keywords to search for
        category: Optional category filter
        
    Returns:
        List of matching patterns, sorted by relevance
        
    Validates: Requirement 17.4 - Cache pattern library queries
    """
    matching_patterns = []
    
    for pattern in ASSERTION_PATTERNS:
        # Check category match
        if category and pattern["category"] != category:
            continue
        
        # Calculate relevance score
        score = 0
        pattern_keywords = pattern["keywords"]
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for pattern_keyword in pattern_keywords:
                if keyword_lower in pattern_keyword or pattern_keyword in keyword_lower:
                    score += 1
        
        if score > 0:
            matching_patterns.append({
                **pattern,
                "relevance_score": score
            })
    
    # Sort by relevance score (descending)
    matching_patterns.sort(key=lambda p: p["relevance_score"], reverse=True)
    
    return matching_patterns


def adapt_pattern(pattern: Dict[str, Any], parameters: Dict[str, str], 
                 requirement_id: str, description: str) -> str:
    """
    Adapt a pattern template with specific parameters.
    
    Args:
        pattern: Pattern dictionary
        parameters: Dictionary mapping parameter names to values
        requirement_id: Requirement ID for traceability
        description: Description for the assertion
        
    Returns:
        Adapted assertion code
    """
    template = pattern["template"]
    
    # Add requirement_id and description to parameters
    all_params = {
        **parameters,
        "requirement_id": requirement_id,
        "description": description
    }
    
    # Replace placeholders in template
    try:
        adapted_code = template.format(**all_params)
        return adapted_code
    except KeyError as e:
        logger.error(f"Missing parameter for pattern adaptation: {e}")
        # Return template with missing parameters highlighted
        return template


def increment_usage(pattern_id: str):
    """
    Increment the usage count for a pattern.
    
    Args:
        pattern_id: Pattern ID
    """
    for pattern in ASSERTION_PATTERNS:
        if pattern["pattern_id"] == pattern_id:
            pattern["usage_count"] += 1
            break


def get_pattern_by_id(pattern_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a pattern by its ID.
    
    Args:
        pattern_id: Pattern ID
        
    Returns:
        Pattern dictionary or None
    """
    for pattern in ASSERTION_PATTERNS:
        if pattern["pattern_id"] == pattern_id:
            return pattern.copy()
    return None


async def seed_pattern_library(db):
    """
    Seed the database with initial assertion patterns.
    
    Args:
        db: Database instance
    """
    try:
        # Check if patterns already exist
        existing_count = await db.pattern_library.count_documents({})
        
        if existing_count > 0:
            logger.info(f"Pattern library already seeded with {existing_count} patterns")
            return
        
        # Insert all patterns
        for pattern in ASSERTION_PATTERNS:
            await db.pattern_library.insert_one(pattern.copy())
        
        logger.info(f"Seeded pattern library with {len(ASSERTION_PATTERNS)} patterns")
        
    except Exception as e:
        logger.error(f"Error seeding pattern library: {str(e)}")
        raise
