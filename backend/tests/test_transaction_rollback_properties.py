"""
Property-based tests for database transaction rollback (Mock-based)

Tests that database transactions properly rollback on failure, preserving data integrity.
Uses mocks to avoid requiring a running MongoDB instance.

Validates: Requirement 19.4
"""
import pytest
from hypothesis import given, strategies as st, settings
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from bson import ObjectId
import asyncio

from app.utils.transactions import TransactionManager, safe_multi_step_operation
from app.middleware.error_handler import DatabaseError


def create_mock_db():
    """Create a mock database with transaction support"""
    mock_db = Mock()
    mock_db.client = Mock()
    
    # Mock collections
    mock_db.test_collection = Mock()
    mock_db.projects = Mock()
    mock_db.specifications = Mock()
    mock_db.rtl_designs = Mock()
    mock_db.assertions = Mock()
    mock_db.alignments = Mock()
    mock_db.agent_executions = Mock()
    mock_db.pipeline_executions = Mock()
    
    return mock_db


def create_mock_session():
    """Create a mock MongoDB session"""
    mock_session = AsyncMock()
    
    # Mock transaction methods
    mock_session.commit_transaction = AsyncMock()
    mock_session.abort_transaction = AsyncMock()
    
    # Create a proper async context manager for start_transaction
    class MockTransaction:
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return None
    
    mock_session.start_transaction = Mock(return_value=MockTransaction())
    
    # Make the session itself an async context manager
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)
    
    return mock_session


# Property 46: Transaction Rollback on Failure
@given(
    doc1_value=st.integers(min_value=1, max_value=1000),
    doc2_value=st.integers(min_value=1, max_value=1000),
)
@settings(max_examples=100, deadline=None)
def test_transaction_rollback_on_failure(doc1_value, doc2_value):
    """
    Feature: sva-chatbot, Property 46: Transaction Rollback on Failure
    
    For any database operation that fails during a multi-step transaction,
    all changes in that transaction should be rolled back, leaving the
    database in its previous consistent state.
    
    Validates: Requirement 19.4
    """
    async def run_test():
        # Create mock database and session
        mock_db = create_mock_db()
        mock_session = create_mock_session()
        
        # Track operations performed
        operations_performed = []
        
        # Mock the session context manager
        async def mock_start_session():
            return mock_session
        
        mock_db.client.start_session = mock_start_session
        
        # Create transaction manager
        transaction_manager = TransactionManager(mock_db)
        
        # Define a multi-step operation that will fail
        async def failing_operation(session):
            # Step 1: Record first operation
            operations_performed.append(("insert", doc1_value))
            
            # Step 2: Record second operation
            operations_performed.append(("insert", doc2_value))
            
            # Step 3: Raise an error (simulating failure)
            raise ValueError("Simulated failure in transaction")
        
        # Execute operation and expect it to fail
        with pytest.raises(DatabaseError) as exc_info:
            await transaction_manager.execute_in_transaction(
                failing_operation,
                "test_failing_operation"
            )
        
        # Verify error message indicates rollback
        assert "rolled back" in str(exc_info.value).lower()
        
        # Verify abort_transaction was called (rollback)
        assert mock_session.abort_transaction.called, "Transaction should be aborted on failure"
        
        # Verify commit_transaction was NOT called
        assert not mock_session.commit_transaction.called, "Transaction should not be committed on failure"
        
        # Verify operations were attempted (but rolled back)
        assert len(operations_performed) == 2, "Both operations should have been attempted"
    
    # Run the async test
    asyncio.run(run_test())


@given(
    project_name=st.text(min_size=1, max_size=50),
    description=st.text(max_size=200),
)
@settings(max_examples=50, deadline=None)
def test_successful_transaction_commits(project_name, description):
    """
    Test that successful transactions commit all changes
    
    Validates: Requirement 19.4
    """
    async def run_test():
        # Create mock database and session
        mock_db = create_mock_db()
        mock_session = create_mock_session()
        
        # Track operations
        operations_performed = []
        
        # Mock the session context manager
        async def mock_start_session():
            return mock_session
        
        mock_db.client.start_session = mock_start_session
        
        # Create transaction manager
        transaction_manager = TransactionManager(mock_db)
        
        # Define a successful multi-step operation
        async def successful_operation(session):
            operations_performed.append(("insert_project", project_name))
            operations_performed.append(("insert_metadata", description))
            return ("id1", "id2")
        
        # Execute operation
        result = await transaction_manager.execute_in_transaction(
            successful_operation,
            "test_successful_operation"
        )
        
        # Verify result
        assert result == ("id1", "id2")
        
        # Verify commit_transaction was called
        assert mock_session.commit_transaction.called, "Transaction should be committed on success"
        
        # Verify abort_transaction was NOT called
        assert not mock_session.abort_transaction.called, "Transaction should not be aborted on success"
        
        # Verify operations were performed
        assert len(operations_performed) == 2
        assert operations_performed[0] == ("insert_project", project_name)
        assert operations_performed[1] == ("insert_metadata", description)
    
    # Run the async test
    asyncio.run(run_test())


@given(
    num_operations=st.integers(min_value=2, max_value=10),
    fail_at_step=st.integers(min_value=0, max_value=9)
)
@settings(max_examples=50, deadline=None)
def test_multi_step_rollback_at_any_step(num_operations, fail_at_step):
    """
    Test that rollback works regardless of which step fails
    
    Validates: Requirement 19.4
    """
    from hypothesis import assume
    assume(fail_at_step < num_operations)
    
    async def run_test():
        # Create mock database and session
        mock_db = create_mock_db()
        mock_session = create_mock_session()
        
        # Track operations
        operations_performed = []
        
        # Mock the session context manager
        async def mock_start_session():
            return mock_session
        
        mock_db.client.start_session = mock_start_session
        
        # Create operations that fail at specified step
        operations = []
        for i in range(num_operations):
            if i == fail_at_step:
                # This operation will fail
                async def failing_op(s, i=i):
                    operations_performed.append(("fail", i))
                    raise ValueError(f"Fail at step {i}")
                operations.append((f"failing_step_{i}", failing_op))
            else:
                # Normal operation
                async def normal_op(s, i=i):
                    operations_performed.append(("insert", i))
                    return Mock(inserted_id=ObjectId())
                operations.append((f"insert_step_{i}", normal_op))
        
        # Execute and expect failure
        with pytest.raises(DatabaseError):
            await safe_multi_step_operation(
                mock_db,
                operations,
                "test_multi_step_failure"
            )
        
        # Verify rollback was called
        assert mock_session.abort_transaction.called, (
            f"Transaction should be aborted when failing at step {fail_at_step}"
        )
        
        # Verify commit was NOT called
        assert not mock_session.commit_transaction.called, (
            f"Transaction should not be committed when failing at step {fail_at_step}"
        )
        
        # Verify operations up to and including the failure were attempted
        assert len(operations_performed) == fail_at_step + 1, (
            f"Expected {fail_at_step + 1} operations to be attempted, "
            f"got {len(operations_performed)}"
        )
    
    # Run the async test
    asyncio.run(run_test())


@pytest.mark.asyncio
async def test_transaction_context_manager_success():
    """
    Test the transaction context manager with successful operation
    
    Validates: Requirement 19.4
    """
    # Create mock database and session
    mock_db = create_mock_db()
    mock_session = create_mock_session()
    
    # Mock the session context manager
    async def mock_start_session():
        return mock_session
    
    mock_db.client.start_session = mock_start_session
    
    # Create transaction manager
    transaction_manager = TransactionManager(mock_db)
    
    # Use transaction context manager successfully
    async with transaction_manager.transaction() as session:
        # Perform some operation
        pass
    
    # Verify commit was called
    assert mock_session.commit_transaction.called


@pytest.mark.asyncio
async def test_transaction_context_manager_failure():
    """
    Test the transaction context manager with failed operation
    
    Validates: Requirement 19.4
    """
    # Create mock database and session
    mock_db = create_mock_db()
    mock_session = create_mock_session()
    
    # Mock the session context manager
    async def mock_start_session():
        return mock_session
    
    mock_db.client.start_session = mock_start_session
    
    # Create transaction manager
    transaction_manager = TransactionManager(mock_db)
    
    # Use transaction context manager with failure
    with pytest.raises(DatabaseError):
        async with transaction_manager.transaction() as session:
            # Simulate an error
            raise ValueError("Test error")
    
    # Verify abort was called
    assert mock_session.abort_transaction.called
    
    # Verify commit was NOT called
    assert not mock_session.commit_transaction.called


@pytest.mark.asyncio
async def test_transaction_preserves_error_details():
    """
    Test that transaction rollback preserves original error details
    
    Validates: Requirement 19.4
    """
    # Create mock database and session
    mock_db = create_mock_db()
    mock_session = create_mock_session()
    
    # Mock the session context manager
    async def mock_start_session():
        return mock_session
    
    mock_db.client.start_session = mock_start_session
    
    # Create transaction manager
    transaction_manager = TransactionManager(mock_db)
    
    # Define operation that fails with specific error
    async def failing_operation(session):
        raise ValueError("Specific error message")
    
    # Execute and capture error
    with pytest.raises(DatabaseError) as exc_info:
        await transaction_manager.execute_in_transaction(
            failing_operation,
            "test_operation"
        )
    
    # Verify error message includes original error
    assert "Specific error message" in str(exc_info.value)
    assert "rolled back" in str(exc_info.value).lower()


def test_transaction_manager_initialization():
    """Test that TransactionManager initializes correctly"""
    mock_db = create_mock_db()
    
    transaction_manager = TransactionManager(mock_db)
    
    assert transaction_manager.db == mock_db
    assert transaction_manager.client == mock_db.client


@given(operation_name=st.text(min_size=1, max_size=50))
@settings(max_examples=20, deadline=None)
def test_transaction_operation_naming(operation_name):
    """
    Test that operation names are properly tracked
    
    Validates: Requirement 19.4
    """
    async def run_test():
        # Create mock database and session
        mock_db = create_mock_db()
        mock_session = create_mock_session()
        
        # Mock the session context manager
        async def mock_start_session():
            return mock_session
        
        mock_db.client.start_session = mock_start_session
        
        # Create transaction manager
        transaction_manager = TransactionManager(mock_db)
        
        # Define operation
        async def test_operation(session):
            return "success"
        
        # Execute operation
        result = await transaction_manager.execute_in_transaction(
            test_operation,
            operation_name
        )
        
        # Verify operation completed
        assert result == "success"
        assert mock_session.commit_transaction.called
    
    # Run the async test
    asyncio.run(run_test())
