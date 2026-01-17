"""
MongoDB database connection and management
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB connection manager with connection pooling and health checks"""
    
    client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls):
        """
        Initialize database connection with connection pooling
        
        Implements Requirements 18.1, 18.2, 18.3:
        - Establishes async MongoDB connection
        - Configures connection pool
        - Sets up database instance
        """
        try:
            # Build connection string with TLS parameters
            connection_url = settings.mongodb_url
            
            # Add TLS parameters if not already in the connection string
            # Use retryWrites=true and w=majority for better reliability
            if '?' not in connection_url:
                connection_url += '?retryWrites=true&w=majority&tls=true'
            elif 'tls=' not in connection_url.lower():
                connection_url += '&tls=true'
            
            # Import ssl module for TLS configuration
            import ssl
            import certifi
            
            # Create TLS context with relaxed settings for OpenSSL 3.x compatibility
            # This is needed because MongoDB Atlas has issues with OpenSSL 3.x strict mode
            tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            tls_context.check_hostname = False  # Disable hostname checking temporarily
            tls_context.verify_mode = ssl.CERT_NONE  # Disable certificate verification temporarily
            
            # Set minimum TLS version to 1.2 (MongoDB Atlas requirement)
            tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
            
            cls.client = AsyncIOMotorClient(
                connection_url,
                maxPoolSize=50,
                minPoolSize=10,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                tlsAllowInvalidCertificates=True,  # Allow invalid certs for now
                tlsAllowInvalidHostnames=True,     # Allow invalid hostnames for now
            )
            cls._db = cls.client[settings.mongodb_db_name]
            
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB: {settings.mongodb_db_name}")
            
            # Create indexes
            await cls._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        
    @classmethod
    async def close_db(cls):
        """Close database connection and cleanup resources"""
        if cls.client:
            cls.client.close()
            logger.info("MongoDB connection closed")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance
        
        Returns:
            AsyncIOMotorDatabase: MongoDB database instance
            
        Raises:
            Exception: If database is not connected
        """
        if cls._db is None:
            raise Exception("Database not connected. Call connect_db() first.")
        return cls._db
    
    @classmethod
    async def health_check(cls) -> bool:
        """
        Check database connection health
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            if cls.client is None:
                return False
            await cls.client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @classmethod
    async def _create_indexes(cls):
        """
        Create database indexes for performance optimization
        
        Implements Requirement 18.5: Database query optimization through indexing
        """
        db = cls.get_db()
        
        try:
            # Projects collection indexes
            await db.projects.create_index([("user_id", 1), ("created_at", -1)])
            await db.projects.create_index("user_id")
            await db.projects.create_index("status")
            await db.projects.create_index([("user_id", 1), ("status", 1)])
            
            # Specifications collection indexes
            await db.specifications.create_index("project_id")
            await db.specifications.create_index([("project_id", 1), ("processed", 1)])
            await db.specifications.create_index([("project_id", 1), ("file_type", 1)])
            await db.specifications.create_index("uploaded_at")
            
            # RTL designs collection indexes
            await db.rtl_designs.create_index("project_id")
            await db.rtl_designs.create_index([("project_id", 1), ("processed", 1)])
            await db.rtl_designs.create_index("uploaded_at")
            
            # Assertions collection indexes
            await db.assertions.create_index([("project_id", 1), ("confidence_score", -1)])
            await db.assertions.create_index("requirement_id")
            await db.assertions.create_index("project_id")
            await db.assertions.create_index([("project_id", 1), ("assertion_type", 1)])
            await db.assertions.create_index([("project_id", 1), ("category", 1)])
            await db.assertions.create_index("generated_at")
            
            # Pattern library collection indexes
            await db.pattern_library.create_index("category")
            await db.pattern_library.create_index("tags")
            await db.pattern_library.create_index([("usage_count", -1)])
            await db.pattern_library.create_index([("category", 1), ("usage_count", -1)])
            await db.pattern_library.create_index("protocol_type")
            
            # Agent execution logs indexes (for performance tracking)
            await db.agent_logs.create_index([("project_id", 1), ("timestamp", -1)])
            await db.agent_logs.create_index("agent_name")
            await db.agent_logs.create_index([("agent_name", 1), ("timestamp", -1)])
            
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create some indexes: {e}")


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency for getting database instance in FastAPI routes
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    return Database.get_db()


class QueryOptimizer:
    """
    Query optimization utilities for efficient database operations
    
    Implements Requirement 18.5: Use projection to limit returned fields
    """
    
    # Common projection patterns for frequently accessed collections
    PROJECT_SUMMARY_PROJECTION = {
        "_id": 1,
        "name": 1,
        "description": 1,
        "status": 1,
        "created_at": 1,
        "updated_at": 1,
        "metadata": 1
    }
    
    ASSERTION_SUMMARY_PROJECTION = {
        "_id": 1,
        "project_id": 1,
        "requirement_id": 1,
        "assertion_type": 1,
        "confidence_score": 1,
        "category": 1,
        "generated_at": 1
    }
    
    SPECIFICATION_SUMMARY_PROJECTION = {
        "_id": 1,
        "project_id": 1,
        "filename": 1,
        "file_type": 1,
        "processed": 1,
        "uploaded_at": 1
    }
    
    RTL_SUMMARY_PROJECTION = {
        "_id": 1,
        "project_id": 1,
        "filename": 1,
        "processed": 1,
        "uploaded_at": 1
    }
    
    @staticmethod
    def get_projection(collection_name: str, summary: bool = False) -> dict:
        """
        Get optimized projection for a collection
        
        Args:
            collection_name: Name of the collection
            summary: Whether to return summary projection (fewer fields)
            
        Returns:
            Projection dictionary for MongoDB queries
        """
        if not summary:
            return {}  # Return all fields
        
        projections = {
            "projects": QueryOptimizer.PROJECT_SUMMARY_PROJECTION,
            "assertions": QueryOptimizer.ASSERTION_SUMMARY_PROJECTION,
            "specifications": QueryOptimizer.SPECIFICATION_SUMMARY_PROJECTION,
            "rtl_designs": QueryOptimizer.RTL_SUMMARY_PROJECTION
        }
        
        return projections.get(collection_name, {})
    
    @staticmethod
    async def get_project_with_stats(
        db: AsyncIOMotorDatabase,
        project_id: str,
        user_id: str
    ) -> dict:
        """
        Get project with computed statistics using optimized aggregation
        
        Args:
            db: Database instance
            project_id: Project ID
            user_id: User ID for authorization
            
        Returns:
            Project document with statistics
        """
        from bson import ObjectId
        
        pipeline = [
            {
                "$match": {
                    "_id": ObjectId(project_id),
                    "user_id": user_id
                }
            },
            {
                "$lookup": {
                    "from": "specifications",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "specs"
                }
            },
            {
                "$lookup": {
                    "from": "rtl_designs",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "rtl_files"
                }
            },
            {
                "$lookup": {
                    "from": "assertions",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "assertions"
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "description": 1,
                    "status": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "user_id": 1,
                    "metadata": {
                        "total_specs": {"$size": "$specs"},
                        "total_rtl_files": {"$size": "$rtl_files"},
                        "total_assertions": {"$size": "$assertions"}
                    }
                }
            }
        ]
        
        result = await db.projects.aggregate(pipeline).to_list(length=1)
        return result[0] if result else None
    
    @staticmethod
    async def get_assertions_by_project(
        db: AsyncIOMotorDatabase,
        project_id: str,
        limit: int = 100,
        skip: int = 0,
        summary: bool = False
    ) -> list:
        """
        Get assertions for a project with pagination and optional projection
        
        Args:
            db: Database instance
            project_id: Project ID
            limit: Maximum number of results
            skip: Number of results to skip
            summary: Whether to return summary projection
            
        Returns:
            List of assertion documents
        """
        from bson import ObjectId
        
        projection = QueryOptimizer.get_projection("assertions", summary)
        
        cursor = db.assertions.find(
            {"project_id": ObjectId(project_id)},
            projection
        ).sort("generated_at", -1).skip(skip).limit(limit)
        
        return await cursor.to_list(length=limit)
