#!/usr/bin/env python3
"""
Generate a summary of all tests in the test suite
"""
import os
import re
from pathlib import Path

def extract_test_info(file_path):
    """Extract test information from a test file"""
    tests = []
    with open(file_path, 'r') as f:
        content = f.read()
        
        # Find all test functions
        test_pattern = r'(?:async\s+)?def\s+(test_\w+)\s*\('
        matches = re.finditer(test_pattern, content)
        
        for match in matches:
            test_name = match.group(1)
            
            # Try to find property number and description
            # Look backwards from the match for docstring
            start = max(0, match.start() - 500)
            context = content[start:match.start()]
            
            property_match = re.search(r'Property\s+(\d+):\s+([^\n]+)', context)
            validates_match = re.search(r'Validates:\s+Requirements?\s+([\d\.,\s]+)', context)
            
            test_info = {
                'name': test_name,
                'file': file_path.name,
            }
            
            if property_match:
                test_info['property'] = f"Property {property_match.group(1)}"
                test_info['description'] = property_match.group(2).strip()
            
            if validates_match:
                test_info['validates'] = validates_match.group(1).strip()
            
            tests.append(test_info)
    
    return tests

def main():
    """Generate test summary"""
    test_dir = Path('tests')
    all_tests = []
    
    # Find all test files
    test_files = sorted(test_dir.glob('test_*.py'))
    
    print("=" * 100)
    print("SVA-CHATBOT TEST SUITE SUMMARY")
    print("=" * 100)
    print()
    
    for test_file in test_files:
        tests = extract_test_info(test_file)
        all_tests.extend(tests)
    
    # Group by file
    by_file = {}
    for test in all_tests:
        file_name = test['file']
        if file_name not in by_file:
            by_file[file_name] = []
        by_file[file_name].append(test)
    
    # Print summary
    total_tests = 0
    property_tests = 0
    unit_tests = 0
    integration_tests = 0
    
    for file_name in sorted(by_file.keys()):
        tests = by_file[file_name]
        print(f"\n{file_name}")
        print("-" * 100)
        
        for test in tests:
            total_tests += 1
            
            if 'property' in test:
                property_tests += 1
                print(f"  ✓ {test['name']}")
                print(f"    {test['property']}: {test.get('description', 'N/A')}")
                if 'validates' in test:
                    print(f"    Validates: Requirements {test['validates']}")
            elif 'integration' in file_name:
                integration_tests += 1
                print(f"  ✓ {test['name']} (Integration Test)")
            else:
                unit_tests += 1
                print(f"  ✓ {test['name']} (Unit Test)")
    
    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"Total Tests: {total_tests}")
    print(f"  - Property-Based Tests: {property_tests}")
    print(f"  - Integration Tests: {integration_tests}")
    print(f"  - Unit Tests: {unit_tests}")
    print()
    print("Test Files:")
    for file_name in sorted(by_file.keys()):
        print(f"  - {file_name}: {len(by_file[file_name])} tests")
    print("=" * 100)

if __name__ == '__main__':
    main()
