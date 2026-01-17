"""
Pytest configuration and fixtures for testing
"""
import pytest
import asyncio
import ssl
import certifi
import os
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_client():
    """Create a test database client"""
    # Use a separate test database
    test_db_name = f"{settings.mongodb_db_name}_test"
    
    # Check if we should skip database tests
    if os.getenv("SKIP_DB_TESTS") == "true":
        pytest.skip("Database tests skipped (SKIP_DB_TESTS=true)")
    
    # Configure SSL/TLS for MongoDB Atlas connections
    # Use certifi for proper certificate verification
    try:
        # Try with proper SSL context using certifi
        client = AsyncIOMotorClient(
            settings.mongodb_url,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        
        # Test connection
        await client.admin.command('ping')
        
    except Exception as e:
        # If connection fails, skip database-dependent tests
        pytest.skip(f"MongoDB connection failed: {str(e)[:100]}. Set up local MongoDB or fix Atlas connection.")
    
    yield client, test_db_name
    
    # Cleanup: drop test database after tests
    try:
        await client.drop_database(test_db_name)
    except Exception:
        pass  # Ignore cleanup errors
    client.close()


@pytest.fixture
async def test_db(test_db_client):
    """Get test database instance"""
    client, db_name = test_db_client
    db = client[db_name]
    
    # Clean database before each test
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].drop()
    
    return db
