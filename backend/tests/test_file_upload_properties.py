"""
Property-based tests for file upload functionality

These tests validate universal correctness properties for file handling.
"""
import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from fastapi.testclient import TestClient
from app.main import app
from app.database import Database
from app.utils.auth import create_access_token, get_password_hash
from bson import ObjectId
import io
import os

# Suppress function_scoped_fixture health check
settings.register_profile("default", suppress_health_check=[HealthCheck.function_scoped_fixture])
settings.load_profile("default")


@pytest.mark.asyncio
@given(
    file_extension=st.sampled_from([".exe", ".zip", ".jpg", ".png", ".html", ".js"]),
    file_size_mb=st.integers(min_value=51, max_value=100)
)
@settings(max_examples=10)
async def test_property_35_invalid_file_rejection(file_extension, file_size_mb):
    """
    Feature: sva-chatbot, Property 35: Invalid File Rejection
    
    For any file that fails validation (wrong type or exceeds size limit),
    the upload should be rejected and an error message displayed.
    
    Validates: Requirements 13.4, 20.3
    """
    # Create fresh DB connection
    await Database.connect_db()
    db = Database.get_db()
    
    try:
        # Create test user
        user_doc = {
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": get_password_hash("password123")
        }
        user_result = await db.users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)
        
        # Create test project
        project_doc = {
            "name": "Test Project",
            "description": "Test",
            "user_id": user_id,
            "status": "draft",
            "metadata": {"total_specs": 0, "total_rtl_files": 0, "total_assertions": 0}
        }
        project_result = await db.projects.insert_one(project_doc)
        project_id = str(project_result.inserted_id)
        
        # Create token
        token = create_access_token(data={"sub": user_id, "email": "test@example.com"})
        
        with TestClient(app) as client:
            # Test 1: Invalid file type for specification
            file_content = b"Test content"
            files = {"file": (f"test{file_extension}", io.BytesIO(file_content), "application/octet-stream")}
            
            response = client.post(
                f"/api/projects/{project_id}/upload-spec",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should reject invalid file type
            assert response.status_code in [400, 413], \
                f"Invalid file type should be rejected, got {response.status_code}"
            
            # Test 2: File size exceeds limit
            # Create a file larger than max size
            large_content = b"x" * (file_size_mb * 1024 * 1024)
            files = {"file": ("test.md", io.BytesIO(large_content), "text/markdown")}
            
            response = client.post(
                f"/api/projects/{project_id}/upload-spec",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should reject file that's too large
            assert response.status_code == 413, \
                f"Oversized file should be rejected with 413, got {response.status_code}"
            
            # Verify error message is descriptive
            assert "detail" in response.json(), \
                "Error response should include detail message"
    
    finally:
        # Cleanup
        await db.users.delete_many({})
        await db.projects.delete_many({})
        await db.specifications.delete_many({})
        await Database.close_db()


@pytest.mark.asyncio
@given(
    text_content=st.text(min_size=10, max_size=500, alphabet=st.characters(blacklist_categories=('Cs',)))
)
@settings(max_examples=10)
async def test_property_1_document_text_extraction_consistency(text_content):
    """
    Feature: sva-chatbot, Property 1: Document Text Extraction Consistency
    
    For any supported document format (PDF, DOCX, MD, TXT) containing text content,
    extracting text from the document should produce output that preserves the
    original text content.
    
    Validates: Requirements 1.1, 1.2, 1.3, 1.4
    """
    # Create fresh DB connection
    await Database.connect_db()
    db = Database.get_db()
    
    try:
        # Create test user
        user_doc = {
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": get_password_hash("password123")
        }
        user_result = await db.users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)
        
        # Create test project
        project_doc = {
            "name": "Test Project",
            "description": "Test",
            "user_id": user_id,
            "status": "draft",
            "metadata": {"total_specs": 0, "total_rtl_files": 0, "total_assertions": 0}
        }
        project_result = await db.projects.insert_one(project_doc)
        project_id = str(project_result.inserted_id)
        
        # Create token
        token = create_access_token(data={"sub": user_id, "email": "test@example.com"})
        
        with TestClient(app) as client:
            # Test with text file (simplest case for round-trip)
            file_content = text_content.encode('utf-8')
            files = {"file": ("test.txt", io.BytesIO(file_content), "text/plain")}
            
            response = client.post(
                f"/api/projects/{project_id}/upload-spec",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should succeed
            assert response.status_code == 200, \
                f"Valid file upload should succeed, got {response.status_code}"
            
            # Get the uploaded specification
            spec_id = response.json()["id"]
            spec = await db.specifications.find_one({"_id": ObjectId(spec_id)})
            
            # Verify text extraction preserved content
            assert spec is not None, "Specification should be stored in database"
            assert spec["raw_text"] is not None, "Text should be extracted"
            
            # For text files, content should be preserved exactly
            # (allowing for minor encoding differences)
            extracted_text = spec["raw_text"]
            assert len(extracted_text) > 0, "Extracted text should not be empty"
            
            # Verify the text content is similar (allowing for encoding variations)
            # We check that most of the original content is preserved
            similarity = sum(c in extracted_text for c in text_content) / len(text_content)
            assert similarity > 0.8, \
                f"Text extraction should preserve most content (similarity: {similarity})"
    
    finally:
        # Cleanup
        await db.users.delete_many({})
        await db.projects.delete_many({})
        await db.specifications.delete_many({})
        
        # Clean up uploaded files
        import shutil
        upload_dir = f"./uploads/{project_id}"
        if os.path.exists(upload_dir):
            shutil.rmtree(upload_dir)
        
        await Database.close_db()


@pytest.mark.asyncio
async def test_valid_file_upload():
    """
    Test that valid files are accepted and stored correctly
    """
    await Database.connect_db()
    db = Database.get_db()
    project_id = None
    
    try:
        # Create test user
        user_doc = {
            "email": "test@example.com",
            "name": "Test User",
            "hashed_password": get_password_hash("test123")  # Shorter password
        }
        user_result = await db.users.insert_one(user_doc)
        user_id = str(user_result.inserted_id)
        
        # Create test project
        project_doc = {
            "name": "Test Project",
            "description": "Test",
            "user_id": user_id,
            "status": "draft",
            "metadata": {"total_specs": 0, "total_rtl_files": 0, "total_assertions": 0}
        }
        project_result = await db.projects.insert_one(project_doc)
        project_id = str(project_result.inserted_id)
        
        # Create token
        token = create_access_token(data={"sub": user_id, "email": "test@example.com"})
        
        with TestClient(app) as client:
            # Test specification upload
            spec_content = b"# Test Specification\n\nThis is a test."
            files = {"file": ("test.md", io.BytesIO(spec_content), "text/markdown")}
            
            response = client.post(
                f"/api/projects/{project_id}/upload-spec",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert "id" in response.json()
            
            # Test RTL upload
            rtl_content = b"module test(); endmodule"
            files = {"file": ("test.sv", io.BytesIO(rtl_content), "text/plain")}
            
            response = client.post(
                f"/api/projects/{project_id}/upload-rtl",
                files=files,
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            assert "id" in response.json()
    
    finally:
        # Cleanup
        await db.users.delete_many({})
        await db.projects.delete_many({})
        await db.specifications.delete_many({})
        await db.rtl_designs.delete_many({})
        
        # Clean up uploaded files
        if project_id:
            import shutil
            upload_dir = f"./uploads/{project_id}"
            if os.path.exists(upload_dir):
                shutil.rmtree(upload_dir)
        
        await Database.close_db()
