"""
Traceability Utilities

This module provides utilities for extracting and managing traceability information
between requirements, RTL code, and generated assertions.

Implements Requirements 8.1, 8.2, 8.3, 8.5
"""
from typing import List, Dict, Any, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class TraceabilityExtractor:
    """
    Extracts comprehensive traceability information from RTL code and assertions
    
    Capabilities:
    - Extract line numbers where signals are defined/used
    - Find signal declarations and assignments
    - Map assertion signals to RTL locations
    - Build requirement-to-assertion mappings
    """
    
    def __init__(self):
        """Initialize traceability extractor"""
        pass
    
    def extract_signal_line_numbers(
        self,
        rtl_code: str,
        signal_names: List[str],
        module_name: Optional[str] = None
    ) -> Dict[str, List[int]]:
        """
        Extract line numbers where signals are defined or used in RTL code
        
        Args:
            rtl_code: RTL source code
            signal_names: List of signal names to find
            module_name: Optional module name to scope the search
            
        Returns:
            Dictionary mapping signal names to list of line numbers
            
        Validates: Requirements 8.3
        """
        signal_lines = {signal: [] for signal in signal_names}
        
        lines = rtl_code.split('\n')
        
        # If module name specified, find module boundaries
        module_start = 0
        module_end = len(lines)
        
        if module_name:
            module_start, module_end = self._find_module_boundaries(lines, module_name)
        
        # Search for each signal in the module
        for signal in signal_names:
            # Create regex pattern for signal (word boundary to avoid partial matches)
            pattern = rf'\b{re.escape(signal)}\b'
            
            for line_num in range(module_start, module_end):
                line = lines[line_num]
                
                # Skip comments
                if line.strip().startswith('//'):
                    continue
                
                # Check if signal appears in this line
                if re.search(pattern, line):
                    # Line numbers are 1-indexed
                    signal_lines[signal].append(line_num + 1)
        
        # Remove signals with no matches
        signal_lines = {sig: lines for sig, lines in signal_lines.items() if lines}
        
        return signal_lines
    
    def _find_module_boundaries(
        self,
        lines: List[str],
        module_name: str
    ) -> Tuple[int, int]:
        """
        Find start and end line indices for a module
        
        Args:
            lines: List of code lines
            module_name: Module name to find
            
        Returns:
            Tuple of (start_line_index, end_line_index)
        """
        start = 0
        end = len(lines)
        
        # Find module declaration
        module_pattern = rf'^\s*module\s+{re.escape(module_name)}\b'
        
        for i, line in enumerate(lines):
            if re.search(module_pattern, line):
                start = i
                break
        
        # Find endmodule
        for i in range(start, len(lines)):
            if re.search(r'^\s*endmodule\b', lines[i]):
                end = i + 1
                break
        
        return start, end
    
    def extract_signal_definitions(
        self,
        rtl_code: str,
        signal_names: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract signal definitions (type, width, direction) from RTL
        
        Args:
            rtl_code: RTL source code
            signal_names: List of signal names
            
        Returns:
            Dictionary with signal definition details
        """
        signal_defs = {}
        
        lines = rtl_code.split('\n')
        
        for signal in signal_names:
            # Look for signal declarations
            # Patterns: input/output/inout/wire/reg/logic [width] signal_name
            patterns = [
                rf'(input|output|inout)\s+(?:wire|reg|logic)?\s*(?:\[.*?\])?\s*\b{re.escape(signal)}\b',
                rf'(wire|reg|logic)\s*(?:\[.*?\])?\s*\b{re.escape(signal)}\b'
            ]
            
            for line_num, line in enumerate(lines):
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        signal_defs[signal] = {
                            'line_number': line_num + 1,
                            'declaration': line.strip(),
                            'type': match.group(1)
                        }
                        break
                
                if signal in signal_defs:
                    break
        
        return signal_defs
    
    def build_assertion_traceability(
        self,
        requirement_id: str,
        requirement_text: str,
        assertion_code: str,
        rtl_code: str,
        rtl_module: str,
        mapped_signals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive traceability information for an assertion
        
        Args:
            requirement_id: Requirement identifier
            requirement_text: Full requirement text
            assertion_code: Generated assertion code
            rtl_code: RTL source code
            rtl_module: Target RTL module name
            mapped_signals: Optional list of mapped signals (extracted if not provided)
            
        Returns:
            Traceability dictionary
            
        Validates: Requirements 8.1, 8.2, 8.3
        """
        # Extract signals from assertion if not provided
        if mapped_signals is None:
            mapped_signals = self.extract_signals_from_assertion(assertion_code)
        
        # Get line numbers for each signal
        signal_line_numbers = self.extract_signal_line_numbers(
            rtl_code, mapped_signals, rtl_module
        )
        
        # Flatten line numbers (all unique lines where any signal appears)
        all_line_numbers = set()
        for lines in signal_line_numbers.values():
            all_line_numbers.update(lines)
        
        # Sort line numbers
        sorted_line_numbers = sorted(list(all_line_numbers))
        
        # Build traceability record
        traceability = {
            "spec_reference": requirement_id,
            "requirement_text": requirement_text,
            "rtl_signals": mapped_signals,
            "rtl_module": rtl_module,
            "line_numbers": sorted_line_numbers,
            "signal_locations": signal_line_numbers  # Detailed per-signal locations
        }
        
        return traceability
    
    def extract_signals_from_assertion(self, assertion_code: str) -> List[str]:
        """
        Extract signal names from assertion code
        
        Args:
            assertion_code: SVA assertion code
            
        Returns:
            List of signal names found in assertion
        """
        # Remove comments
        code = re.sub(r'//.*$', '', assertion_code, flags=re.MULTILINE)
        
        # Remove SVA keywords and operators
        sva_keywords = [
            'assert', 'property', 'sequence', 'posedge', 'negedge',
            'disable', 'iff', 'throughout', 'within', 'intersect',
            'first_match', 'not', 'and', 'or', 'if', 'else'
        ]
        
        # Find potential signal names (identifiers)
        # Pattern: word characters, underscores, but not starting with digit
        potential_signals = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        
        # Filter out keywords
        signals = []
        for sig in potential_signals:
            if sig.lower() not in sva_keywords and sig not in signals:
                signals.append(sig)
        
        return signals
    
    def build_traceability_matrix(
        self,
        requirements: List[Dict[str, Any]],
        assertions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build requirement-to-assertion traceability matrix
        
        Args:
            requirements: List of requirement dictionaries
            assertions: List of assertion dictionaries
            
        Returns:
            Traceability matrix with coverage statistics
            
        Validates: Requirements 8.5
        """
        # Build mapping from requirement_id to assertions
        req_to_assertions = {}
        
        for req in requirements:
            req_id = req.get('requirement_id', '')
            req_to_assertions[req_id] = {
                'requirement': req,
                'assertions': [],
                'coverage': 0.0
            }
        
        # Map assertions to requirements
        for assertion in assertions:
            req_id = assertion.get('requirement_id', '')
            if req_id in req_to_assertions:
                req_to_assertions[req_id]['assertions'].append(assertion)
        
        # Calculate coverage
        total_requirements = len(requirements)
        covered_requirements = sum(
            1 for data in req_to_assertions.values() if len(data['assertions']) > 0
        )
        
        overall_coverage = (
            (covered_requirements / total_requirements * 100)
            if total_requirements > 0 else 0.0
        )
        
        # Calculate per-requirement coverage (1.0 if has assertions, 0.0 otherwise)
        for req_id, data in req_to_assertions.items():
            data['coverage'] = 1.0 if len(data['assertions']) > 0 else 0.0
        
        # Build matrix
        matrix = {
            'requirements': list(req_to_assertions.values()),
            'total_requirements': total_requirements,
            'covered_requirements': covered_requirements,
            'uncovered_requirements': total_requirements - covered_requirements,
            'overall_coverage_percentage': round(overall_coverage, 2),
            'total_assertions': len(assertions)
        }
        
        return matrix
    
    def get_uncovered_requirements(
        self,
        requirements: List[Dict[str, Any]],
        assertions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Get list of requirements that have no assertions
        
        Args:
            requirements: List of requirement dictionaries
            assertions: List of assertion dictionaries
            
        Returns:
            List of uncovered requirements
        """
        # Get all requirement IDs that have assertions
        covered_req_ids = set(
            assertion.get('requirement_id', '') for assertion in assertions
        )
        
        # Find requirements without assertions
        uncovered = [
            req for req in requirements
            if req.get('requirement_id', '') not in covered_req_ids
        ]
        
        return uncovered
    
    def get_assertion_coverage_by_category(
        self,
        requirements: List[Dict[str, Any]],
        assertions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate coverage statistics by requirement category
        
        Args:
            requirements: List of requirement dictionaries
            assertions: List of assertion dictionaries
            
        Returns:
            Dictionary with coverage by category
        """
        # Group requirements by category
        req_by_category = {}
        for req in requirements:
            category = req.get('category', 'unknown')
            if category not in req_by_category:
                req_by_category[category] = []
            req_by_category[category].append(req)
        
        # Calculate coverage for each category
        coverage_by_category = {}
        
        for category, reqs in req_by_category.items():
            matrix = self.build_traceability_matrix(reqs, assertions)
            coverage_by_category[category] = {
                'total_requirements': matrix['total_requirements'],
                'covered_requirements': matrix['covered_requirements'],
                'coverage_percentage': matrix['overall_coverage_percentage'],
                'assertion_count': len([
                    a for a in assertions
                    if any(r.get('requirement_id') == a.get('requirement_id') for r in reqs)
                ])
            }
        
        return coverage_by_category


# Global traceability extractor instance
traceability_extractor = TraceabilityExtractor()


# Convenience functions
def extract_signal_line_numbers(
    rtl_code: str,
    signal_names: List[str],
    module_name: Optional[str] = None
) -> Dict[str, List[int]]:
    """Extract line numbers where signals appear in RTL"""
    return traceability_extractor.extract_signal_line_numbers(
        rtl_code, signal_names, module_name
    )


def build_assertion_traceability(
    requirement_id: str,
    requirement_text: str,
    assertion_code: str,
    rtl_code: str,
    rtl_module: str,
    mapped_signals: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Build comprehensive traceability for an assertion"""
    return traceability_extractor.build_assertion_traceability(
        requirement_id, requirement_text, assertion_code,
        rtl_code, rtl_module, mapped_signals
    )


def build_traceability_matrix(
    requirements: List[Dict[str, Any]],
    assertions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Build requirement-to-assertion traceability matrix"""
    return traceability_extractor.build_traceability_matrix(requirements, assertions)


__all__ = [
    'TraceabilityExtractor',
    'traceability_extractor',
    'extract_signal_line_numbers',
    'build_assertion_traceability',
    'build_traceability_matrix'
]
