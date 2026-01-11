"""LLM diagnosis node for the diagnosis workflow."""

from datetime import datetime

import structlog
from langsmith import traceable

from oceanus_agent.models.state import DiagnosisState, DiagnosisStatus
from oceanus_agent.services.llm_service import LLMService

logger = structlog.get_logger()


class LLMDiagnoser:
    """Node for generating diagnosis using LLM."""

    def __init__(self, llm_service: LLMService, max_retries: int = 3):
        self.llm_service = llm_service
        self.max_retries = max_retries

    @traceable(name="diagnose_exception")
    async def __call__(self, state: DiagnosisState) -> DiagnosisState:
        """Generate diagnosis for the job exception.

        Args:
            state: Current workflow state.

        Returns:
            Updated state with diagnosis result.
        """
        job_info = state.get("job_info")

        if not job_info:
            return state

        retry_count = state.get("retry_count", 0)

        try:
            # Classify error type if not already set
            if not job_info.get("error_type"):
                error_type = await self.llm_service.classify_error(
                    job_info["error_message"]
                )
                job_info = {**job_info, "error_type": error_type}

            # Generate diagnosis
            diagnosis_result = await self.llm_service.generate_diagnosis(
                job_info=job_info,
                context=state.get("retrieved_context")
            )

            logger.info(
                "Generated diagnosis",
                job_id=job_info["job_id"],
                confidence=diagnosis_result["confidence"],
                priority=diagnosis_result["priority"]
            )

            return {
                **state,
                "job_info": job_info,
                "diagnosis_result": diagnosis_result,
                "status": DiagnosisStatus.IN_PROGRESS,
                "error": None,
                "retry_count": 0
            }

        except Exception as e:
            new_retry_count = retry_count + 1
            logger.warning(
                "Error generating diagnosis",
                job_id=job_info["job_id"],
                error=str(e),
                retry_count=new_retry_count
            )

            if new_retry_count >= self.max_retries:
                return {
                    **state,
                    "status": DiagnosisStatus.FAILED,
                    "error": f"Diagnosis failed after {new_retry_count} retries: {str(e)}",
                    "end_time": datetime.now().isoformat(),
                    "retry_count": new_retry_count
                }

            return {
                **state,
                "error": str(e),
                "retry_count": new_retry_count
            }
