"""Result storage node for the diagnosis workflow."""

from datetime import datetime
from langsmith import traceable
import structlog

from oceanus_agent.models.state import DiagnosisState, DiagnosisStatus
from oceanus_agent.services.mysql_service import MySQLService


logger = structlog.get_logger()


class ResultStorer:
    """Node for storing diagnosis results to MySQL."""

    def __init__(self, mysql_service: MySQLService):
        self.mysql_service = mysql_service

    @traceable(name="store_result")
    async def __call__(self, state: DiagnosisState) -> DiagnosisState:
        """Store diagnosis result to MySQL.

        Args:
            state: Current workflow state.

        Returns:
            Updated state with completion status.
        """
        job_info = state.get("job_info")
        diagnosis_result = state.get("diagnosis_result")

        if not job_info:
            return state

        try:
            if diagnosis_result:
                # Store successful diagnosis
                await self.mysql_service.update_diagnosis_result(
                    exception_id=job_info["exception_id"],
                    diagnosis=diagnosis_result,
                    status="completed"
                )

                logger.info(
                    "Stored diagnosis result",
                    exception_id=job_info["exception_id"],
                    job_id=job_info["job_id"],
                    confidence=diagnosis_result["confidence"]
                )

                return {
                    **state,
                    "status": DiagnosisStatus.COMPLETED,
                    "end_time": datetime.now().isoformat()
                }
            else:
                # Mark as failed
                error_msg = state.get("error", "Unknown error")
                await self.mysql_service.mark_exception_failed(
                    exception_id=job_info["exception_id"],
                    error_message=error_msg
                )

                logger.warning(
                    "Stored failure result",
                    exception_id=job_info["exception_id"],
                    job_id=job_info["job_id"],
                    error=error_msg
                )

                return {
                    **state,
                    "status": DiagnosisStatus.FAILED,
                    "end_time": datetime.now().isoformat()
                }

        except Exception as e:
            logger.exception(
                "Error storing result",
                job_id=job_info["job_id"],
                error=str(e)
            )
            return {
                **state,
                "status": DiagnosisStatus.FAILED,
                "error": f"Storage error: {str(e)}",
                "end_time": datetime.now().isoformat()
            }
