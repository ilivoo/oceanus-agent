"""Unit tests for MilvusService."""

from unittest.mock import MagicMock, patch

import pytest
from pymilvus import MilvusClient

from oceanus_agent.config.settings import MilvusSettings
from oceanus_agent.services.milvus_service import MilvusService


class TestMilvusService:
    """Test suite for MilvusService."""

    @pytest.fixture
    def mock_settings(self):
        """Mock MilvusSettings."""
        settings = MagicMock(spec=MilvusSettings)
        settings.uri = "http://localhost:19530"
        settings.token_value = "root:Milvus"
        settings.cases_collection = "flink_cases"
        settings.docs_collection = "flink_docs"
        settings.vector_dim = 1536
        return settings

    @pytest.fixture
    def mock_client(self):
        """Mock MilvusClient."""
        with patch("oceanus_agent.services.milvus_service.MilvusClient") as mock:
            client_instance = mock.return_value
            client_instance.has_collection.return_value = True
            yield client_instance

    @pytest.fixture
    def milvus_service(self, mock_settings, mock_client):
        """Create MilvusService instance with mocks."""
        return MilvusService(mock_settings)

    def test_init_creates_collections_if_not_exist(self, mock_settings):
        """Test initialization creates collections if they don't exist."""
        with patch("oceanus_agent.services.milvus_service.MilvusClient") as mock_cls:
            client_instance = mock_cls.return_value
            # Simulate collections not existing
            client_instance.has_collection.return_value = False
            
            MilvusService(mock_settings)
            
            # Check has_collection called for both collections
            assert client_instance.has_collection.call_count == 2
            
            # Check create_collection called twice
            assert client_instance.create_collection.call_count == 2
            
            # Verify schema creation
            assert client_instance.create_schema.call_count == 2
            
    def test_init_skips_creation_if_exist(self, mock_settings):
        """Test initialization skips creation if collections exist."""
        with patch("oceanus_agent.services.milvus_service.MilvusClient") as mock_cls:
            client_instance = mock_cls.return_value
            # Simulate collections existing
            client_instance.has_collection.return_value = True
            
            MilvusService(mock_settings)
            
            # Check create_collection NOT called
            client_instance.create_collection.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_similar_cases(self, milvus_service, mock_client):
        """Test searching similar cases."""
        # Mock search result
        mock_client.search.return_value = [[
            {
                "entity": {
                    "case_id": "case-1",
                    "error_type": "checkpoint_failure",
                    "error_pattern": "timeout",
                    "root_cause": "network",
                    "solution": "retry"
                },
                "distance": 0.85
            }
        ]]
        
        query_vector = [0.1] * 1536
        results = await milvus_service.search_similar_cases(query_vector, error_type="checkpoint_failure")
        
        assert len(results) == 1
        assert results[0]["case_id"] == "case-1"
        assert results[0]["similarity_score"] == 0.85
        
        # Verify search call
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args[1]
        assert call_args["collection_name"] == "flink_cases"
        assert call_args["filter"] == 'error_type == "checkpoint_failure"'

    @pytest.mark.asyncio
    async def test_search_doc_snippets(self, milvus_service, mock_client):
        """Test searching document snippets."""
        # Mock search result
        mock_client.search.return_value = [[
            {
                "entity": {
                    "doc_id": "doc-1",
                    "title": "Checkpoint Guide",
                    "content": "How to tune checkpoints...",
                    "doc_url": "http://docs.flink/checkpoints",
                    "category": "checkpoint"
                },
                "distance": 0.9
            }
        ]]
        
        query_vector = [0.1] * 1536
        results = await milvus_service.search_doc_snippets(query_vector, category="checkpoint")
        
        assert len(results) == 1
        assert results[0]["doc_id"] == "doc-1"
        assert results[0]["title"] == "Checkpoint Guide"
        
        # Verify search call
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args[1]
        assert call_args["collection_name"] == "flink_docs"
        assert call_args["filter"] == 'category == "checkpoint"'

    @pytest.mark.asyncio
    async def test_insert_case(self, milvus_service, mock_client):
        """Test inserting a case."""
        vector = [0.1] * 1536
        await milvus_service.insert_case(
            case_id="case-new",
            vector=vector,
            error_type="oom",
            error_pattern="OOM error",
            root_cause="Bad config",
            solution="Fix config"
        )
        
        mock_client.insert.assert_called_once()
        call_args = mock_client.insert.call_args[1]
        assert call_args["collection_name"] == "flink_cases"
        assert call_args["data"][0]["case_id"] == "case-new"

    @pytest.mark.asyncio
    async def test_insert_doc(self, milvus_service, mock_client):
        """Test inserting a document."""
        vector = [0.1] * 1536
        await milvus_service.insert_doc(
            doc_id="doc-new",
            vector=vector,
            title="New Doc",
            content="Content",
            doc_url="http://url",
            category="general"
        )
        
        mock_client.insert.assert_called_once()
        call_args = mock_client.insert.call_args[1]
        assert call_args["collection_name"] == "flink_docs"
        assert call_args["data"][0]["doc_id"] == "doc-new"

    def test_get_collection_stats(self, milvus_service, mock_client):
        """Test getting collection statistics."""
        # Mock describe_collection
        mock_client.describe_collection.return_value = {"description": "Test Collection"}
        
        # Mock query for count
        mock_client.query.return_value = [{"count(*)": 100}]
        
        stats = milvus_service.get_collection_stats()
        
        assert "flink_cases" in stats
        assert "flink_docs" in stats
        assert stats["flink_cases"]["num_entities"] == 100

    def test_close(self, milvus_service, mock_client):
        """Test closing connection."""
        milvus_service.close()
        mock_client.close.assert_called_once()
