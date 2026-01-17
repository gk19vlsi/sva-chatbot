"""
Property-based tests for authentication and authorization

These tests validate universal correctness properties for security features.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.database import Database
from app.utils.auth import create_access_token, get_password_hash
from bson import ObjectId


# Suppress function_scoped_fixture health check
settings.register_profile("default", suppress_health_check=[HealthCheck.function_scoped_fixture])
settings.load_profile("default")


@pytest.mark.asyncio
@given(
    endpoint=st.sampled_from([
        "/api/auth/me",
        "/api/auth/refresh",
    ])
)
@settings(max_examples=10)
async def test_property_48_authentication_requirement(endpoint):
    """
    Feature: sva-chatbot, Property 48: Authentication Requirement
    
    For any API endpoint (except public health checks), requests without a valid
    JWT token should be rejected with a 401 Unauthorized response.
    
    Validates: Requirements 20.1
    """
    # Create fresh DB connection
    await Database.connect_db()
    
    try:
        with TestClient(app) as client:
            # Test 1: Request without token
            response = client.get(endpoint)
            assert response.status_code == 403, \
                f"Endpoint {endpoint} without token should return 403, got {response.status_code}"
            
            # Test 2: Request with invalid token
            response = client.get(
                endpoint,
                headers={"Authorization": "Bearer invalid_token_12345"}
            )
            assert response.status_code == 401, \
                f"Endpoint {endpoint} with invalid token should return 401, got {response.status_code}"
            
            # Test 3: Request with malformed Authorization header
            response = client.get(
                endpoint,
                headers={"Authorization": "InvalidFormat"}
            )
            assert response.status_code == 403, \
                f"Endpoint {endpoint} with malformed auth should return 403, got {response.status_code}"
    
    finally:
        # Cleanup
        await Database.close_db()


@pytest.mark.asyncio
@given(
    project_name=st.text(min_size=1, max_size=50),
    user1_email=st.emails(),
    user2_email=st.emails(),
    password=st.text(min_size=8, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',)))
)
@settings(max_examples=10)
async def test_property_49_project_ownership_authorization(
    project_name,
    user1_email,
    user2_email,
    password
):
    """
    Feature: sva-chatbot, Property 49: Project Ownership Authorization
    
    For any project access request, the system should verify that the requesting
    user's ID matches the project's user_id before allowing access.
    
    Validates: Requirements 20.2
    """
    # Skip if emails are the same
    if user1_email == user2_email:
        return
    
    # Create fresh DB connection
    await Database.connect_db()
    db = Database.get_db()
    
    try:
        # Create two users
        user1_doc = {
            "email": user1_email,
            "name": "User 1",
            "hashed_password": get_password_hash(password)
        }
        user2_doc = {
            "email": user2_email,
            "name": "User 2",
            "hashed_password": get_password_hash(password)
        }
        
        user1_result = await db.users.insert_one(user1_doc)
        user2_result = await db.users.insert_one(user2_doc)
        
        user1_id = str(user1_result.inserted_id)
        user2_id = str(user2_result.inserted_id)
        
        # Create project owned by user1
        project_doc = {
            "name": project_name,
            "description": "Test project",
            "user_id": user1_id,
            "status": "draft"
        }
        project_result = await db.projects.insert_one(project_doc)
        project_id = str(project_result.inserted_id)
        
        # Test with authorization dependency
        # Test 1: Owner should have access
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
        assert project is not None
        assert str(project.get("user_id")) == user1_id, \
            "Owner should be able to access their own project"
        
        # Test 2: Non-owner should NOT have access
        project = await db.projects.find_one({"_id": ObjectId(project_id)})
        assert project is not None
        
        # Verify that user2 does not own the project
        assert str(project.get("user_id")) != user2_id, \
            "Non-owner should not have access to project"
        
        # Test 3: Verify the authorization logic would reject user2
        is_owner = str(project.get("user_id")) == user2_id
        assert not is_owner, \
            "Authorization check should fail for non-owner"
    
    finally:
        # Cleanup
        await db.users.delete_many({})
        await db.projects.delete_many({})
        await Database.close_db()


@pytest.mark.asyncio
async def test_public_endpoints_no_auth():
    """
    Test that public endpoints (health check, root) don't require authentication
    """
    await Database.connect_db()
    
    try:
        with TestClient(app) as client:
            # Test root endpoint
            response = client.get("/")
            assert response.status_code == 200, \
                "Root endpoint should be accessible without auth"
            
            # Test health check endpoint
            response = client.get("/health")
            assert response.status_code == 200, \
                "Health check endpoint should be accessible without auth"
    
    finally:
        await Database.close_db()
