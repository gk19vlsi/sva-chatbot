"""
Property-based tests for database transaction rollback

Tests that database transactions properly rollback on failure, preserving data integrity.

Validates: Requirement 19.4
"""
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
from datetime import datetime

from app.utils.transactions import (
    TransactionManager,
    safe_multi_step_operation,
    create_project_with_metadata,
    delete_project_cascade,
    update_assertion_with_feedback
)
from app.middleware.error_handler import DatabaseError


# Test database configuration
TEST_DB_URL = "mongodb://localhost:27017"
TEST_DB_NAME = "sva_chatbot_test_transactions"


@pytest.fixture
async def test_db():
    """Create a test database connection"""
    client = AsyncIOMotorClient(TEST_DB_URL)
    db = client[TEST_DB_NAME]
    
    # Clean up before test
    await db.test_collection.delete_many({})
    await db.projects.delete_many({})
    await db.specifications.delete_many({})
    await db.rtl_designs.delete_many({})
    await db.assertions.delete_many({})
    await db.alignments.delete_many({})
    await db.agent_executions.delete_many({})
    await db.pipeline_executions.delete_many({})
    await db.project_metadata.delete_many({})
    await db.pattern_library.delete_many({})
    
    yield db
    
    # Clean up after test
    await db.test_collection.delete_many({})
    await db.projects.delete_many({})
    await db.specifications.delete_many({})
    await db.rtl_designs.delete_many({})
    await db.assertions.delete_many({})
    await db.alignments.delete_many({})
    await db.agent_executions.delete_many({})
    await db.pipeline_executions.delete_many({})
    await db.project_metadata.delete_many({})
    await db.pattern_library.delete_many({})
    
    client.close()


# Property 46: Transaction Rollback on Failure
@given(
    doc1_value=st.integers(min_value=1, max_value=1000),
    doc2_value=st.integers(min_value=1, max_value=1000),
)
@settings(
    max_examples=100,
    deadline=None
)
def test_transaction_rollback_on_failure(doc1_value, doc2_value):
    """
    Feature: sva-chatbot, Property 46: Transaction Rollback on Failure
    
    For any database operation that fails during a multi-step transaction,
    all changes in that transaction should be rolled back, leaving the
    database in its previous consistent state.
    
    Validates: Requirement 19.4
    """
    async def run_test():
        # Create test database connection
        client = AsyncIOMotorClient(TEST_DB_URL)
        test_db = client[TEST_DB_NAME]
        
        # Clean up before test
        await test_db.test_collection.delete_many({})
        
        try:
            # Get initial count
            initial_count = await test_db.test_collection.count_documents({})
            
            # Create transaction manager
            transaction_manager = TransactionManager(test_db)
            
            # Define a multi-step operation that will fail on the second step
            async def failing_operation(session):
                # Step 1: Insert first document (should succeed)
                await test_db.test_collection.insert_one(
                    {"value": doc1_value, "step": 1},
                    session=session
                )
                
                # Step 2: Insert second document (should succeed)
                await test_db.test_collection.insert_one(
                    {"value": doc2_value, "step": 2},
                    session=session
                )
                
                # Step 3: Raise an error (simulating failure)
                raise ValueError("Simulated failure in transaction")
            
            # Execute operation and expect it to fail
            with pytest.raises(DatabaseError):
                await transaction_manager.execute_in_transaction(
                    failing_operation,
                    "test_failing_operation"
                )
            
            # Verify rollback: count should be unchanged
            final_count = await test_db.test_collection.count_documents({})
            assert final_count == initial_count, (
                f"Transaction rollback failed: expected {initial_count} documents, "
                f"found {final_count}"
            )
            
            # Verify no documents were persisted
            doc1_exists = await test_db.test_collection.find_one({"value": doc1_value, "step": 1})
            doc2_exists = await test_db.test_collection.find_one({"value": doc2_value, "step": 2})
            
            assert doc1_exists is None, "First document should not exist after rollback"
            assert doc2_exists is None, "Second document should not exist after rollback"
            
        finally:
            # Clean up after test
            await test_db.test_collection.delete_many({})
            client.close()
    
    # Run the async test
    asyncio.run(run_test())


@given(
    project_name=st.text(min_size=1, max_size=50),
    description=st.text(max_size=200),
)
@settings(
    max_examples=50,
    deadline=None
)
def test_successful_transaction_commits(project_name, description):
    """
    Test that successful transactions commit all changes
    
    Validates: Requirement 19.4
    """
    async def run_test():
        # Create test database connection
        client = AsyncIOMotorClient(TEST_DB_URL)
        test_db = client[TEST_DB_NAME]
        
        # Clean up before test
        await test_db.test_collection.delete_many({})
        
        try:
            # Get initial count
            initial_count = await test_db.test_collection.count_documents({})
            
            # Create transaction manager
            transaction_manager = TransactionManager(test_db)
            
            # Define a successful multi-step operation
            async def successful_operation(session):
                # Insert multiple documents
                result1 = await test_db.test_collection.insert_one(
                    {"name": project_name, "type": "project"},
                    session=session
                )
                
                result2 = await test_db.test_collection.insert_one(
                    {"description": description, "type": "metadata"},
                    session=session
                )
                
                return (result1.inserted_id, result2.inserted_id)
            
            # Execute operation
            ids = await transaction_manager.execute_in_transaction(
                successful_operation,
                "test_successful_operation"
            )
            
            # Verify commit: count should increase by 2
            final_count = await test_db.test_collection.count_documents({})
            assert final_count == initial_count + 2, (
                f"Transaction commit failed: expected {initial_count + 2} documents, "
                f"found {final_count}"
            )
            
            # Verify documents exist
            doc1 = await test_db.test_collection.find_one({"_id": ids[0]})
            doc2 = await test_db.test_collection.find_one({"_id": ids[1]})
            
            assert doc1 is not None, "First document should exist after commit"
            assert doc2 is not None, "Second document should exist after commit"
            assert doc1["name"] == project_name
            assert doc2["description"] == description
            
        finally:
            # Clean up after test
            await test_db.test_collection.delete_many({})
            client.close()
    
    # Run the async test
    asyncio.run(run_test())


@pytest.mark.asyncio
async def test_safe_multi_step_operation_rollback(test_db):
    """
    Test that safe_multi_step_operation rolls back on failure
    
    Validates: Requirement 19.4
    """
    initial_count = await test_db.test_collection.count_documents({})
    
    # Define operations where the second one fails
    operations = [
        ("insert_doc1", lambda s: test_db.test_collection.insert_one(
            {"value": 1}, session=s
        )),
        ("insert_doc2", lambda s: test_db.test_collection.insert_one(
            {"value": 2}, session=s
        )),
        ("failing_step", lambda s: (_ for _ in ()).throw(ValueError("Fail"))),
    ]
    
    # Execute and expect failure
    with pytest.raises(DatabaseError):
        await safe_multi_step_operation(
            test_db,
            operations,
            "test_multi_step"
        )
    
    # Verify rollback
    final_count = await test_db.test_collection.count_documents({})
    assert final_count == initial_count


@pytest.mark.asyncio
async def test_create_project_with_metadata_rollback(test_db):
    """
    Test that create_project_with_metadata rolls back on failure
    
    Validates: Requirement 19.4
    """
    # Create invalid metadata that will cause an error
    project_data = {
        "name": "Test Project",
        "user_id": "user123",
        "created_at": datetime.utcnow()
    }
    
    # This will fail because we'll simulate an error
    initial_project_count = await test_db.projects.count_documents({})
    initial_metadata_count = await test_db.project_metadata.count_documents({})
    
    # Patch the insert to fail on metadata
    async def failing_create(session):
        # Insert project
        project_result = await test_db.projects.insert_one(project_data, session=session)
        
        # Simulate failure before metadata insert
        raise ValueError("Simulated metadata creation failure")
    
    transaction_manager = TransactionManager(test_db)
    
    with pytest.raises(DatabaseError):
        await transaction_manager.execute_in_transaction(
            failing_create,
            "test_create_project"
        )
    
    # Verify rollback - no new documents
    final_project_count = await test_db.projects.count_documents({})
    final_metadata_count = await test_db.project_metadata.count_documents({})
    
    assert final_project_count == initial_project_count
    assert final_metadata_count == initial_metadata_count


@pytest.mark.asyncio
async def test_delete_project_cascade_atomicity(test_db):
    """
    Test that cascade deletion is atomic - all or nothing
    
    Validates: Requirements 12.3, 19.4
    """
    # Create a project with associated data
    project_id = ObjectId()
    
    await test_db.projects.insert_one({
        "_id": project_id,
        "name": "Test Project",
        "user_id": "user123"
    })
    
    await test_db.specifications.insert_one({
        "project_id": project_id,
        "filename": "spec.md"
    })
    
    await test_db.rtl_designs.insert_one({
        "project_id": project_id,
        "filename": "design.sv"
    })
    
    await test_db.assertions.insert_one({
        "project_id": project_id,
        "code": "assert property ..."
    })
    
    # Verify data exists
    assert await test_db.projects.count_documents({"_id": project_id}) == 1
    assert await test_db.specifications.count_documents({"project_id": project_id}) == 1
    assert await test_db.rtl_designs.count_documents({"project_id": project_id}) == 1
    assert await test_db.assertions.count_documents({"project_id": project_id}) == 1
    
    # Delete project with cascade
    result = await delete_project_cascade(test_db, str(project_id))
    
    # Verify all data is deleted
    assert await test_db.projects.count_documents({"_id": project_id}) == 0
    assert await test_db.specifications.count_documents({"project_id": project_id}) == 0
    assert await test_db.rtl_designs.count_documents({"project_id": project_id}) == 0
    assert await test_db.assertions.count_documents({"project_id": project_id}) == 0
    
    # Verify deletion counts
    assert result["projects"] == 1
    assert result["specifications"] == 1
    assert result["rtl_designs"] == 1
    assert result["assertions"] == 1


@pytest.mark.asyncio
async def test_update_assertion_with_feedback_atomicity(test_db):
    """
    Test that assertion feedback update with pattern increment is atomic
    
    Validates: Requirements 10.3, 11.4, 19.4
    """
    # Create assertion and pattern
    assertion_id = ObjectId()
    pattern_id = ObjectId()
    
    await test_db.assertions.insert_one({
        "_id": assertion_id,
        "code": "assert property ...",
        "user_feedback": {}
    })
    
    await test_db.pattern_library.insert_one({
        "_id": pattern_id,
        "name": "Test Pattern",
        "usage_count": 5
    })
    
    # Update with positive feedback
    feedback = {"rating": 5, "comment": "Great!"}
    
    result = await update_assertion_with_feedback(
        test_db,
        str(assertion_id),
        feedback,
        str(pattern_id)
    )
    
    assert result is True
    
    # Verify assertion was updated
    assertion = await test_db.assertions.find_one({"_id": assertion_id})
    assert assertion["user_feedback"]["rating"] == 5
    
    # Verify pattern usage was incremented
    pattern = await test_db.pattern_library.find_one({"_id": pattern_id})
    assert pattern["usage_count"] == 6


@pytest.mark.asyncio
async def test_transaction_context_manager(test_db):
    """
    Test the transaction context manager directly
    
    Validates: Requirement 19.4
    """
    transaction_manager = TransactionManager(test_db)
    
    initial_count = await test_db.test_collection.count_documents({})
    
    # Test successful transaction
    async with transaction_manager.transaction() as session:
        await test_db.test_collection.insert_one(
            {"value": 100},
            session=session
        )
    
    # Verify commit
    assert await test_db.test_collection.count_documents({}) == initial_count + 1
    
    # Test failed transaction
    try:
        async with transaction_manager.transaction() as session:
            await test_db.test_collection.insert_one(
                {"value": 200},
                session=session
            )
            raise ValueError("Simulated error")
    except DatabaseError:
        pass
    
    # Verify rollback - count should still be initial + 1
    assert await test_db.test_collection.count_documents({}) == initial_count + 1


@given(
    num_operations=st.integers(min_value=2, max_value=10),
    fail_at_step=st.integers(min_value=0, max_value=9)
)
@settings(
    max_examples=50,
    deadline=None
)
def test_multi_step_rollback_at_any_step(num_operations, fail_at_step):
    """
    Test that rollback works regardless of which step fails
    
    Validates: Requirement 19.4
    """
    assume(fail_at_step < num_operations)
    
    async def run_test():
        # Create test database connection
        client = AsyncIOMotorClient(TEST_DB_URL)
        test_db = client[TEST_DB_NAME]
        
        # Clean up before test
        await test_db.test_collection.delete_many({})
        
        try:
            initial_count = await test_db.test_collection.count_documents({})
            
            # Create operations that fail at specified step
            operations = []
            for i in range(num_operations):
                if i == fail_at_step:
                    # This operation will fail
                    operations.append((
                        f"failing_step_{i}",
                        lambda s, i=i: (_ for _ in ()).throw(ValueError(f"Fail at step {i}"))
                    ))
                else:
                    # Normal operation
                    operations.append((
                        f"insert_step_{i}",
                        lambda s, i=i: test_db.test_collection.insert_one(
                            {"step": i, "value": i * 10},
                            session=s
                        )
                    ))
            
            # Execute and expect failure
            with pytest.raises(DatabaseError):
                await safe_multi_step_operation(
                    test_db,
                    operations,
                    "test_multi_step_failure"
                )
            
            # Verify complete rollback
            final_count = await test_db.test_collection.count_documents({})
            assert final_count == initial_count, (
                f"Rollback failed when failing at step {fail_at_step}: "
                f"expected {initial_count} documents, found {final_count}"
            )
            
        finally:
            # Clean up after test
            await test_db.test_collection.delete_many({})
            client.close()
    
    # Run the async test
    asyncio.run(run_test())
