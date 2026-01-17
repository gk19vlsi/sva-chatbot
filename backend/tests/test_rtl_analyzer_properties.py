"""
Property-Based Tests for RTL Analyzer Agent

Tests universal properties that must hold for all RTL analysis operations.
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.utils.sv_parser import SystemVerilogParser, detect_clocks_and_resets
import tempfile
import os


# Strategy for generating SystemVerilog module code
@st.composite
def systemverilog_module(draw):
    """Generate realistic SystemVerilog module code."""
    module_name = draw(st.sampled_from(["fifo", "counter", "arbiter", "controller", "processor"]))
    
    # Generate ports
    num_inputs = draw(st.integers(min_value=1, max_value=3))
    num_outputs = draw(st.integers(min_value=1, max_value=3))
    
    inputs = []
    outputs = []
    
    for i in range(num_inputs):
        input_name = draw(st.sampled_from(["clk", "rst_n", "enable", "valid", "data_in"]))
        inputs.append(f"input logic {input_name}")
    
    for i in range(num_outputs):
        output_name = draw(st.sampled_from(["ready", "done", "data_out", "valid_out"]))
        outputs.append(f"output logic {output_name}")
    
    ports = ",\n    ".join(inputs + outputs)
    
    code = f"""module {module_name} (
    {ports}
);
    // Internal signals
    logic internal_state;
    
    // Module implementation
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            internal_state <= 1'b0;
        end
    end
endmodule
"""
    
    return code, module_name, len(inputs) + len(outputs)


@pytest.mark.asyncio
@given(sv_code=systemverilog_module())
@settings(max_examples=100, deadline=None)
async def test_systemverilog_parsing_completeness(sv_code):
    """
    Property 2: SystemVerilog Parsing Completeness
    
    Universal Property:
    For any valid SystemVerilog module with N ports,
    the parser must extract the module and at least N signals.
    
    Validates: Requirements 2.1, 2.2
    """
    code, expected_module_name, expected_min_ports = sv_code
    
    # Create parser
    parser = SystemVerilogParser()
    
    # Parse the code
    parsed_data, success = parser.parse_code(code)
    
    # Property: Parsing must succeed for valid code
    assert success, "Parser failed on valid SystemVerilog code"
    
    # Property: Must extract modules
    assert "modules" in parsed_data
    assert len(parsed_data["modules"]) > 0, "No modules extracted"
    
    # Property: Module name must match
    module = parsed_data["modules"][0]
    assert "name" in module
    assert module["name"] == expected_module_name, \
        f"Expected module name '{expected_module_name}', got '{module['name']}'"
    
    # Property: Must extract signals
    assert "signals" in module
    assert isinstance(module["signals"], list)
    
    # Property: Must extract at least the expected number of ports
    # (may extract more due to internal signals)
    assert len(module["signals"]) >= expected_min_ports, \
        f"Expected at least {expected_min_ports} signals, got {len(module['signals'])}"
    
    # Property: Each signal must have required fields
    for signal in module["signals"]:
        assert "name" in signal, "Signal missing 'name' field"
        assert "type" in signal, "Signal missing 'type' field"
        assert signal["type"] in ["logic", "wire", "reg"], \
            f"Invalid signal type: {signal['type']}"


@pytest.mark.asyncio
async def test_clock_signal_detection():
    """
    Test that clock signals are detected correctly.
    
    Part of Property 8: Clock and Reset Signal Detection
    """
    # Test various clock naming conventions
    signals = [
        {"name": "clk", "type": "logic"},
        {"name": "clock", "type": "logic"},
        {"name": "sys_clk", "type": "logic"},
        {"name": "data", "type": "logic"},
    ]
    
    clocks, resets = detect_clocks_and_resets(signals)
    
    # Property: Must detect clock signals
    assert "clk" in clocks
    assert "clock" in clocks
    assert "sys_clk" in clocks
    
    # Property: Must not detect non-clock signals as clocks
    assert "data" not in clocks


@pytest.mark.asyncio
async def test_reset_signal_detection():
    """
    Test that reset signals are detected correctly.
    
    Part of Property 8: Clock and Reset Signal Detection
    """
    # Test various reset naming conventions
    signals = [
        {"name": "rst", "type": "logic"},
        {"name": "reset", "type": "logic"},
        {"name": "rst_n", "type": "logic"},
        {"name": "rstn", "type": "logic"},
        {"name": "data", "type": "logic"},
    ]
    
    clocks, resets = detect_clocks_and_resets(signals)
    
    # Property: Must detect reset signals
    assert "rst" in resets
    assert "reset" in resets
    assert "rst_n" in resets
    assert "rstn" in resets
    
    # Property: Must not detect non-reset signals as resets
    assert "data" not in resets


@pytest.mark.asyncio
async def test_module_with_file():
    """
    Test parsing a SystemVerilog module from a file.
    """
    # Create a temporary file with SystemVerilog code
    sv_code = """module test_module (
    input logic clk,
    input logic rst_n,
    input logic data_in,
    output logic data_out
);
    logic internal_reg;
    
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            internal_reg <= 1'b0;
        end else begin
            internal_reg <= data_in;
        end
    end
    
    assign data_out = internal_reg;
endmodule
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(sv_code)
        temp_file = f.name
    
    try:
        parser = SystemVerilogParser()
        parsed_data, success = parser.parse_file(temp_file)
        
        # Property: Must successfully parse file
        assert success
        assert len(parsed_data["modules"]) == 1
        
        module = parsed_data["modules"][0]
        assert module["name"] == "test_module"
        assert len(module["signals"]) >= 4  # At least 4 ports
        
        # Detect clocks and resets
        clocks, resets = detect_clocks_and_resets(module["signals"])
        assert "clk" in clocks
        assert "rst_n" in resets
        
    finally:
        # Clean up temp file
        os.unlink(temp_file)


if __name__ == "__main__":
    print("Run with: pytest tests/test_rtl_analyzer_properties.py -v")



@pytest.mark.asyncio
@given(
    clock_name=st.sampled_from(["clk", "clock", "sys_clk", "core_clk", "clk_i"]),
    reset_name=st.sampled_from(["rst", "reset", "rst_n", "rstn", "rst_i", "areset_n"])
)
@settings(max_examples=100, deadline=None)
async def test_clock_and_reset_signal_detection(clock_name, reset_name):
    """
    Property 8: Clock and Reset Signal Detection
    
    Universal Property:
    For any RTL module with signals named with clock/reset patterns,
    the analyzer must correctly identify them as clock/reset signals.
    
    Validates: Requirements 4.1, 4.2
    """
    from app.agents.rtl_analyzer import RTLAnalyzerAgent
    from app.agents.base import PipelineContext
    from app.clients.groq_client import GroqClient
    from unittest.mock import AsyncMock, MagicMock
    from bson import ObjectId
    import json
    
    # Create RTL code with the specified clock and reset
    rtl_code = f"""module test_module (
    input logic {clock_name},
    input logic {reset_name},
    input logic data_in,
    output logic data_out
);
    logic internal_reg;
    
    always_ff @(posedge {clock_name}) begin
        if (!{reset_name}) begin
            internal_reg <= 1'b0;
        end else begin
            internal_reg <= data_in;
        end
    end
    
    assign data_out = internal_reg;
endmodule
"""
    
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.rtl_designs = AsyncMock()
    mock_db.rtl_designs.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = RTLAnalyzerAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response for semantic analysis
    mock_semantic_response = json.dumps({
        "state_machines": [],
        "protocols": []
    })
    
    agent.call_groq = AsyncMock(return_value=mock_semantic_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "rtl_code": rtl_code,
            "rtl_design_id": str(ObjectId())
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully analyze RTL
    assert result.success, f"Agent failed: {result.error}"
    assert "modules" in result.data
    
    # Property: Must detect the clock signal
    modules = result.data["modules"]
    assert len(modules) > 0
    
    module = modules[0]
    assert "clocks" in module
    assert clock_name in module["clocks"], \
        f"Clock signal '{clock_name}' not detected. Found: {module['clocks']}"
    
    # Property: Must detect the reset signal
    assert "resets" in module
    assert reset_name in module["resets"], \
        f"Reset signal '{reset_name}' not detected. Found: {module['resets']}"
    
    # Property: Default clock and reset must be set
    assert "default_clock" in result.data
    assert "default_reset" in result.data
    assert result.data["default_clock"] == clock_name
    assert result.data["default_reset"] == reset_name



@pytest.mark.asyncio
@given(
    state_signal=st.sampled_from(["state", "current_state", "fsm_state", "ctrl_state"]),
    state1=st.sampled_from(["IDLE", "INIT", "RESET"]),
    state2=st.sampled_from(["ACTIVE", "RUNNING", "BUSY"])
)
@settings(max_examples=100, deadline=None)
async def test_state_machine_extraction(state_signal, state1, state2):
    """
    Property 9: State Machine Extraction
    
    Universal Property:
    For any RTL module containing a state machine with identifiable states,
    the analyzer should extract state machine information via LLM analysis.
    
    Validates: Requirements 4.3
    """
    from app.agents.rtl_analyzer import RTLAnalyzerAgent
    from app.agents.base import PipelineContext
    from app.clients.groq_client import GroqClient
    from unittest.mock import AsyncMock, MagicMock
    from bson import ObjectId
    import json
    
    # Create RTL code with a state machine
    rtl_code = f"""module fsm_module (
    input logic clk,
    input logic rst_n,
    input logic start,
    output logic done
);
    typedef enum logic [1:0] {{
        {state1},
        {state2}
    }} state_t;
    
    state_t {state_signal};
    
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            {state_signal} <= {state1};
        end else begin
            case ({state_signal})
                {state1}: if (start) {state_signal} <= {state2};
                {state2}: {state_signal} <= {state1};
            endcase
        end
    end
    
    assign done = ({state_signal} == {state2});
endmodule
"""
    
    # Setup mock database and client
    mock_db = MagicMock()
    mock_db.rtl_designs = AsyncMock()
    mock_db.rtl_designs.update_one = AsyncMock()
    
    mock_groq_client = AsyncMock(spec=GroqClient)
    agent = RTLAnalyzerAgent(groq_client=mock_groq_client, db=mock_db)
    
    # Mock LLM response with state machine detection
    mock_semantic_response = json.dumps({
        "state_machines": [
            {
                "state_signal": state_signal,
                "states": [state1, state2],
                "description": "Main FSM"
            }
        ],
        "protocols": []
    })
    
    agent.call_groq = AsyncMock(return_value=mock_semantic_response)
    
    # Create context
    context = PipelineContext(
        project_id=str(ObjectId()),
        data={
            "rtl_code": rtl_code,
            "rtl_design_id": str(ObjectId())
        }
    )
    
    # Execute agent
    result = await agent.execute(context)
    
    # Property: Must successfully analyze RTL
    assert result.success, f"Agent failed: {result.error}"
    assert "modules" in result.data
    
    # Property: Must extract state machine information
    modules = result.data["modules"]
    assert len(modules) > 0
    
    module = modules[0]
    assert "state_machines" in module
    
    # Property: State machine should be detected (via LLM)
    state_machines = module["state_machines"]
    if len(state_machines) > 0:
        fsm = state_machines[0]
        assert "state_signal" in fsm
        assert "states" in fsm
        # The LLM should identify the state signal
        assert fsm["state_signal"] == state_signal, \
            f"Expected state signal '{state_signal}', got '{fsm['state_signal']}'"
