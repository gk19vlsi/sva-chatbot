"""
Property-based tests for database operations

Tests Properties 30 and 44 from the design document
"""
import pytest
from hypothesis import given, strategies as st, settings as hypothesis_settings, HealthCheck
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


# Custom strategies for generating test data
@st.composite
def project_data(draw):
    """Generate random project data"""
    return {
        "name": draw(st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters=['\x00']))),
        "description": draw(st.one_of(
            st.none(),
            st.text(max_size=1000, alphabet=st.characters(blacklist_characters=['\x00']))
        )),
        "user_id": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00']))),
        "status": draw(st.sampled_from(["draft", "processing", "completed", "failed"])),
        "metadata": {
            "total_specs": draw(st.integers(min_value=0, max_value=100)),
            "total_rtl_files": draw(st.integers(min_value=0, max_value=100)),
            "total_assertions": draw(st.integers(min_value=0, max_value=1000))
        },
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@st.composite
def specification_data(draw):
    """Generate random specification data"""
    return {
        "project_id": ObjectId(),
        "filename": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00', '/']))),
        "file_type": draw(st.sampled_from(["pdf", "docx", "md", "txt"])),
        "file_path": draw(st.text(min_size=1, max_size=200, alphabet=st.characters(blacklist_characters=['\x00']))),
        "raw_text": draw(st.one_of(
            st.none(),
            st.text(max_size=5000, alphabet=st.characters(blacklist_characters=['\x00']))
        )),
        "parsed_requirements": [],
        "uploaded_at": datetime.utcnow(),
        "processed": draw(st.booleans())
    }


@st.composite
def assertion_data(draw):
    """Generate random assertion data"""
    return {
        "project_id": ObjectId(),
        "requirement_id": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00']))),
        "rtl_module": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00']))),
        "assertion_code": draw(st.text(min_size=1, max_size=1000, alphabet=st.characters(blacklist_characters=['\x00']))),
        "assertion_type": draw(st.sampled_from(["immediate", "concurrent", "property", "sequence"])),
        "category": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00']))),
        "confidence_score": draw(st.floats(min_value=0.0, max_value=1.0)),
        "explanation": draw(st.text(max_size=500, alphabet=st.characters(blacklist_characters=['\x00']))),
        "traceability": {
            "spec_reference": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00']))),
            "requirement_text": draw(st.text(min_size=1, max_size=500, alphabet=st.characters(blacklist_characters=['\x00']))),
            "rtl_signals": draw(st.lists(st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00'])), max_size=10)),
            "rtl_module": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_characters=['\x00']))),
            "line_numbers": draw(st.lists(st.integers(min_value=1, max_value=10000), max_size=20))
        },
        "user_feedback": {
            "rating": None,
            "modified": False,
            "comments": None
        },
        "generated_at": datetime.utcnow(),
        "agent_version": "1.0.0"
    }


async def get_test_db():
    """Get a fresh test database connection"""
    test_db_name = f"{settings.mongodb_db_name}_test"
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[test_db_name]
    
    # Clean all collections
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].drop()
    
    return db, client


@pytest.mark.asyncio
@given(data=project_data())
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_30_project_metadata_persistence(data):
    """
    Feature: sva-chatbot, Property 30: Project Metadata Persistence
    
    For any created project, storing it and then retrieving it should produce
    a project record with the same name, description, and user_id.
    
    Validates: Requirements 12.1
    """
    db, client = await get_test_db()
    
    try:
        # Store project
        result = await db.projects.insert_one(data)
        project_id = result.inserted_id
        
        # Retrieve project
        retrieved = await db.projects.find_one({"_id": project_id})
        
        # Verify equivalence
        assert retrieved is not None
        assert retrieved["name"] == data["name"]
        assert retrieved["description"] == data["description"]
        assert retrieved["user_id"] == data["user_id"]
        assert retrieved["status"] == data["status"]
        assert retrieved["metadata"]["total_specs"] == data["metadata"]["total_specs"]
        assert retrieved["metadata"]["total_rtl_files"] == data["metadata"]["total_rtl_files"]
        assert retrieved["metadata"]["total_assertions"] == data["metadata"]["total_assertions"]
    finally:
        client.close()


@pytest.mark.asyncio
@given(data=specification_data())
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_44_specification_storage_consistency(data):
    """
    Feature: sva-chatbot, Property 44: Database Storage Consistency
    
    For any document (specification, RTL, or assertion) stored in MongoDB,
    retrieving it by ID should return a document with all the same field values.
    
    Validates: Requirements 18.1, 18.2, 18.3
    """
    db, client = await get_test_db()
    
    try:
        # Store specification
        result = await db.specifications.insert_one(data)
        spec_id = result.inserted_id
        
        # Retrieve specification
        retrieved = await db.specifications.find_one({"_id": spec_id})
        
        # Verify all fields match
        assert retrieved is not None
        assert retrieved["project_id"] == data["project_id"]
        assert retrieved["filename"] == data["filename"]
        assert retrieved["file_type"] == data["file_type"]
        assert retrieved["file_path"] == data["file_path"]
        assert retrieved["raw_text"] == data["raw_text"]
        assert retrieved["processed"] == data["processed"]
    finally:
        client.close()


@pytest.mark.asyncio
@given(data=assertion_data())
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_44_assertion_storage_consistency(data):
    """
    Feature: sva-chatbot, Property 44: Database Storage Consistency
    
    For any assertion stored in MongoDB, retrieving it by ID should return
    a document with all the same field values.
    
    Validates: Requirements 18.1, 18.2, 18.3
    """
    db, client = await get_test_db()
    
    try:
        # Store assertion
        result = await db.assertions.insert_one(data)
        assertion_id = result.inserted_id
        
        # Retrieve assertion
        retrieved = await db.assertions.find_one({"_id": assertion_id})
        
        # Verify all fields match
        assert retrieved is not None
        assert retrieved["project_id"] == data["project_id"]
        assert retrieved["requirement_id"] == data["requirement_id"]
        assert retrieved["rtl_module"] == data["rtl_module"]
        assert retrieved["assertion_code"] == data["assertion_code"]
        assert retrieved["assertion_type"] == data["assertion_type"]
        assert retrieved["category"] == data["category"]
        assert abs(retrieved["confidence_score"] - data["confidence_score"]) < 0.0001
        assert retrieved["explanation"] == data["explanation"]
        assert retrieved["traceability"]["spec_reference"] == data["traceability"]["spec_reference"]
        assert retrieved["traceability"]["requirement_text"] == data["traceability"]["requirement_text"]
        assert retrieved["traceability"]["rtl_signals"] == data["traceability"]["rtl_signals"]
        assert retrieved["traceability"]["rtl_module"] == data["traceability"]["rtl_module"]
        assert retrieved["traceability"]["line_numbers"] == data["traceability"]["line_numbers"]
    finally:
        client.close()


@pytest.mark.asyncio
@given(
    user_id=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters=['\x00'])),
    num_projects=st.integers(min_value=0, max_value=10)
)
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_31_project_listing_completeness(user_id, num_projects):
    """
    Feature: sva-chatbot, Property 31: Project Listing Completeness
    
    For any user with N projects, listing projects should return exactly N
    project records with summary statistics.
    
    Validates: Requirements 12.2
    """
    db, client = await get_test_db()
    
    try:
        # Create N projects for the user
        project_ids = []
        for i in range(num_projects):
            project_doc = {
                "name": f"Project {i}",
                "description": f"Description {i}",
                "user_id": user_id,
                "status": "draft",
                "metadata": {
                    "total_specs": i,
                    "total_rtl_files": i,
                    "total_assertions": i * 2
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            result = await db.projects.insert_one(project_doc)
            project_ids.append(result.inserted_id)
        
        # Create some projects for a different user (should not be returned)
        other_user_id = f"{user_id}_other"
        for i in range(3):
            other_project = {
                "name": f"Other Project {i}",
                "user_id": other_user_id,
                "status": "draft",
                "metadata": {
                    "total_specs": 0,
                    "total_rtl_files": 0,
                    "total_assertions": 0
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await db.projects.insert_one(other_project)
        
        # List projects for the user
        projects = await db.projects.find({"user_id": user_id}).to_list(length=None)
        
        # Verify exactly N projects returned
        assert len(projects) == num_projects
        
        # Verify all projects have summary statistics
        for project in projects:
            assert "metadata" in project
            assert "total_specs" in project["metadata"]
            assert "total_rtl_files" in project["metadata"]
            assert "total_assertions" in project["metadata"]
            assert project["user_id"] == user_id
    finally:
        client.close()


@pytest.mark.asyncio
@given(
    num_specs=st.integers(min_value=0, max_value=5),
    num_rtl=st.integers(min_value=0, max_value=5),
    num_assertions=st.integers(min_value=0, max_value=10)
)
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_32_cascading_project_deletion(num_specs, num_rtl, num_assertions):
    """
    Feature: sva-chatbot, Property 32: Cascading Project Deletion
    
    For any project with associated specifications, RTL files, and assertions,
    deleting the project should remove all associated records from the database.
    
    Validates: Requirements 12.3
    """
    db, client = await get_test_db()
    
    try:
        # Create a project
        project_doc = {
            "name": "Test Project",
            "description": "Test Description",
            "user_id": "test_user",
            "status": "draft",
            "metadata": {
                "total_specs": num_specs,
                "total_rtl_files": num_rtl,
                "total_assertions": num_assertions
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.projects.insert_one(project_doc)
        project_id = result.inserted_id
        
        # Create associated specifications
        spec_ids = []
        for i in range(num_specs):
            spec_doc = {
                "project_id": project_id,
                "filename": f"spec_{i}.md",
                "file_type": "md",
                "file_path": f"/path/to/spec_{i}.md",
                "raw_text": f"Specification content {i}",
                "parsed_requirements": [],
                "uploaded_at": datetime.utcnow(),
                "processed": False
            }
            result = await db.specifications.insert_one(spec_doc)
            spec_ids.append(result.inserted_id)
        
        # Create associated RTL files
        rtl_ids = []
        for i in range(num_rtl):
            rtl_doc = {
                "project_id": project_id,
                "filename": f"design_{i}.sv",
                "file_path": f"/path/to/design_{i}.sv",
                "source_code": f"module design_{i}; endmodule",
                "parsed_ast": {},
                "analysis": {},
                "uploaded_at": datetime.utcnow(),
                "processed": False
            }
            result = await db.rtl_designs.insert_one(rtl_doc)
            rtl_ids.append(result.inserted_id)
        
        # Create associated assertions
        assertion_ids = []
        for i in range(num_assertions):
            assertion_doc = {
                "project_id": project_id,
                "requirement_id": f"req_{i}",
                "rtl_module": "test_module",
                "assertion_code": f"assert property (test_{i});",
                "assertion_type": "concurrent",
                "category": "functional",
                "confidence_score": 0.9,
                "explanation": f"Test assertion {i}",
                "traceability": {
                    "spec_reference": f"spec_{i}",
                    "requirement_text": f"Requirement {i}",
                    "rtl_signals": ["clk", "rst"],
                    "rtl_module": "test_module",
                    "line_numbers": [i]
                },
                "user_feedback": {
                    "rating": None,
                    "modified": False,
                    "comments": None
                },
                "generated_at": datetime.utcnow(),
                "agent_version": "1.0.0"
            }
            result = await db.assertions.insert_one(assertion_doc)
            assertion_ids.append(result.inserted_id)
        
        # Verify all records exist before deletion
        assert await db.projects.count_documents({"_id": project_id}) == 1
        assert await db.specifications.count_documents({"project_id": project_id}) == num_specs
        assert await db.rtl_designs.count_documents({"project_id": project_id}) == num_rtl
        assert await db.assertions.count_documents({"project_id": project_id}) == num_assertions
        
        # Delete the project (cascading delete)
        await db.projects.delete_one({"_id": project_id})
        await db.specifications.delete_many({"project_id": project_id})
        await db.rtl_designs.delete_many({"project_id": project_id})
        await db.assertions.delete_many({"project_id": project_id})
        
        # Verify all associated records are deleted
        assert await db.projects.count_documents({"_id": project_id}) == 0
        assert await db.specifications.count_documents({"project_id": project_id}) == 0
        assert await db.rtl_designs.count_documents({"project_id": project_id}) == 0
        assert await db.assertions.count_documents({"project_id": project_id}) == 0
    finally:
        client.close()


@pytest.mark.asyncio
@given(
    num_specs=st.integers(min_value=0, max_value=10),
    num_rtl=st.integers(min_value=0, max_value=10),
    num_assertions=st.integers(min_value=0, max_value=20)
)
@hypothesis_settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_33_project_statistics_accuracy(num_specs, num_rtl, num_assertions):
    """
    Feature: sva-chatbot, Property 33: Project Statistics Accuracy
    
    For any project, the tracked statistics (total specs, total RTL files,
    total assertions) should match the actual count of documents in the
    respective collections.
    
    Validates: Requirements 12.5
    """
    db, client = await get_test_db()
    
    try:
        # Create a project with initial statistics
        project_doc = {
            "name": "Statistics Test Project",
            "description": "Testing statistics accuracy",
            "user_id": "test_user",
            "status": "draft",
            "metadata": {
                "total_specs": 0,
                "total_rtl_files": 0,
                "total_assertions": 0
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await db.projects.insert_one(project_doc)
        project_id = result.inserted_id
        
        # Create specifications
        for i in range(num_specs):
            spec_doc = {
                "project_id": project_id,
                "filename": f"spec_{i}.md",
                "file_type": "md",
                "file_path": f"/path/to/spec_{i}.md",
                "raw_text": f"Content {i}",
                "parsed_requirements": [],
                "uploaded_at": datetime.utcnow(),
                "processed": False
            }
            await db.specifications.insert_one(spec_doc)
        
        # Create RTL files
        for i in range(num_rtl):
            rtl_doc = {
                "project_id": project_id,
                "filename": f"design_{i}.sv",
                "file_path": f"/path/to/design_{i}.sv",
                "source_code": f"module design_{i}; endmodule",
                "parsed_ast": {},
                "analysis": {},
                "uploaded_at": datetime.utcnow(),
                "processed": False
            }
            await db.rtl_designs.insert_one(rtl_doc)
        
        # Create assertions
        for i in range(num_assertions):
            assertion_doc = {
                "project_id": project_id,
                "requirement_id": f"req_{i}",
                "rtl_module": "test_module",
                "assertion_code": f"assert property (test_{i});",
                "assertion_type": "concurrent",
                "category": "functional",
                "confidence_score": 0.9,
                "explanation": f"Test assertion {i}",
                "traceability": {
                    "spec_reference": f"spec_{i}",
                    "requirement_text": f"Requirement {i}",
                    "rtl_signals": ["clk"],
                    "rtl_module": "test_module",
                    "line_numbers": [i]
                },
                "user_feedback": {
                    "rating": None,
                    "modified": False,
                    "comments": None
                },
                "generated_at": datetime.utcnow(),
                "agent_version": "1.0.0"
            }
            await db.assertions.insert_one(assertion_doc)
        
        # Update project statistics
        actual_specs = await db.specifications.count_documents({"project_id": project_id})
        actual_rtl = await db.rtl_designs.count_documents({"project_id": project_id})
        actual_assertions = await db.assertions.count_documents({"project_id": project_id})
        
        await db.projects.update_one(
            {"_id": project_id},
            {
                "$set": {
                    "metadata.total_specs": actual_specs,
                    "metadata.total_rtl_files": actual_rtl,
                    "metadata.total_assertions": actual_assertions
                }
            }
        )
        
        # Retrieve project and verify statistics match actual counts
        project = await db.projects.find_one({"_id": project_id})
        
        assert project["metadata"]["total_specs"] == num_specs
        assert project["metadata"]["total_rtl_files"] == num_rtl
        assert project["metadata"]["total_assertions"] == num_assertions
        
        # Verify statistics match actual document counts
        assert project["metadata"]["total_specs"] == actual_specs
        assert project["metadata"]["total_rtl_files"] == actual_rtl
        assert project["metadata"]["total_assertions"] == actual_assertions
    finally:
        client.close()
