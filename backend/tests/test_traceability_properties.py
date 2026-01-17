"""
Property-Based Tests for Traceability Management

Tests Properties 20 and 21 from the design document:
- Property 20: Traceability Completeness
- Property 21: Traceability Matrix Completeness

Validates Requirements 8.1, 8.2, 8.3, 8.5
"""
import pytest
from hypothesis import given, strategies as st, settings
from app.utils.traceability import (
    TraceabilityExtractor,
    extract_signal_line_numbers,
    build_assertion_traceability,
    build_traceability_matrix
)


class TestTraceabilityProperties:
    """Property-based tests for traceability management"""
    
    @given(
        signal_name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=65, max_codepoint=122),
            min_size=3,
            max_size=20
        ).filter(lambda x: x[0].isalpha())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_20_traceability_completeness(self, signal_name):
        """
        Feature: sva-chatbot, Property 20: Traceability Completeness
        
        For any generated assertion, its traceability record should include
        the originating requirement text, all RTL signals referenced in the
        assertion, and the RTL module name.
        
        Validates: Requirements 8.1, 8.2, 8.3
        """
        # Create sample RTL code with the signal
        rtl_code = f"""
module test_module (
    input wire clk,
    input wire rst_n,
    input wire {signal_name}
);
    
    always @(posedge clk) begin
        if ({signal_name}) begin
            // do something
        end
    end
    
endmodule
"""
        
        # Create sample assertion code
        assertion_code = f"assert property (@(posedge clk) {signal_name} |-> ##1 rst_n);"
        
        # Build traceability
        extractor = TraceabilityExtractor()
        traceability = extractor.build_assertion_traceability(
            requirement_id="REQ-001",
            requirement_text=f"When {signal_name} is asserted, rst_n must be asserted next cycle",
            assertion_code=assertion_code,
            rtl_code=rtl_code,
            rtl_module="test_module",
            mapped_signals=[signal_name, "rst_n", "clk"]
        )
        
        # Property: Traceability must include requirement text
        assert "requirement_text" in traceability
        assert traceability["requirement_text"] != ""
        assert signal_name in traceability["requirement_text"]
        
        # Property: Traceability must include RTL signals
        assert "rtl_signals" in traceability
        assert isinstance(traceability["rtl_signals"], list)
        assert len(traceability["rtl_signals"]) > 0
        assert signal_name in traceability["rtl_signals"]
        
        # Property: Traceability must include RTL module name
        assert "rtl_module" in traceability
        assert traceability["rtl_module"] == "test_module"
        
        # Property: Traceability must include spec reference
        assert "spec_reference" in traceability
        assert traceability["spec_reference"] == "REQ-001"
    
    @given(
        num_requirements=st.integers(min_value=1, max_value=20),
        num_assertions=st.integers(min_value=0, max_value=30)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_21_traceability_matrix_completeness(
        self,
        num_requirements,
        num_assertions
    ):
        """
        Feature: sva-chatbot, Property 21: Traceability Matrix Completeness
        
        For any project with N requirements and M assertions, the traceability
        matrix should contain entries for all N requirements, showing which
        assertions (if any) validate each requirement.
        
        Validates: Requirements 8.5
        """
        # Generate requirements
        requirements = [
            {
                "requirement_id": f"REQ-{i:03d}",
                "text": f"Requirement {i}",
                "category": "functional"
            }
            for i in range(1, num_requirements + 1)
        ]
        
        # Generate assertions (some may map to same requirement)
        assertions = []
        for i in range(num_assertions):
            # Map to a random requirement (or create orphan assertion)
            req_idx = i % num_requirements if num_requirements > 0 else 0
            req_id = f"REQ-{req_idx + 1:03d}"
            
            assertions.append({
                "id": f"AST-{i:03d}",
                "requirement_id": req_id,
                "assertion_code": f"assert property (signal_{i});",
                "confidence_score": 0.8
            })
        
        # Build traceability matrix
        extractor = TraceabilityExtractor()
        matrix = extractor.build_traceability_matrix(requirements, assertions)
        
        # Property: Matrix must include all requirements
        assert "requirements" in matrix
        assert len(matrix["requirements"]) == num_requirements
        
        # Property: Matrix must have correct total counts
        assert matrix["total_requirements"] == num_requirements
        assert matrix["total_assertions"] == num_assertions
        
        # Property: Covered + uncovered must equal total
        assert (
            matrix["covered_requirements"] + matrix["uncovered_requirements"]
            == num_requirements
        )
        
        # Property: Coverage percentage must be between 0 and 100
        assert 0.0 <= matrix["overall_coverage_percentage"] <= 100.0
        
        # Property: If no assertions, coverage should be 0%
        if num_assertions == 0:
            assert matrix["overall_coverage_percentage"] == 0.0
            assert matrix["covered_requirements"] == 0
        
        # Property: Each requirement entry must have requirement and assertions list
        for req_entry in matrix["requirements"]:
            assert "requirement" in req_entry
            assert "assertions" in req_entry
            assert isinstance(req_entry["assertions"], list)
            assert "coverage" in req_entry
            
            # Coverage should be 1.0 if has assertions, 0.0 otherwise
            if len(req_entry["assertions"]) > 0:
                assert req_entry["coverage"] == 1.0
            else:
                assert req_entry["coverage"] == 0.0
    
    def test_signal_line_number_extraction(self):
        """
        Test that signal line numbers are correctly extracted from RTL code
        
        Validates: Requirements 8.3
        """
        rtl_code = """
module test_module (
    input wire clk,
    input wire rst_n,
    input wire valid,
    output reg ready
);
    
    always @(posedge clk) begin
        if (!rst_n) begin
            ready <= 1'b0;
        end else if (valid) begin
            ready <= 1'b1;
        end
    end
    
endmodule
"""
        
        # Extract line numbers for signals
        signal_lines = extract_signal_line_numbers(
            rtl_code,
            ["clk", "rst_n", "valid", "ready"],
            "test_module"
        )
        
        # All signals should be found
        assert "clk" in signal_lines
        assert "rst_n" in signal_lines
        assert "valid" in signal_lines
        assert "ready" in signal_lines
        
        # Each signal should have at least one line number
        for signal, lines in signal_lines.items():
            assert len(lines) > 0
            # Line numbers should be positive integers
            for line_num in lines:
                assert isinstance(line_num, int)
                assert line_num > 0
    
    def test_signal_extraction_from_assertion(self):
        """
        Test that signals are correctly extracted from assertion code
        
        Validates: Requirements 8.2
        """
        extractor = TraceabilityExtractor()
        
        # Test various assertion formats
        test_cases = [
            (
                "assert property (@(posedge clk) req |-> ##[1:5] ack);",
                ["clk", "req", "ack"]
            ),
            (
                "assert property (@(posedge clk) disable iff (!rst_n) valid && ready);",
                ["clk", "rst_n", "valid", "ready"]
            ),
            (
                "assert (enable == 1'b1);",
                ["enable"]
            )
        ]
        
        for assertion_code, expected_signals in test_cases:
            extracted = extractor.extract_signals_from_assertion(assertion_code)
            
            # All expected signals should be found
            for signal in expected_signals:
                assert signal in extracted, f"Signal {signal} not found in {extracted}"
    
    def test_uncovered_requirements_detection(self):
        """
        Test that uncovered requirements are correctly identified
        
        Validates: Requirements 8.5
        """
        requirements = [
            {"requirement_id": "REQ-001", "text": "Req 1"},
            {"requirement_id": "REQ-002", "text": "Req 2"},
            {"requirement_id": "REQ-003", "text": "Req 3"},
        ]
        
        # Only REQ-001 and REQ-003 have assertions
        assertions = [
            {"requirement_id": "REQ-001", "assertion_code": "assert (a);"},
            {"requirement_id": "REQ-003", "assertion_code": "assert (b);"},
        ]
        
        extractor = TraceabilityExtractor()
        uncovered = extractor.get_uncovered_requirements(requirements, assertions)
        
        # REQ-002 should be uncovered
        assert len(uncovered) == 1
        assert uncovered[0]["requirement_id"] == "REQ-002"
    
    def test_coverage_by_category(self):
        """
        Test that coverage statistics by category are correctly calculated
        
        Validates: Requirements 8.5
        """
        requirements = [
            {"requirement_id": "REQ-001", "text": "Req 1", "category": "functional"},
            {"requirement_id": "REQ-002", "text": "Req 2", "category": "functional"},
            {"requirement_id": "REQ-003", "text": "Req 3", "category": "timing"},
            {"requirement_id": "REQ-004", "text": "Req 4", "category": "timing"},
        ]
        
        # Cover one functional and both timing requirements
        assertions = [
            {"requirement_id": "REQ-001", "assertion_code": "assert (a);"},
            {"requirement_id": "REQ-003", "assertion_code": "assert (b);"},
            {"requirement_id": "REQ-004", "assertion_code": "assert (c);"},
        ]
        
        extractor = TraceabilityExtractor()
        coverage = extractor.get_assertion_coverage_by_category(requirements, assertions)
        
        # Should have two categories
        assert "functional" in coverage
        assert "timing" in coverage
        
        # Functional: 1 of 2 covered (50%)
        assert coverage["functional"]["total_requirements"] == 2
        assert coverage["functional"]["covered_requirements"] == 1
        assert coverage["functional"]["coverage_percentage"] == 50.0
        
        # Timing: 2 of 2 covered (100%)
        assert coverage["timing"]["total_requirements"] == 2
        assert coverage["timing"]["covered_requirements"] == 2
        assert coverage["timing"]["coverage_percentage"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
