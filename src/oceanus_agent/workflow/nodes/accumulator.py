"""Knowledge accumulation node for the diagnosis workflow."""

import re
import uuid
from typing import Any

import structlog
from langsmith import traceable

from oceanus_agent.config.settings import KnowledgeSettings
from oceanus_agent.models.state import DiagnosisState
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.services.milvus_service import MilvusService
from oceanus_agent.services.mysql_service import MySQLService

logger = structlog.get_logger()


class KnowledgeAccumulator:
    """Node for accumulating high-confidence diagnoses into the knowledge base."""

    def __init__(
        self,
        mysql_service: MySQLService,
        milvus_service: MilvusService,
        llm_service: LLMService,
        settings: KnowledgeSettings,
    ):
        self.mysql_service = mysql_service
        self.milvus_service = milvus_service
        self.llm_service = llm_service
        self.settings = settings

    @traceable(name="accumulate_knowledge")
    async def __call__(self, state: DiagnosisState) -> DiagnosisState:
        """Accumulate high-confidence diagnosis into the knowledge base.

        Args:
            state: Current workflow state.

        Returns:
            Unchanged state (accumulation is a side effect).
        """
        job_info = state.get("job_info")
        diagnosis = state.get("diagnosis_result")

        if not job_info or not diagnosis:
            return state

        # Only accumulate high-confidence diagnoses
        if diagnosis["confidence"] < self.settings.confidence_threshold:
            logger.debug(
                "Skipping knowledge accumulation (low confidence)",
                job_id=job_info["job_id"],
                confidence=diagnosis["confidence"],
                threshold=self.settings.confidence_threshold,
            )
            return state

        try:
            # Generate case ID
            case_id = f"case_{uuid.uuid4().hex[:12]}"

            # Extract error pattern
            error_pattern = self._extract_error_pattern(job_info["error_message"])

            # Build case text for embedding
            case_text = self._build_case_text(job_info, diagnosis)

            # Generate embedding
            embedding = await self.llm_service.generate_embedding(case_text)

            # Insert into Milvus
            await self.milvus_service.insert_case(
                case_id=case_id,
                vector=embedding,
                error_type=job_info.get("error_type") or "other",
                error_pattern=error_pattern,
                root_cause=diagnosis["root_cause"],
                solution=diagnosis["suggested_fix"],
            )

            # Insert metadata into MySQL
            await self.mysql_service.insert_knowledge_case(
                case_id=case_id,
                error_type=job_info.get("error_type") or "other",
                error_pattern=error_pattern,
                root_cause=diagnosis["root_cause"],
                solution=diagnosis["suggested_fix"],
                source_exception_id=job_info["exception_id"],
                source_type="auto",
            )

            logger.info(
                "Accumulated knowledge case",
                case_id=case_id,
                job_id=job_info["job_id"],
                confidence=diagnosis["confidence"],
            )

        except Exception as e:
            # Don't fail the workflow for accumulation errors
            logger.warning(
                "Error accumulating knowledge", job_id=job_info["job_id"], error=str(e)
            )

        return state

    def _extract_error_pattern(self, error_message: str) -> str:
        """Extract generalized error pattern from error message.

        Args:
            error_message: Raw error message.

        Returns:
            Generalized error pattern.
        """
        pattern = error_message

        # Replace numbers with placeholder
        pattern = re.sub(r"\d+", "<NUM>", pattern)

        # Replace UUIDs with placeholder
        pattern = re.sub(
            r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",
            "<UUID>",
            pattern,
        )

        # Replace timestamps with placeholder
        pattern = re.sub(
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}", "<TIMESTAMP>", pattern
        )

        # Replace hex addresses with placeholder
        pattern = re.sub(r"0x[a-fA-F0-9]+", "<ADDR>", pattern)

        # Replace file paths with placeholder
        pattern = re.sub(r"/[\w/.-]+", "<PATH>", pattern)

        # Limit length
        return pattern[:2000]

    def _build_case_text(self, job_info: Any, diagnosis: Any) -> str:
        """Build case text for embedding generation.

        Args:
            job_info: Job information.
            diagnosis: Diagnosis result.

        Returns:
            Combined text for embedding.
        """
        return f"""Error Type: {job_info.get("error_type", "unknown")}
Error Message: {job_info["error_message"][:1000]}
Root Cause: {diagnosis["root_cause"]}
Solution: {diagnosis["suggested_fix"]}""".strip()
