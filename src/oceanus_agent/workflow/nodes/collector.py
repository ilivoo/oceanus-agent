"""Data collection node for the diagnosis workflow."""

from datetime import datetime

import structlog
from langsmith import traceable

from oceanus_agent.models.state import DiagnosisState, DiagnosisStatus
from oceanus_agent.services.mysql_service import MySQLService

logger = structlog.get_logger()


class JobCollector:
    """Node for collecting pending job exceptions from MySQL."""

    def __init__(self, mysql_service: MySQLService):
        self.mysql_service = mysql_service

    @traceable(name="collect_job_exception")
    async def __call__(self, state: DiagnosisState) -> DiagnosisState:
        """Collect a pending job exception.

        Args:
            state: Current workflow state.

        Returns:
            Updated state with job info or None if no pending jobs.
        """
        try:
            job_info = await self.mysql_service.get_pending_exception()

            if job_info is None:
                logger.info("No pending exceptions to process")
                return {
                    **state,
                    "job_info": None,
                    "status": DiagnosisStatus.COMPLETED,
                    "end_time": datetime.now().isoformat()
                }

            logger.info(
                "Collected job exception",
                exception_id=job_info["exception_id"],
                job_id=job_info["job_id"],
                error_type=job_info.get("error_type")
            )

            return {
                **state,
                "job_info": job_info,
                "status": DiagnosisStatus.IN_PROGRESS
            }

        except Exception as e:
            logger.exception("Error collecting job exception", error=str(e))
            return {
                **state,
                "job_info": None,
                "status": DiagnosisStatus.FAILED,
                "error": f"Collection error: {str(e)}",
                "end_time": datetime.now().isoformat()
            }
