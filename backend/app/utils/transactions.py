"""
Database transaction management utilities

Provides transaction support for MongoDB operations with automatic rollback on failure.

Validates: Requirement 19.4
"""
from motor.motor_asyncio import AsyncIOMotorClientSession, AsyncIOMotorDatabase
from typing import Callable, Any, Optional
from contextlib import asynccontextmanager
import logging

from app.middleware.error_handler import DatabaseError

logger = logging.getLogger(__name__)


class TransactionManager:
    """
    Manager for database transactions with automatic rollback
    
    Validates: Requirement 19.4
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize transaction manager
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self.client = db.client
    
    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for database transactions
        
        Automatically commits on success and rolls back on failure.
        
        Usage:
            async with transaction_manager.transaction() as session:
                await db.collection.insert_one(doc, session=session)
                await db.collection.update_one(filter, update, session=session)
        
        Yields:
            AsyncIOMotorClientSession: MongoDB session for transaction
            
        Validates: Requirement 19.4 - Transaction Rollback on Failure
        """
        session = None
        try:
            # Start a client session
            async with await self.client.start_session() as session:
                # Start transaction
                async with session.start_transaction():
                    logger.info("Transaction started")
                    
                    try:
                        # Yield session to caller
                        yield session
                        
                        # If we reach here, commit the transaction
                        await session.commit_transaction()
                        logger.info("Transaction committed successfully")
                        
                    except Exception as e:
                        # Rollback on any error
                        logger.error(f"Transaction failed, rolling back: {str(e)}")
                        await session.abort_transaction()
                        logger.info("Transaction rolled back")
                        raise DatabaseError(f"Transaction failed and was rolled back: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Failed to start transaction: {str(e)}")
            raise DatabaseError(f"Failed to start transaction: {str(e)}")
    
    async def execute_in_transaction(
        self,
        operation: Callable[[AsyncIOMotorClientSession], Any],
        operation_name: str = "database operation"
    ) -> Any:
        """
        Execute a database operation within a transaction
        
        Args:
            operation: Async function that takes a session and performs database operations
            operation_name: Name of the operation for logging
            
        Returns:
            Result of the operation
            
        Raises:
            DatabaseError: If operation fails
            
        Validates: Requirement 19.4
        """
        try:
            async with self.transaction() as session:
                logger.info(f"Executing {operation_name} in transaction")
                result = await operation(session)
                logger.info(f"{operation_name} completed successfully")
                return result
                
        except DatabaseError:
            # Re-raise DatabaseError as-is
            raise
        except Exception as e:
            logger.error(f"{operation_name} failed: {str(e)}")
            raise DatabaseError(f"{operation_name} failed: {str(e)}")


async def safe_multi_step_operation(
    db: AsyncIOMotorDatabase,
    operations: list[tuple[str, Callable]],
    operation_name: str = "multi-step operation"
) -> list[Any]:
    """
    Execute multiple database operations in a single transaction
    
    All operations succeed together or all fail together (atomicity).
    
    Args:
        db: MongoDB database instance
        operations: List of (name, operation_function) tuples
        operation_name: Overall operation name for logging
        
    Returns:
        List of results from each operation
        
    Raises:
        DatabaseError: If any operation fails
        
    Example:
        results = await safe_multi_step_operation(
            db,
            [
                ("create_project", lambda s: db.projects.insert_one(project, session=s)),
                ("create_spec", lambda s: db.specifications.insert_one(spec, session=s)),
            ],
            "project_creation"
        )
        
    Validates: Requirement 19.4
    """
    transaction_manager = TransactionManager(db)
    results = []
    
    async def execute_all(session: AsyncIOMotorClientSession):
        """Execute all operations in sequence"""
        for op_name, op_func in operations:
            logger.info(f"Executing step: {op_name}")
            result = await op_func(session)
            results.append(result)
        return results
    
    try:
        return await transaction_manager.execute_in_transaction(
            execute_all,
            operation_name
        )
    except Exception as e:
        logger.error(
            f"{operation_name} failed after {len(results)} steps, "
            f"all changes rolled back: {str(e)}"
        )
        raise


async def create_project_with_metadata(
    db: AsyncIOMotorDatabase,
    project_data: dict,
    initial_metadata: dict
) -> tuple[Any, Any]:
    """
    Example: Create a project and its metadata in a single transaction
    
    Args:
        db: MongoDB database instance
        project_data: Project document data
        initial_metadata: Initial metadata document
        
    Returns:
        Tuple of (project_id, metadata_id)
        
    Validates: Requirement 19.4
    """
    async def create_both(session: AsyncIOMotorClientSession):
        # Insert project
        project_result = await db.projects.insert_one(project_data, session=session)
        project_id = project_result.inserted_id
        
        # Add project_id to metadata
        initial_metadata["project_id"] = project_id
        
        # Insert metadata
        metadata_result = await db.project_metadata.insert_one(
            initial_metadata,
            session=session
        )
        metadata_id = metadata_result.inserted_id
        
        return (project_id, metadata_id)
    
    transaction_manager = TransactionManager(db)
    return await transaction_manager.execute_in_transaction(
        create_both,
        "create_project_with_metadata"
    )


async def delete_project_cascade(
    db: AsyncIOMotorDatabase,
    project_id: str
) -> dict:
    """
    Delete a project and all associated data in a single transaction
    
    Deletes:
    - Project document
    - All specifications
    - All RTL designs
    - All assertions
    - All alignments
    - All agent executions
    
    Args:
        db: MongoDB database instance
        project_id: Project ID to delete
        
    Returns:
        Dict with deletion counts
        
    Validates: Requirements 12.3, 19.4
    """
    from bson import ObjectId
    
    async def delete_all(session: AsyncIOMotorClientSession):
        deletion_counts = {}
        
        # Delete project
        project_result = await db.projects.delete_one(
            {"_id": ObjectId(project_id)},
            session=session
        )
        deletion_counts["projects"] = project_result.deleted_count
        
        # Delete specifications
        spec_result = await db.specifications.delete_many(
            {"project_id": ObjectId(project_id)},
            session=session
        )
        deletion_counts["specifications"] = spec_result.deleted_count
        
        # Delete RTL designs
        rtl_result = await db.rtl_designs.delete_many(
            {"project_id": ObjectId(project_id)},
            session=session
        )
        deletion_counts["rtl_designs"] = rtl_result.deleted_count
        
        # Delete assertions
        assertion_result = await db.assertions.delete_many(
            {"project_id": ObjectId(project_id)},
            session=session
        )
        deletion_counts["assertions"] = assertion_result.deleted_count
        
        # Delete alignments
        alignment_result = await db.alignments.delete_many(
            {"project_id": ObjectId(project_id)},
            session=session
        )
        deletion_counts["alignments"] = alignment_result.deleted_count
        
        # Delete agent executions
        agent_result = await db.agent_executions.delete_many(
            {"project_id": ObjectId(project_id)},
            session=session
        )
        deletion_counts["agent_executions"] = agent_result.deleted_count
        
        # Delete pipeline executions
        pipeline_result = await db.pipeline_executions.delete_many(
            {"project_id": project_id},
            session=session
        )
        deletion_counts["pipeline_executions"] = pipeline_result.deleted_count
        
        logger.info(f"Cascade deletion completed: {deletion_counts}")
        
        return deletion_counts
    
    transaction_manager = TransactionManager(db)
    return await transaction_manager.execute_in_transaction(
        delete_all,
        f"delete_project_cascade_{project_id}"
    )


async def update_assertion_with_feedback(
    db: AsyncIOMotorDatabase,
    assertion_id: str,
    feedback: dict,
    pattern_id: Optional[str] = None
) -> bool:
    """
    Update assertion feedback and optionally increment pattern usage in a transaction
    
    Args:
        db: MongoDB database instance
        assertion_id: Assertion ID to update
        feedback: Feedback data to store
        pattern_id: Optional pattern ID to increment usage count
        
    Returns:
        True if successful
        
    Validates: Requirements 10.3, 11.4, 19.4
    """
    from bson import ObjectId
    
    async def update_both(session: AsyncIOMotorClientSession):
        # Update assertion with feedback
        assertion_result = await db.assertions.update_one(
            {"_id": ObjectId(assertion_id)},
            {"$set": {"user_feedback": feedback}},
            session=session
        )
        
        if assertion_result.matched_count == 0:
            raise ValueError(f"Assertion {assertion_id} not found")
        
        # If positive feedback and pattern was used, increment pattern usage
        if pattern_id and feedback.get("rating", 0) >= 4:
            pattern_result = await db.pattern_library.update_one(
                {"_id": ObjectId(pattern_id)},
                {"$inc": {"usage_count": 1}},
                session=session
            )
            
            if pattern_result.matched_count == 0:
                logger.warning(f"Pattern {pattern_id} not found, skipping usage increment")
        
        return True
    
    transaction_manager = TransactionManager(db)
    return await transaction_manager.execute_in_transaction(
        update_both,
        f"update_assertion_feedback_{assertion_id}"
    )
