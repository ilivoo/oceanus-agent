"""Unit tests for KnowledgeRetriever node."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from oceanus_agent.config.settings import KnowledgeSettings
from oceanus_agent.models.state import RetrievedCase, RetrievedDoc
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.services.milvus_service import MilvusService
from oceanus_agent.workflow.nodes.retriever import KnowledgeRetriever


class TestKnowledgeRetriever:
    """Test suite for KnowledgeRetriever node."""

    @pytest.fixture
    def mock_milvus_service(self):
        """Mock MilvusService."""
        service = MagicMock(spec=MilvusService)
        service.search_similar_cases = AsyncMock()
        service.search_doc_snippets = AsyncMock()
        return service

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLMService."""
        service = MagicMock(spec=LLMService)
        service.generate_embedding = AsyncMock()
        return service

    @pytest.fixture
    def mock_settings(self):
        """Mock KnowledgeSettings."""
        settings = MagicMock(spec=KnowledgeSettings)
        settings.max_similar_cases = 3
        settings.max_doc_snippets = 3
        return settings

    @pytest.fixture
    def retriever(self, mock_milvus_service, mock_llm_service, mock_settings):
        """Create KnowledgeRetriever instance."""
        return KnowledgeRetriever(mock_milvus_service, mock_llm_service, mock_settings)

    @pytest.mark.asyncio
    async def test_retrieve_success(
        self, retriever, mock_milvus_service, mock_llm_service
    ):
        """Test successful retrieval."""
        state = {
            "job_info": {
                "job_id": "job-1",
                "error_type": "checkpoint",
                "error_message": "timeout",
            }
        }

        # Mock LLM embedding
        mock_llm_service.generate_embedding.return_value = [0.1] * 1536

        # Mock Milvus search
        mock_case = RetrievedCase(
            case_id="c1",
            error_type="checkpoint",
            error_pattern="p",
            root_cause="r",
            solution="s",
            similarity_score=0.9,
        )
        mock_doc = RetrievedDoc(
            doc_id="d1", title="t", content="c", similarity_score=0.8
        )
        mock_milvus_service.search_similar_cases.return_value = [mock_case]
        mock_milvus_service.search_doc_snippets.return_value = [mock_doc]

        new_state = await retriever(state)

        assert "retrieved_context" in new_state
        context = new_state["retrieved_context"]
        assert len(context["similar_cases"]) == 1
        assert len(context["doc_snippets"]) == 1
        assert context["similar_cases"][0] == mock_case

        # Verify calls
        mock_llm_service.generate_embedding.assert_called_once()
        mock_milvus_service.search_similar_cases.assert_called_once()

    @pytest.mark.asyncio
    async def test_retrieve_no_job_info(self, retriever):
        """Test retrieval with missing job info."""
        state = {}
        new_state = await retriever(state)
        assert new_state == state

    @pytest.mark.asyncio
    async def test_retrieve_error_handling(self, retriever, mock_llm_service):
        """Test error handling during retrieval (should return empty context)."""
        state = {
            "job_info": {
                "job_id": "job-1",
                "error_type": "checkpoint",
                "error_message": "timeout",
            }
        }

        mock_llm_service.generate_embedding.side_effect = Exception("API Error")

        new_state = await retriever(state)

        assert "retrieved_context" in new_state
        assert new_state["retrieved_context"]["similar_cases"] == []
        assert new_state["retrieved_context"]["doc_snippets"] == []
