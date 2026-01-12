"""Unit tests for KnowledgeAccumulator node."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from oceanus_agent.config.settings import KnowledgeSettings
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.services.milvus_service import MilvusService
from oceanus_agent.services.mysql_service import MySQLService
from oceanus_agent.workflow.nodes.accumulator import KnowledgeAccumulator


class TestKnowledgeAccumulator:
    """Test suite for KnowledgeAccumulator node."""

    @pytest.fixture
    def mock_services(self):
        """Mock all dependent services."""
        return {
            "mysql": MagicMock(spec=MySQLService),
            "milvus": MagicMock(spec=MilvusService),
            "llm": MagicMock(spec=LLMService)
        }

    @pytest.fixture
    def mock_settings(self):
        """Mock KnowledgeSettings."""
        settings = MagicMock(spec=KnowledgeSettings)
        settings.confidence_threshold = 0.8
        return settings

    @pytest.fixture
    def accumulator(self, mock_services, mock_settings):
        """Create KnowledgeAccumulator instance."""
        mock_services["llm"].generate_embedding = AsyncMock()
        mock_services["milvus"].insert_case = AsyncMock()
        mock_services["mysql"].insert_knowledge_case = AsyncMock()
        
        return KnowledgeAccumulator(
            mock_services["mysql"],
            mock_services["milvus"],
            mock_services["llm"],
            mock_settings
        )

    @pytest.mark.asyncio
    async def test_accumulate_high_confidence(self, accumulator, mock_services):
        """Test accumulation when confidence is high."""
        state = {
            "job_info": {
                "exception_id": 1,
                "job_id": "job-1",
                "error_message": "error",
                "error_type": "checkpoint"
            },
            "diagnosis_result": {
                "confidence": 0.9,
                "root_cause": "cause",
                "suggested_fix": "fix"
            }
        }
        
        mock_services["llm"].generate_embedding.return_value = [0.1] * 1536
        
        await accumulator(state)
        
        mock_services["milvus"].insert_case.assert_called_once()
        mock_services["mysql"].insert_knowledge_case.assert_called_once()

    @pytest.mark.asyncio
    async def test_skip_low_confidence(self, accumulator, mock_services):
        """Test skipping accumulation when confidence is low."""
        state = {
            "job_info": {"job_id": "job-1"},
            "diagnosis_result": {
                "confidence": 0.5,  # Below 0.8 threshold
            }
        }
        
        await accumulator(state)
        
        mock_services["milvus"].insert_case.assert_not_called()
        mock_services["mysql"].insert_knowledge_case.assert_not_called()

    @pytest.mark.asyncio
    async def test_accumulate_error_handling(self, accumulator, mock_services):
        """Test error handling during accumulation (should not raise)."""
        state = {
            "job_info": {
                "exception_id": 1,
                "job_id": "job-1",
                "error_message": "error"
            },
            "diagnosis_result": {
                "confidence": 0.9,
                "root_cause": "cause",
                "suggested_fix": "fix"
            }
        }
        
        mock_services["llm"].generate_embedding.side_effect = Exception("API Error")
        
        # Should not raise exception
        await accumulator(state)
        
        mock_services["milvus"].insert_case.assert_not_called()
