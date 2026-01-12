"""Unit tests for LLMDiagnoser node."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from oceanus_agent.models.state import DiagnosisStatus
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.workflow.nodes.diagnoser import LLMDiagnoser


class TestLLMDiagnoser:
    """Test suite for LLMDiagnoser node."""

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLMService."""
        service = MagicMock(spec=LLMService)
        service.classify_error = AsyncMock()
        service.generate_diagnosis = AsyncMock()
        return service

    @pytest.fixture
    def diagnoser(self, mock_llm_service):
        """Create LLMDiagnoser instance."""
        return LLMDiagnoser(mock_llm_service, max_retries=3)

    @pytest.mark.asyncio
    async def test_diagnose_success(self, diagnoser, mock_llm_service):
        """Test successful diagnosis."""
        state = {
            "job_info": {
                "job_id": "job-1",
                "error_message": "timeout"
            },
            "retrieved_context": {}
        }
        
        # Mock classify
        mock_llm_service.classify_error.return_value = "checkpoint_failure"
        
        # Mock diagnosis
        diagnosis_result = {
            "root_cause": "network",
            "suggested_fix": "retry",
            "confidence": 0.9,
            "priority": "high"
        }
        mock_llm_service.generate_diagnosis.return_value = diagnosis_result
        
        new_state = await diagnoser(state)
        
        assert new_state["diagnosis_result"] == diagnosis_result
        assert new_state["job_info"]["error_type"] == "checkpoint_failure"
        assert new_state["status"] == DiagnosisStatus.IN_PROGRESS
        assert new_state["retry_count"] == 0

    @pytest.mark.asyncio
    async def test_diagnose_retry_logic(self, diagnoser, mock_llm_service):
        """Test retry logic on failure."""
        state = {
            "job_info": {
                "job_id": "job-1",
                "error_message": "error"
            },
            "retry_count": 0
        }
        
        mock_llm_service.classify_error.side_effect = Exception("LLM Error")
        
        new_state = await diagnoser(state)
        
        assert new_state["retry_count"] == 1
        assert "LLM Error" in new_state["error"]
        assert new_state.get("status") != DiagnosisStatus.FAILED

    @pytest.mark.asyncio
    async def test_diagnose_max_retries_exceeded(self, diagnoser, mock_llm_service):
        """Test failure after max retries."""
        state = {
            "job_info": {
                "job_id": "job-1",
                "error_message": "error"
            },
            "retry_count": 2  # Max is 3, so next failure hits max
        }
        
        mock_llm_service.classify_error.side_effect = Exception("LLM Error")
        
        new_state = await diagnoser(state)
        
        assert new_state["retry_count"] == 3
        assert new_state["status"] == DiagnosisStatus.FAILED
        assert "Diagnosis failed after 3 retries" in new_state["error"]
        assert "end_time" in new_state
