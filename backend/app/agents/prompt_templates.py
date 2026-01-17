"""
Advanced Prompt Templates for Multi-Agent Pipeline

This module provides sophisticated prompt templates for each agent with:
- Clear role definitions and expertise framing
- Few-shot examples demonstrating desired behavior
- Chain-of-thought prompting for complex reasoning
- Structured output enforcement (JSON mode)
- Context-aware prompt construction
- Intelligent context window management

Implements Requirements 3.1, 3.2, 3.3, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 6.1, 6.2, 7.2, 7.3
"""
from typing import Dict, List, Any, Optional
import json
from app.agents.context_manager import context_manager


class PromptTemplate:
    """Base class for prompt templates with common utilities"""
    
    @staticmethod
    def format_json_schema(schema: Dict[str, Any]) -> str:
        """Format JSON schema for output enforcement"""
        return json.dumps(schema, indent=2)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 2000) -> str:
        """Truncate text to fit within context window"""
        return context_manager.truncate_text(text, max_length)


class SpecificationParserPrompts(PromptTemplate):
    """
    Advanced prompts for Specification Parser Agent
    
    Validates: Requirements 3.1, 3.2, 3.3, 3.4
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """
        System prompt with role definition and expertise framing
        
        Returns:
            System prompt string
        """
        return """You are an expert Requirements Engineer specializing in hardware verification specifications.

Your expertise includes:
- Extracting structured requirements from natural language documents
- Identifying temporal constraints and timing relationships
- Categorizing requirements by type (functional, timing, safety, liveness)
- Recognizing hardware entities (signals, modules, states, protocols)
- Detecting ambiguities and incomplete specifications

Your responses must be:
- Precise and technically accurate
- Structured as valid JSON
- Complete without omitting requirements
- Consistent in categorization

You follow IEEE standards for requirements engineering and understand hardware verification terminology."""
    
    @staticmethod
    def get_segmentation_prompt(spec_text: str) -> str:
        """
        Prompt for requirement segmentation with few-shot examples
        Uses context manager for intelligent text handling
        
        Args:
            spec_text: Specification text to segment
            
        Returns:
            User prompt string
        """
        # Use context manager to prepare specification text
        prepared_text = context_manager.prepare_specification_context(spec_text, max_chars=3000)
        
        return f"""Extract individual requirements from the specification document.

TASK: Segment the specification into atomic, testable requirements.

GUIDELINES:
1. Each requirement must be a complete, standalone statement
2. Split compound requirements (containing "and", "or") into separate items
3. Preserve original wording - do not paraphrase
4. Number requirements sequentially
5. Include all requirements - do not omit any

FEW-SHOT EXAMPLES:

Example 1 - Input:
"The FIFO must accept data when not full and the write enable is high. The FIFO must output data when not empty and read enable is high."

Example 1 - Output:
{{
  "requirements": [
    "The FIFO must accept data when not full and the write enable is high",
    "The FIFO must output data when not empty and read enable is high"
  ]
}}

Example 2 - Input:
"When the handshake request signal is asserted, the acknowledge signal must be asserted within 5 clock cycles, and the data must remain stable during this period."

Example 2 - Output:
{{
  "requirements": [
    "When the handshake request signal is asserted, the acknowledge signal must be asserted within 5 clock cycles",
    "The data must remain stable during the handshake period"
  ]
}}

SPECIFICATION TO ANALYZE:
{prepared_text}

OUTPUT FORMAT (JSON only):
{{
  "requirements": [
    "requirement 1 text",
    "requirement 2 text"
  ]
}}

Return ONLY valid JSON. No additional text or explanation."""
    
    @staticmethod
    def get_categorization_prompt(requirement_text: str) -> str:
        """
        Prompt for requirement categorization with chain-of-thought reasoning
        
        Args:
            requirement_text: Single requirement to categorize
            
        Returns:
            User prompt string
        """
        return f"""Analyze this hardware requirement using chain-of-thought reasoning.

REQUIREMENT: {requirement_text}

ANALYSIS STEPS:

Step 1 - Identify Temporal Keywords:
Look for: within, before, after, until, always, eventually, never, whenever, immediately, next, cycles, simultaneously, followed by, preceded by, during

Step 2 - Categorize Requirement:
- FUNCTIONAL: Basic behavior (if X then Y), no timing constraints
  Example: "When enable is high, output must equal input"
- TIMING: Temporal constraints with specific cycle counts or ordering
  Example: "Acknowledge must arrive within 5 cycles of request"
- SAFETY: Something bad never happens (never, must not, shall not)
  Example: "Read and write must never be asserted simultaneously"
- LIVENESS: Something good eventually happens (eventually, always)
  Example: "Every request must eventually receive an acknowledge"

Step 3 - Extract Entities:
Identify: signal names, module names, state names, port names, protocol names

Step 4 - Reasoning:
Explain your categorization choice based on the keywords and structure.

FEW-SHOT EXAMPLE:

Requirement: "The acknowledge signal must be asserted within 3 clock cycles after the request signal is asserted"

Reasoning:
- Temporal keywords found: "within", "after", "clock cycles"
- Contains specific timing constraint (3 cycles)
- Describes ordering relationship (request before acknowledge)
- Category: TIMING
- Entities: acknowledge, request

Output:
{{
  "temporal_keywords": ["within", "after", "clock cycles"],
  "category": "timing",
  "entities": ["acknowledge", "request"],
  "reasoning": "Contains explicit timing constraint with cycle count and temporal ordering"
}}

NOW ANALYZE THE REQUIREMENT ABOVE.

OUTPUT FORMAT (JSON only):
{{
  "temporal_keywords": ["keyword1", "keyword2"],
  "category": "functional|timing|safety|liveness",
  "entities": ["entity1", "entity2"],
  "reasoning": "brief explanation of categorization"
}}

Return ONLY valid JSON."""


class RTLAnalyzerPrompts(PromptTemplate):
    """
    Advanced prompts for RTL Analyzer Agent
    
    Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """System prompt for RTL analysis"""
        return """You are an expert Hardware Design Engineer specializing in SystemVerilog RTL analysis.

Your expertise includes:
- Understanding SystemVerilog syntax and semantics
- Identifying clock and reset signals by naming conventions and usage patterns
- Recognizing finite state machines (FSMs) and extracting state definitions
- Detecting common hardware protocols (handshake, FIFO, AXI, APB, AHB)
- Building signal dependency relationships
- Understanding hardware design patterns and best practices

Your responses must be:
- Technically accurate for hardware designs
- Structured as valid JSON
- Complete in identifying all relevant patterns
- Precise in signal and module identification

You understand both synthesizable RTL and verification constructs."""
    
    @staticmethod
    def get_semantic_analysis_prompt(module_name: str, module_code: str, 
                                    signal_names: List[str]) -> str:
        """
        Prompt for semantic RTL analysis with structured reasoning
        Uses context manager for code handling
        
        Args:
            module_name: Name of the module
            module_code: Module source code
            signal_names: List of signal names
            
        Returns:
            User prompt string
        """
        # Use context manager to prepare RTL code
        prepared_code = context_manager.prepare_rtl_context(module_code, module_name, max_chars=2500)
        signals_str = ', '.join(signal_names[:30])
        
        return f"""Analyze this SystemVerilog module for semantic patterns and structures.

MODULE: {module_name}
SIGNALS: {signals_str}

CODE:
{prepared_code}

ANALYSIS TASKS:

Task 1 - State Machine Detection:
Look for:
- Case statements with state variables
- Enum type definitions for states
- Always blocks with state transitions
- State register assignments

For each FSM found, extract:
- State signal name
- All state names/values
- Brief description of FSM purpose

Task 2 - Protocol Pattern Recognition:
Identify common patterns:

HANDSHAKE: valid/ready, req/ack, req/gnt pairs
- Signals: valid, ready (or similar names)
- Pattern: Producer asserts valid, consumer asserts ready

FIFO: push/pop with full/empty flags
- Signals: push, pop, full, empty, data
- Pattern: Write when not full, read when not empty

AXI: AWVALID/AWREADY, WVALID/WREADY, etc.
- Signals: *VALID, *READY for each channel
- Pattern: AXI handshake protocol

APB: PSEL, PENABLE, PREADY
- Signals: PSEL, PENABLE, PREADY, PWRITE
- Pattern: APB bus protocol

FEW-SHOT EXAMPLE:

Code:
```systemverilog
always_ff @(posedge clk) begin
  case (state)
    IDLE: if (start) state <= ACTIVE;
    ACTIVE: if (done) state <= IDLE;
  endcase
end

assign valid_out = (state == ACTIVE);
always_ff @(posedge clk) begin
  if (valid_out && ready_in) data_out <= data_reg;
end
```

Output:
{{
  "state_machines": [
    {{
      "state_signal": "state",
      "states": ["IDLE", "ACTIVE"],
      "description": "Main control FSM with start/done handshake"
    }}
  ],
  "protocols": [
    {{
      "type": "handshake",
      "signals": ["valid_out", "ready_in"],
      "description": "Output handshake protocol for data transfer"
    }}
  ]
}}

NOW ANALYZE THE MODULE ABOVE.

OUTPUT FORMAT (JSON only):
{{
  "state_machines": [
    {{
      "state_signal": "signal_name",
      "states": ["STATE1", "STATE2"],
      "description": "FSM purpose"
    }}
  ],
  "protocols": [
    {{
      "type": "handshake|fifo|axi|apb|ahb|custom",
      "signals": ["signal1", "signal2"],
      "description": "protocol description"
    }}
  ]
}}

Return ONLY valid JSON."""


class AlignmentPrompts(PromptTemplate):
    """
    Advanced prompts for Alignment Agent
    
    Validates: Requirements 5.1, 5.2
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """System prompt for alignment analysis"""
        return """You are an expert Verification Engineer specializing in requirement-to-implementation traceability.

Your expertise includes:
- Mapping natural language requirements to hardware signals
- Understanding semantic relationships between specifications and RTL
- Assessing confidence in requirement-RTL alignments
- Identifying missing or incomplete implementations
- Detecting ambiguities in specifications

Your responses must be:
- Precise in signal-to-entity mappings
- Honest about confidence levels (0.0 to 1.0)
- Explicit about ambiguities and uncertainties
- Structured as valid JSON
- Complete in identifying all relevant mappings

You understand both hardware specifications and RTL implementations."""
    
    @staticmethod
    def get_mapping_prompt(req_text: str, entities: List[str], 
                          signals: List[Dict[str, str]]) -> str:
        """
        Prompt for entity-to-signal mapping with confidence scoring
        
        Args:
            req_text: Requirement text
            entities: List of entity names from requirement
            signals: List of available RTL signals
            
        Returns:
            User prompt string
        """
        # Limit signals for context window
        signal_list = signals[:50]
        signals_str = '\n'.join([
            f"  - {s['name']} (module: {s['module']}, type: {s.get('type', 'unknown')})"
            for s in signal_list
        ])
        
        entities_str = ', '.join(entities) if entities else 'None explicitly mentioned'
        
        return f"""Map requirement entities to RTL signals with confidence scoring.

REQUIREMENT: {req_text}

ENTITIES MENTIONED: {entities_str}

AVAILABLE RTL SIGNALS:
{signals_str}

MAPPING PROCESS:

Step 1 - Identify Semantic Matches:
For each entity, find RTL signals that could implement it:
- Exact name match (highest confidence: 0.9-1.0)
- Partial name match (medium confidence: 0.6-0.8)
- Semantic match (lower confidence: 0.4-0.6)
- No clear match (confidence: 0.0-0.3)

Step 2 - Assess Confidence:
Consider:
- Name similarity (exact > partial > semantic)
- Signal type appropriateness
- Module context relevance
- Multiple possible matches (reduces confidence)

Step 3 - Identify Ambiguities:
Note when:
- Multiple signals could match one entity
- Entity has no clear RTL signal
- Requirement is unclear or incomplete

FEW-SHOT EXAMPLE:

Requirement: "The acknowledge signal must be asserted within 3 cycles of the request"
Entities: ["acknowledge", "request"]
Signals: ["ack", "req", "valid", "ready"]

Reasoning:
- "acknowledge" → "ack": Exact semantic match, confidence 0.95
- "request" → "req": Exact semantic match, confidence 0.95
- No ambiguities, clear one-to-one mapping

Output:
{{
  "signals": [
    {{
      "entity": "acknowledge",
      "rtl_signal": "ack",
      "module": "handshake_ctrl",
      "confidence": 0.95,
      "reasoning": "Exact semantic match for acknowledge signal"
    }},
    {{
      "entity": "request",
      "rtl_signal": "req",
      "module": "handshake_ctrl",
      "confidence": 0.95,
      "reasoning": "Exact semantic match for request signal"
    }}
  ],
  "ambiguities": [],
  "notes": "Clear one-to-one mapping with high confidence"
}}

NOW PERFORM THE MAPPING.

OUTPUT FORMAT (JSON only):
{{
  "signals": [
    {{
      "entity": "entity_name",
      "rtl_signal": "signal_name",
      "module": "module_name",
      "confidence": 0.85,
      "reasoning": "explanation of match"
    }}
  ],
  "ambiguities": ["description of any unclear mappings"],
  "notes": "overall assessment of alignment quality"
}}

Return ONLY valid JSON."""


class SVAGeneratorPrompts(PromptTemplate):
    """
    Advanced prompts for SVA Generator Agent
    
    Validates: Requirements 6.1, 6.2
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """System prompt for SVA generation"""
        return """You are an expert SystemVerilog Assertion (SVA) Engineer with deep knowledge of formal verification.

Your expertise includes:
- Writing syntactically correct SystemVerilog assertions
- Choosing appropriate assertion types (immediate vs concurrent)
- Using SVA temporal operators correctly (|=>, |->
, ##, [*], [->], etc.)
- Avoiding vacuous and over-constrained assertions
- Writing clear, maintainable assertion code
- Understanding hardware timing and protocols

Your assertions must be:
- Syntactically correct per IEEE 1800 SystemVerilog standard
- Semantically meaningful (not vacuous)
- Appropriately constrained (not too loose or too tight)
- Well-commented with clear intent
- Properly clocked for concurrent assertions
- Reset-aware when applicable

You follow industry best practices for assertion-based verification."""
    
    @staticmethod
    def get_generation_prompt(req_text: str, req_id: str, category: str,
                             temporal_keywords: List[str], entities: List[str],
                             rtl_context: Dict[str, Any], assertion_type: str) -> str:
        """
        Prompt for SVA generation with examples and structured output
        
        Args:
            req_text: Requirement text
            req_id: Requirement identifier
            category: Requirement category
            temporal_keywords: Temporal keywords found
            entities: Entity names
            rtl_context: RTL context dictionary
            assertion_type: Type of assertion to generate
            
        Returns:
            User prompt string
        """
        # Extract context information
        modules = rtl_context.get("modules", [])
        clock = rtl_context.get("default_clock", "clk")
        reset = rtl_context.get("default_reset", "rst_n")
        
        modules_info = "No RTL modules available"
        if modules:
            modules_info = '\n'.join([
                f"  Module: {m.get('name', 'unknown')}\n"
                f"    Signals: {', '.join([s.get('name', '') for s in m.get('signals', [])[:10]])}"
                for m in modules[:3]
            ])
        
        temporal_str = ', '.join(temporal_keywords) if temporal_keywords else 'None'
        entities_str = ', '.join(entities) if entities else 'None'
        
        return f"""Generate a SystemVerilog assertion for this requirement.

REQUIREMENT ID: {req_id}
REQUIREMENT: {req_text}
CATEGORY: {category}
ASSERTION TYPE: {assertion_type}

CONTEXT:
- Temporal Keywords: {temporal_str}
- Entities: {entities_str}
- Clock Signal: {clock}
- Reset Signal: {reset}

RTL MODULES:
{modules_info}

GENERATION GUIDELINES:

1. IMMEDIATE ASSERTIONS (for combinational logic):
   - Use: assert (condition);
   - No clock reference needed
   - For instantaneous checks

2. CONCURRENT ASSERTIONS (for temporal properties):
   - Use: assert property (@(posedge {clock}) condition);
   - Include clock edge
   - Use temporal operators for sequences

3. TEMPORAL OPERATORS:
   - ##N: Delay by N cycles
   - |->: Overlapping implication (consequent starts same cycle)
   - |=>: Non-overlapping implication (consequent starts next cycle)
   - [*N]: Repeat N times
   - [->N]: Go-to repetition (match N times, not necessarily consecutive)
   - throughout: Condition holds throughout sequence

4. RESET HANDLING:
   - Disable assertion during reset: disable iff (!{reset})
   - Or check reset explicitly in condition

FEW-SHOT EXAMPLES:

Example 1 - Handshake Timing:
Requirement: "When request is asserted, acknowledge must be asserted within 3 cycles"
Category: timing
Type: concurrent

Output:
{{
  "code": "// Validates: REQ-001 - Acknowledge timing constraint\\nassert property (@(posedge clk) disable iff (!rst_n)\\n  req |-> ##[1:3] ack\\n);",
  "module": "handshake_ctrl",
  "signals": ["req", "ack", "clk", "rst_n"],
  "confidence": 0.90,
  "explanation": "Checks that ack is asserted 1-3 cycles after req using bounded delay operator"
}}

Example 2 - Safety Property:
Requirement: "Read and write must never be asserted simultaneously"
Category: safety
Type: concurrent

Output:
{{
  "code": "// Validates: REQ-002 - Read/write mutual exclusion\\nassert property (@(posedge clk) disable iff (!rst_n)\\n  !(read && write)\\n);",
  "module": "memory_ctrl",
  "signals": ["read", "write", "clk", "rst_n"],
  "confidence": 0.95,
  "explanation": "Ensures read and write are never high simultaneously, preventing conflicts"
}}

Example 3 - Functional Property:
Requirement: "When enable is high, output must equal input"
Category: functional
Type: immediate

Output:
{{
  "code": "// Validates: REQ-003 - Enable functionality\\nassert property (@(posedge clk) disable iff (!rst_n)\\n  enable |-> (output_data == input_data)\\n);",
  "module": "data_path",
  "signals": ["enable", "output_data", "input_data", "clk", "rst_n"],
  "confidence": 0.92,
  "explanation": "Verifies that output matches input when enable is asserted"
}}

NOW GENERATE THE ASSERTION.

OUTPUT FORMAT (JSON only):
{{
  "code": "complete SVA code with comments",
  "module": "target_module_name",
  "signals": ["signal1", "signal2"],
  "confidence": 0.85,
  "explanation": "what the assertion verifies and how"
}}

Return ONLY valid JSON."""


class ValidationPrompts(PromptTemplate):
    """
    Advanced prompts for Validation Agent
    
    Validates: Requirements 7.2, 7.3
    """
    
    @staticmethod
    def get_system_prompt() -> str:
        """System prompt for validation analysis"""
        return """You are an expert Formal Verification Engineer specializing in assertion quality analysis.

Your expertise includes:
- Detecting vacuous assertions (always true or always false)
- Identifying over-constrained assertions (too restrictive)
- Assessing assertion complexity and maintainability
- Understanding common assertion pitfalls
- Evaluating assertion effectiveness

Your analysis must be:
- Technically rigorous
- Honest about quality issues
- Constructive with improvement suggestions
- Structured as valid JSON
- Based on formal verification principles

You understand both the theory and practice of assertion-based verification."""
    
    @staticmethod
    def get_quality_analysis_prompt(assertion_code: str, requirement_text: str,
                                   rtl_module: str) -> str:
        """
        Prompt for assertion quality analysis with detailed reasoning
        
        Args:
            assertion_code: SVA assertion code
            requirement_text: Original requirement
            rtl_module: Target RTL module
            
        Returns:
            User prompt string
        """
        return f"""Analyze this SystemVerilog assertion for quality issues.

ASSERTION CODE:
{assertion_code}

ORIGINAL REQUIREMENT: {requirement_text}
TARGET MODULE: {rtl_module}

QUALITY ANALYSIS TASKS:

Task 1 - Vacuity Detection:
Check if assertion is:
- Always true (vacuously true): No real constraint
- Always false (vacuously false): Impossible to satisfy
- Trivially satisfied: Too weak to catch bugs

Common vacuity patterns:
- Antecedent never true: "never_true |-> anything"
- Consequent always true: "condition |-> always_true"
- Tautologies: "signal |-> signal"

Task 2 - Over-Constraint Detection:
Check if assertion is:
- Too restrictive: Prevents valid behaviors
- Too specific: Doesn't generalize
- Conflicting: Contradicts other requirements

Common over-constraint patterns:
- Exact cycle counts when ranges acceptable
- Unnecessary mutual exclusions
- Overly strict orderings

Task 3 - Complexity Assessment:
Evaluate:
- Simple: Single condition or basic temporal sequence
- Medium: Multiple conditions with temporal operators
- Complex: Nested sequences, multiple implications

Task 4 - Improvement Suggestions:
Provide actionable recommendations for:
- Fixing vacuity or over-constraints
- Simplifying complex assertions
- Improving readability
- Strengthening weak assertions

FEW-SHOT EXAMPLE:

Assertion:
```systemverilog
assert property (@(posedge clk)
  req |-> req
);
```

Analysis:
- Vacuity: YES - Tautology (req implies itself)
- Reasoning: This assertion is always true when req is true, provides no verification value
- Over-constraint: NO
- Complexity: simple
- Suggestion: "Should check a consequent behavior, e.g., 'req |-> ##[1:5] ack'"

Output:
{{
  "has_vacuity": true,
  "vacuity_reason": "Tautology - antecedent and consequent are identical, assertion provides no verification value",
  "has_over_constraint": false,
  "over_constraint_reason": "",
  "complexity": "simple",
  "quality_score": 0.2,
  "notes": "Replace with meaningful consequent that checks actual system behavior, such as response signal assertion"
}}

NOW ANALYZE THE ASSERTION ABOVE.

OUTPUT FORMAT (JSON only):
{{
  "has_vacuity": true|false,
  "vacuity_reason": "explanation if vacuous, empty string otherwise",
  "has_over_constraint": true|false,
  "over_constraint_reason": "explanation if over-constrained, empty string otherwise",
  "complexity": "simple|medium|complex",
  "quality_score": 0.75,
  "notes": "improvement suggestions and quality assessment"
}}

Return ONLY valid JSON."""


# Export all prompt classes
__all__ = [
    'SpecificationParserPrompts',
    'RTLAnalyzerPrompts',
    'AlignmentPrompts',
    'SVAGeneratorPrompts',
    'ValidationPrompts'
]
