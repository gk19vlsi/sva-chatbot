# End-to-End Testing Report

**Generated:** January 17, 2026  
**Test Type:** Manual End-to-End Testing Documentation

## Overview

This document provides a comprehensive guide for performing end-to-end testing of the SVA-Chatbot system. Due to the current database connection issues identified in the unit test suite, automated E2E tests cannot be executed. This document serves as a manual testing guide and checklist.

## Prerequisites

Before performing E2E testing, ensure:

1. **Database Connection**
   - MongoDB instance is running and accessible
   - Connection string is properly configured in `.env`
   - Database credentials are valid

2. **API Keys**
   - Groq API key is configured in `.env`
   - API key has sufficient quota for testing

3. **Test Data**
   - Sample specification documents (PDF, DOCX, MD, TXT)
   - Sample SystemVerilog RTL files (.sv, .v)
   - Test user accounts created

4. **Services Running**
   - Backend server running on configured port
   - Frontend application running (if testing UI)

## Test Scenarios

### Scenario 1: Complete User Workflow - Happy Path

**Objective:** Validate the complete flow from file upload to assertion export

**Steps:**

1. **User Authentication**

   ```bash
   # Test user registration
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "Test123!"}'

   # Test user login
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "Test123!"}'
   ```

   **Expected:** Receive JWT token for authenticated requests

2. **Project Creation**

   ```bash
   curl -X POST http://localhost:8000/api/projects \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Project", "description": "E2E Test"}'
   ```

   **Expected:** Project created with unique ID

3. **Upload Specification**

   ```bash
   curl -X POST http://localhost:8000/api/projects/<project_id>/upload-spec \
     -H "Authorization: Bearer <token>" \
     -F "file=@test_spec.pdf"
   ```

   **Expected:**
   - File uploaded successfully
   - Text extracted from document
   - Requirements parsed and stored

4. **Upload RTL Design**

   ```bash
   curl -X POST http://localhost:8000/api/projects/<project_id>/upload-rtl \
     -H "Authorization: Bearer <token>" \
     -F "file=@test_design.sv"
   ```

   **Expected:**
   - File uploaded successfully
   - RTL parsed into AST
   - Modules, signals, and state machines extracted

5. **Generate Assertions**

   ```bash
   curl -X POST http://localhost:8000/api/projects/<project_id>/generate \
     -H "Authorization: Bearer <token>"
   ```

   **Expected:**
   - Pipeline executes all 5 agents sequentially
   - WebSocket updates received for each stage
   - Assertions generated with traceability
   - Quality scores calculated

6. **Review Assertions**

   ```bash
   curl -X GET http://localhost:8000/api/projects/<project_id>/assertions \
     -H "Authorization: Bearer <token>"
   ```

   **Expected:**
   - List of generated assertions
   - Each assertion includes:
     - SVA code
     - Confidence score
     - Quality score
     - Traceability information

7. **Edit Assertion**

   ```bash
   curl -X PUT http://localhost:8000/api/assertions/<assertion_id> \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"code": "assert property (@(posedge clk) req |-> ##1 ack);"}'
   ```

   **Expected:**
   - Assertion updated
   - Syntax validated
   - Modified flag set
   - Original version preserved

8. **Provide Feedback**

   ```bash
   curl -X POST http://localhost:8000/api/assertions/<assertion_id>/feedback \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"rating": 5, "comment": "Excellent assertion"}'
   ```

   **Expected:**
   - Feedback stored
   - Pattern usage count updated (if applicable)

9. **Export Assertions**

   ```bash
   curl -X GET http://localhost:8000/api/projects/<project_id>/export \
     -H "Authorization: Bearer <token>" \
     -o assertions.sv
   ```

   **Expected:**
   - SVA file downloaded
   - Contains all assertions
   - Includes comments and traceability
   - Grouped by module
   - Integration instructions included

10. **View Traceability Matrix**

    ```bash
    curl -X GET http://localhost:8000/api/projects/<project_id>/traceability \
      -H "Authorization: Bearer <token>"
    ```

    **Expected:**
    - Matrix showing requirement-to-assertion mappings
    - Coverage percentages
    - Uncovered requirements identified

**Success Criteria:**

- ✅ All API calls return expected status codes
- ✅ Data persists correctly in database
- ✅ Generated assertions are syntactically valid
- ✅ Traceability links are maintained
- ✅ Export file contains all assertions

---

### Scenario 2: Error Handling

**Objective:** Validate system behavior under error conditions

**Test Cases:**

1. **Invalid File Upload**
   - Upload non-supported file type (.exe, .zip)
   - **Expected:** 400 Bad Request with descriptive error

2. **File Size Limit**
   - Upload file exceeding size limit
   - **Expected:** 413 Payload Too Large

3. **Invalid RTL Syntax**
   - Upload SystemVerilog file with syntax errors
   - **Expected:** Error message with line numbers

4. **Unauthorized Access**
   - Access project without authentication
   - **Expected:** 401 Unauthorized
   - Access another user's project
   - **Expected:** 403 Forbidden

5. **Missing Requirements**
   - Generate assertions without uploading specification
   - **Expected:** 400 Bad Request with clear message

6. **API Rate Limiting**
   - Make excessive API calls in short time
   - **Expected:** 429 Too Many Requests

7. **Database Connection Failure**
   - Simulate database unavailability
   - **Expected:** 503 Service Unavailable with retry guidance

8. **Groq API Failure**
   - Simulate API key exhaustion or service outage
   - **Expected:** Fallback to secondary model or graceful error

**Success Criteria:**

- ✅ All errors return appropriate HTTP status codes
- ✅ Error messages are descriptive and actionable
- ✅ No sensitive information leaked in errors
- ✅ System recovers gracefully from failures

---

### Scenario 3: Performance Testing

**Objective:** Validate system performance under load

**Test Cases:**

1. **Large Specification Document**
   - Upload 100+ page PDF specification
   - **Measure:** Processing time, memory usage
   - **Target:** < 30 seconds for parsing

2. **Large RTL Design**
   - Upload RTL file with 10,000+ lines
   - **Measure:** Parsing time, AST generation time
   - **Target:** < 60 seconds for analysis

3. **Multiple Assertions Generation**
   - Generate 50+ assertions from complex specification
   - **Measure:** Total pipeline execution time
   - **Target:** < 5 minutes for complete pipeline

4. **Concurrent Users**
   - Simulate 10 concurrent users uploading files
   - **Measure:** Response times, error rates
   - **Target:** < 10% degradation in response time

5. **WebSocket Performance**
   - Test real-time updates with multiple clients
   - **Measure:** Message delivery latency
   - **Target:** < 100ms latency for status updates

6. **Database Query Performance**
   - Query projects with 100+ assertions
   - **Measure:** Query response time
   - **Target:** < 1 second for listing

**Success Criteria:**

- ✅ All operations complete within target times
- ✅ No memory leaks during extended operation
- ✅ System remains responsive under load
- ✅ Database queries use proper indexes

---

### Scenario 4: Real Specification and RTL Testing

**Objective:** Validate system with real-world hardware designs

**Test Cases:**

1. **AXI Protocol Specification**
   - Upload ARM AMBA AXI specification excerpt
   - Upload AXI master/slave RTL implementation
   - **Expected:**
     - Protocol patterns recognized
     - Handshake assertions generated
     - Burst transaction properties created

2. **FIFO Design**
   - Upload FIFO specification
   - Upload synchronous FIFO RTL
   - **Expected:**
     - Full/empty conditions verified
     - Read/write pointer assertions
     - Data integrity properties

3. **State Machine Verification**
   - Upload FSM specification
   - Upload state machine RTL
   - **Expected:**
     - All states identified
     - Transition assertions generated
     - Illegal state detection properties

4. **Clock Domain Crossing**
   - Upload CDC specification
   - Upload CDC synchronizer RTL
   - **Expected:**
     - Clock signals identified correctly
     - Metastability assertions generated
     - Data coherency properties

**Success Criteria:**

- ✅ System correctly identifies design patterns
- ✅ Generated assertions match industry best practices
- ✅ Traceability maintained for all requirements
- ✅ Quality scores reflect assertion correctness

---

## Test Data Requirements

### Sample Specifications

Create test specifications covering:

- Timing requirements (setup/hold times, delays)
- Functional requirements (operations, behaviors)
- Protocol requirements (handshakes, sequences)
- Safety requirements (error conditions, resets)
- Liveness requirements (progress, fairness)

### Sample RTL Designs

Create test RTL files with:

- Various module sizes (small, medium, large)
- Different design patterns (FSM, datapath, protocol)
- Multiple clock domains
- Reset logic (sync/async)
- Common verification challenges

---

## Automated E2E Test Script

Once database issues are resolved, use this script for automated E2E testing:

```python
#!/usr/bin/env python3
"""
Automated End-to-End Test Suite
"""
import requests
import time
import json
from pathlib import Path

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "e2e_test@example.com"
TEST_PASSWORD = "E2ETest123!"

def run_e2e_test():
    """Run complete E2E test workflow"""

    print("=" * 80)
    print("SVA-Chatbot End-to-End Test")
    print("=" * 80)

    # 1. Register user
    print("\n1. Registering test user...")
    response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code in [200, 201, 409], f"Registration failed: {response.text}"

    # 2. Login
    print("2. Logging in...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create project
    print("3. Creating project...")
    response = requests.post(
        f"{BASE_URL}/api/projects",
        headers=headers,
        json={"name": "E2E Test Project", "description": "Automated test"}
    )
    assert response.status_code in [200, 201], f"Project creation failed: {response.text}"
    project_id = response.json()["id"]

    # 4. Upload specification
    print("4. Uploading specification...")
    with open("test_data/sample_spec.md", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/upload-spec",
            headers=headers,
            files={"file": f}
        )
    assert response.status_code in [200, 201], f"Spec upload failed: {response.text}"

    # 5. Upload RTL
    print("5. Uploading RTL design...")
    with open("test_data/sample_design.sv", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/projects/{project_id}/upload-rtl",
            headers=headers,
            files={"file": f}
        )
    assert response.status_code in [200, 201], f"RTL upload failed: {response.text}"

    # 6. Generate assertions
    print("6. Generating assertions...")
    response = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/generate",
        headers=headers
    )
    assert response.status_code in [200, 202], f"Generation failed: {response.text}"

    # Wait for generation to complete
    print("   Waiting for generation to complete...")
    time.sleep(30)

    # 7. Get assertions
    print("7. Retrieving assertions...")
    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/assertions",
        headers=headers
    )
    assert response.status_code == 200, f"Get assertions failed: {response.text}"
    assertions = response.json()
    assert len(assertions) > 0, "No assertions generated"
    print(f"   Generated {len(assertions)} assertions")

    # 8. Export assertions
    print("8. Exporting assertions...")
    response = requests.get(
        f"{BASE_URL}/api/projects/{project_id}/export",
        headers=headers
    )
    assert response.status_code == 200, f"Export failed: {response.text}"
    assert len(response.content) > 0, "Export file is empty"

    # 9. Cleanup
    print("9. Cleaning up...")
    response = requests.delete(
        f"{BASE_URL}/api/projects/{project_id}",
        headers=headers
    )
    assert response.status_code in [200, 204], f"Cleanup failed: {response.text}"

    print("\n" + "=" * 80)
    print("✅ End-to-End Test PASSED")
    print("=" * 80)

if __name__ == "__main__":
    try:
        run_e2e_test()
    except AssertionError as e:
        print(f"\n❌ Test FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test ERROR: {e}")
        exit(1)
```

---

## Current Status

**Status:** ⚠️ **BLOCKED**

**Reason:** Database connection issues prevent automated E2E testing

**Blockers:**

1. MongoDB Atlas SSL handshake failures
2. Test database configuration issues
3. Async event loop closure in tests

**Required Actions:**

1. Fix database connection for testing environment
2. Set up local MongoDB instance or use mongomock
3. Resolve async test configuration issues

**Manual Testing:** Can be performed once backend server is running with proper database connection

---

## Recommendations

1. **Set Up Test Environment**
   - Use Docker Compose for local testing environment
   - Include MongoDB, backend, and frontend services
   - Use test-specific database and API keys

2. **Create Test Data Repository**
   - Maintain library of test specifications
   - Maintain library of test RTL designs
   - Version control test data

3. **Implement Automated E2E Tests**
   - Use pytest with requests library
   - Implement WebSocket testing with websockets library
   - Add performance benchmarking with pytest-benchmark

4. **Continuous Integration**
   - Run E2E tests on every PR
   - Generate test reports automatically
   - Track performance metrics over time

---

## Conclusion

End-to-end testing framework and test scenarios have been documented. However, automated execution is currently blocked by database connection issues identified in the unit test suite.

**Next Steps:**

1. Resolve database connection issues
2. Set up proper test environment
3. Execute manual E2E tests
4. Implement automated E2E test suite
5. Integrate E2E tests into CI/CD pipeline

Once these steps are completed, comprehensive E2E testing will validate all user workflows, error scenarios, and performance requirements.
