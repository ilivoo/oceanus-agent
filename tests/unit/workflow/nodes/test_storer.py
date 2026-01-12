"""Unit tests for ResultStorer node."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from oceanus_agent.models.state import DiagnosisStatus
from oceanus_agent.services.mysql_service import MySQLService
from oceanus_agent.workflow.nodes.storer import ResultStorer


class TestResultStorer:
    """Test suite for ResultStorer node."""

    @pytest.fixture
    def mock_mysql_service(self):
        """Mock MySQLService."""
        service = MagicMock(spec=MySQLService)
        service.update_diagnosis_result = AsyncMock()
        service.mark_exception_failed = AsyncMock()
        return service

    @pytest.fixture
    def storer(self, mock_mysql_service):
        """Create ResultStorer instance."""
        return ResultStorer(mock_mysql_service)

    @pytest.mark.asyncio
    async def test_store_success(self, storer, mock_mysql_service):
        """Test storing successful diagnosis."""
        state = {
            "job_info": {
                "exception_id": 1,
                "job_id": "job-1"
            },
            "diagnosis_result": {
                "confidence": 0.9
            }
        }
        
        new_state = await storer(state)
        
        mock_mysql_service.update_diagnosis_result.assert_called_once()
        assert new_state["status"] == DiagnosisStatus.COMPLETED
        assert "end_time" in new_state

    @pytest.mark.asyncio
    async def test_store_failure(self, storer, mock_mysql_service):
        """Test storing failure when diagnosis is missing."""
        state = {
            "job_info": {
                "exception_id": 1,
                "job_id": "job-1"
            },
            "diagnosis_result": None,
            "error": "Diagnosis failed"
        }
        
        new_state = await storer(state)
        
        mock_mysql_service.mark_exception_failed.assert_called_once()
        call_args = mock_mysql_service.mark_exception_failed.call_args[1]
        assert call_args["error_message"] == "Diagnosis failed"
        
        assert new_state["status"] == DiagnosisStatus.FAILED
        assert "end_time" in new_state

    @pytest.mark.asyncio
    async def test_store_db_error(self, storer, mock_mysql_service):
        """Test handling DB error during storage."""
        state = {
            "job_info": {
                "exception_id": 1,
                "job_id": "job-1"
            },
            "diagnosis_result": {"confidence": 0.9}
        }
        
        mock_mysql_service.update_diagnosis_result.side_effect = Exception("DB Error")
        
        new_state = await storer(state)
        
        assert new_state["status"] == DiagnosisStatus.FAILED
        assert "Storage error" in new_state["error"]
