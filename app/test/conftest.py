import pytest
import asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
import pytest_asyncio

from app.main import app
from app.database import mongodb, get_database
from app.config import settings

# Test database
TEST_DATABASE_URL = "mongodb://localhost:27017/cms_dinamico_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_db():
    """Setup test database"""
    client = AsyncIOMotorClient(TEST_DATABASE_URL)
    database = client.cms_dinamico_test
    
    # Override database dependency
    mongodb.database = database
    
    yield database
    
    # Cleanup
    await client.drop_database("cms_dinamico_test")
    client.close()

@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as c:
        yield c

@pytest.fixture
async def mock_user():
    """Mock user for testing"""
    return {
        "user_id": "test_user_123",
        "email": "test@example.com",
        "role": "admin"
    }