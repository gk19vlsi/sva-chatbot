"""
SystemVerilog Assertion syntax validation utilities

This module provides basic syntax validation for SVA code.
"""
import re
from typing import Tuple


def validate_sva_syntax(sva_code: str) -> Tuple[bool, str]:
    """
    Validate basic SystemVerilog Assertion syntax
    
    This is a simplified validator that checks for common SVA patterns.
    It does not perform full SystemVerilog parsing.
    
    Args:
        sva_code: SVA code string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    Validates: Requirements 6.6, 7.1
    """
    if not sva_code or not sva_code.strip():
        return False, "Empty assertion code"
    
    # Check for basic assertion keywords
    has_assertion = bool(
        re.search(r'\bassert\b', sva_code) or
        re.search(r'\bassume\b', sva_code) or
        re.search(r'\bcover\b', sva_code)
    )
    
    if not has_assertion:
        return False, "Missing assertion keyword (assert, assume, or cover)"
    
    # Check for property keyword in concurrent assertions
    if re.search(r'\bassert\s+property\b', sva_code):
        # This is a concurrent assertion
        
        # Check for clock event
        has_clock = bool(re.search(r'@\s*\(\s*(posedge|negedge)\s+\w+\s*\)', sva_code))
        if not has_clock:
            return False, "Concurrent assertion missing clock event (@(posedge clk) or @(negedge clk))"
        
        # Check for implication operators
        has_implication = bool(
            re.search(r'\|->', sva_code) or
            re.search(r'\|=>', sva_code)
        )
        
        # Check for basic temporal operators (optional but common)
        has_temporal = bool(
            re.search(r'##\d+', sva_code) or  # Delay
            re.search(r'\[\*\d+\]', sva_code) or  # Repetition
            re.search(r'\[=\d+\]', sva_code) or  # Goto repetition
            re.search(r'\[->\d+\]', sva_code) or  # Non-consecutive repetition
            has_implication
        )
    
    # Check for balanced parentheses
    paren_count = 0
    for char in sva_code:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
        if paren_count < 0:
            return False, "Unbalanced parentheses (too many closing parentheses)"
    
    if paren_count != 0:
        return False, "Unbalanced parentheses (unclosed opening parentheses)"
    
    # Check for statement terminator
    if not sva_code.rstrip().endswith(';'):
        return False, "Missing semicolon at end of assertion"
    
    # Basic validation passed
    return True, ""


def extract_clock_signal(sva_code: str) -> str:
    """
    Extract clock signal name from SVA code
    
    Args:
        sva_code: SVA code string
        
    Returns:
        Clock signal name or empty string if not found
    """
    match = re.search(r'@\s*\(\s*(?:posedge|negedge)\s+(\w+)\s*\)', sva_code)
    if match:
        return match.group(1)
    return ""


def extract_reset_signal(sva_code: str) -> str:
    """
    Extract reset signal name from SVA code
    
    Args:
        sva_code: SVA code string
        
    Returns:
        Reset signal name or empty string if not found
    """
    # Look for common reset patterns
    # Pattern 1: disable iff (!rst_n) or disable iff (!reset_n) or disable iff (!reset)
    match = re.search(r'disable\s+iff\s*\(\s*!?\s*(\w*reset\w*|\w*rst\w*)\s*\)', sva_code, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 2: if (rst_n) or if (!rst_n) or if (reset_n) or if (!reset_n)
    match = re.search(r'if\s*\(\s*!?\s*(\w*reset\w*|\w*rst\w*)\s*\)', sva_code, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return ""


def extract_signals(sva_code: str) -> list:
    """
    Extract signal names from SVA code
    
    Args:
        sva_code: SVA code string
        
    Returns:
        List of signal names found in the code
    """
    # Remove comments
    code = re.sub(r'//.*$', '', sva_code, flags=re.MULTILINE)
    code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    
    # Find all identifiers (simplified - doesn't handle all SystemVerilog syntax)
    identifiers = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', code)
    
    # Filter out keywords
    keywords = {
        'assert', 'property', 'assume', 'cover', 'posedge', 'negedge',
        'if', 'else', 'disable', 'iff', 'and', 'or', 'not', 'throughout',
        'within', 'intersect', 'first_match', 'sequence', 'endsequence',
        'endproperty', 'begin', 'end', 'module', 'endmodule'
    }
    
    signals = [id for id in identifiers if id.lower() not in keywords]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_signals = []
    for signal in signals:
        if signal not in seen:
            seen.add(signal)
            unique_signals.append(signal)
    
    return unique_signals
