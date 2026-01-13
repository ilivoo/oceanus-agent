"""Fixtures for integration tests."""

import pytest_asyncio
from oceanus_agent.config.settings import settings
from oceanus_agent.services.milvus_service import MilvusService
from oceanus_agent.services.mysql_service import MySQLService
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest_asyncio.fixture(scope="session")
async def db_setup():
    """Ensure database exists and tables are created."""
    # This assumes the user and password in settings.mysql have permissions to create DBs
    # or that the DB already exists from docker-compose.
    # For CI/Local, we use the one from settings.
    engine = create_async_engine(settings.mysql.url)

    # We could run migrations or init script here if needed.
    # For now, we assume the DB is initialized by docker-compose/scripts.

    yield

    await engine.dispose()


@pytest_asyncio.fixture
async def real_mysql_service(db_setup):
    """Real MySQL service connecting to the integration DB."""
    service = MySQLService(settings.mysql)

    # Clean up tables before each test
    async with service.async_session() as session:
        # Disable foreign key checks to truncate tables
        await session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        await session.execute(text("TRUNCATE TABLE knowledge_cases;"))
        await session.execute(text("TRUNCATE TABLE flink_job_exceptions;"))
        await session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await session.commit()

    yield service

    await service.close()


@pytest_asyncio.fixture
async def real_milvus_service():
    """Real Milvus service connecting to the integration Milvus."""
    service = MilvusService(settings.milvus)

    # Clean up collections before each test (optional, or just delete all data)
    # Milvus doesn't have a simple TRUNCATE, we might need to query and delete or drop and recreate.
    # For safety in tests, we'll try to drop if they exist to start fresh.
    for coll_name in [
        settings.milvus.cases_collection,
        settings.milvus.docs_collection,
    ]:
        if service.client.has_collection(coll_name):
            # Using query to get all IDs and delete might be slow but safe
            service.client.drop_collection(coll_name)

    # Re-initialize collections
    service._ensure_collections()

    yield service

    service.close()
