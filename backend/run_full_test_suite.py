#!/usr/bin/env python3
"""
Full test suite runner with coverage and summary reporting
"""
import subprocess
import sys
import os
import json
from datetime import datetime

def run_tests():
    """Run the full test suite with coverage"""
    print("=" * 80)
    print("SVA-Chatbot Full Test Suite")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Set environment variables
    env = os.environ.copy()
    env['SKIP_DB_TESTS'] = 'true'
    env['HYPOTHESIS_PROFILE'] = 'default'
    
    # Run pytest with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--hypothesis-show-statistics',
        '--maxfail=5',  # Stop after 5 failures
        '-x',  # Stop on first failure for debugging
    ]
    
    print("Running command:")
    print(" ".join(cmd))
    print()
    print("=" * 80)
    print()
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=False,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        print()
        print("=" * 80)
        print(f"Test run completed with exit code: {result.returncode}")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        return result.returncode
        
    except subprocess.TimeoutExpired:
        print()
        print("=" * 80)
        print("ERROR: Test suite timed out after 10 minutes")
        print("=" * 80)
        return 1
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("Test run interrupted by user")
        print("=" * 80)
        return 130

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
