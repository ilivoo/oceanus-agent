"""Unit tests for JobCollector node."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from oceanus_agent.models.state import DiagnosisStatus
from oceanus_agent.services.mysql_service import MySQLService
from oceanus_agent.workflow.nodes.collector import JobCollector


class TestJobCollector:
    """Test suite for JobCollector node."""

    @pytest.fixture
    def mock_mysql_service(self):
        """Mock MySQLService."""
        service = MagicMock(spec=MySQLService)
        service.get_pending_exception = AsyncMock()
        return service

    @pytest.fixture
    def collector(self, mock_mysql_service):
        """Create JobCollector instance."""
        return JobCollector(mock_mysql_service)

    @pytest.mark.asyncio
    async def test_collect_job_found(self, collector, mock_mysql_service):
        """Test collecting a job when one is pending."""
        job_info = {
            "exception_id": 1,
            "job_id": "job-123",
            "error_message": "error"
        }
        mock_mysql_service.get_pending_exception.return_value = job_info
        
        state = {}
        new_state = await collector(state)
        
        assert new_state["job_info"] == job_info
        assert new_state["status"] == DiagnosisStatus.IN_PROGRESS
        assert "error" not in new_state or new_state["error"] is None

    @pytest.mark.asyncio
    async def test_collect_job_not_found(self, collector, mock_mysql_service):
        """Test collecting when no job is pending."""
        mock_mysql_service.get_pending_exception.return_value = None
        
        state = {}
        new_state = await collector(state)
        
        assert new_state["job_info"] is None
        assert new_state["status"] == DiagnosisStatus.COMPLETED
        assert "end_time" in new_state

    @pytest.mark.asyncio
    async def test_collect_error(self, collector, mock_mysql_service):
        """Test error handling during collection."""
        mock_mysql_service.get_pending_exception.side_effect = Exception("DB Error")
        
        state = {}
        new_state = await collector(state)
        
        assert new_state["job_info"] is None
        assert new_state["status"] == DiagnosisStatus.FAILED
        assert "DB Error" in new_state["error"]
        assert "end_time" in new_state
