"""MySQL database service for exception and knowledge case management."""

from typing import Optional, List
from datetime import datetime
import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

from oceanus_agent.config.settings import MySQLSettings
from oceanus_agent.models.state import JobInfo, DiagnosisResult


logger = structlog.get_logger()


class MySQLService:
    """Service for MySQL database operations."""

    def __init__(self, settings: MySQLSettings):
        self.settings = settings
        self.engine = create_async_engine(
            settings.url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    async def get_pending_exception(self) -> Optional[JobInfo]:
        """Get one pending exception for diagnosis.

        Returns:
            JobInfo if found, None otherwise.
        """
        async with self.async_session() as session:
            query = text("""
                SELECT id, job_id, job_name, job_type, job_config,
                       error_message, error_type, created_at
                FROM flink_job_exceptions
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            """)

            result = await session.execute(query)
            row = result.fetchone()

            if not row:
                return None

            # Mark as in_progress
            update_query = text("""
                UPDATE flink_job_exceptions
                SET status = 'in_progress'
                WHERE id = :id
            """)
            await session.execute(update_query, {"id": row[0]})
            await session.commit()

            # Parse job_config
            job_config = row[4]
            if isinstance(job_config, str):
                try:
                    job_config = json.loads(job_config)
                except json.JSONDecodeError:
                    job_config = {}

            return JobInfo(
                exception_id=row[0],
                job_id=row[1],
                job_name=row[2],
                job_type=row[3],
                job_config=job_config,
                error_message=row[5],
                error_type=row[6],
                created_at=str(row[7]) if row[7] else ""
            )

    async def update_diagnosis_result(
        self,
        exception_id: int,
        diagnosis: DiagnosisResult,
        status: str = "completed"
    ) -> None:
        """Update exception with diagnosis result.

        Args:
            exception_id: ID of the exception record.
            diagnosis: Diagnosis result to store.
            status: New status (completed or failed).
        """
        async with self.async_session() as session:
            query = text("""
                UPDATE flink_job_exceptions
                SET status = :status,
                    suggested_fix = :suggested_fix,
                    diagnosis_confidence = :confidence,
                    diagnosed_at = :diagnosed_at
                WHERE id = :id
            """)

            suggested_fix = json.dumps({
                "root_cause": diagnosis["root_cause"],
                "detailed_analysis": diagnosis["detailed_analysis"],
                "suggested_fix": diagnosis["suggested_fix"],
                "priority": diagnosis["priority"],
                "related_docs": diagnosis["related_docs"]
            }, ensure_ascii=False)

            await session.execute(query, {
                "id": exception_id,
                "status": status,
                "suggested_fix": suggested_fix,
                "confidence": diagnosis["confidence"],
                "diagnosed_at": datetime.now()
            })
            await session.commit()

            logger.info(
                "Updated diagnosis result",
                exception_id=exception_id,
                status=status,
                confidence=diagnosis["confidence"]
            )

    async def mark_exception_failed(
        self,
        exception_id: int,
        error_message: str
    ) -> None:
        """Mark an exception as failed.

        Args:
            exception_id: ID of the exception record.
            error_message: Error message to store.
        """
        async with self.async_session() as session:
            query = text("""
                UPDATE flink_job_exceptions
                SET status = 'failed',
                    suggested_fix = :error_message,
                    diagnosed_at = :diagnosed_at
                WHERE id = :id
            """)

            await session.execute(query, {
                "id": exception_id,
                "error_message": json.dumps(
                    {"error": error_message},
                    ensure_ascii=False
                ),
                "diagnosed_at": datetime.now()
            })
            await session.commit()

            logger.warning(
                "Marked exception as failed",
                exception_id=exception_id,
                error=error_message
            )

    async def insert_knowledge_case(
        self,
        case_id: str,
        error_type: str,
        error_pattern: str,
        root_cause: str,
        solution: str,
        source_exception_id: Optional[int] = None,
        source_type: str = "auto"
    ) -> None:
        """Insert a new knowledge case.

        Args:
            case_id: Unique case identifier.
            error_type: Type of error.
            error_pattern: Generalized error pattern.
            root_cause: Root cause of the error.
            solution: Solution to fix the error.
            source_exception_id: ID of source exception if auto-generated.
            source_type: Source type (manual or auto).
        """
        async with self.async_session() as session:
            query = text("""
                INSERT INTO knowledge_cases
                (case_id, error_type, error_pattern, root_cause, solution,
                 source_exception_id, source_type, verified)
                VALUES
                (:case_id, :error_type, :error_pattern, :root_cause, :solution,
                 :source_exception_id, :source_type, FALSE)
            """)

            await session.execute(query, {
                "case_id": case_id,
                "error_type": error_type,
                "error_pattern": error_pattern,
                "root_cause": root_cause,
                "solution": solution,
                "source_exception_id": source_exception_id,
                "source_type": source_type
            })
            await session.commit()

            logger.info(
                "Inserted knowledge case",
                case_id=case_id,
                error_type=error_type,
                source_type=source_type
            )

    async def get_pending_count(self) -> int:
        """Get count of pending exceptions.

        Returns:
            Number of pending exceptions.
        """
        async with self.async_session() as session:
            query = text("""
                SELECT COUNT(*) FROM flink_job_exceptions
                WHERE status = 'pending'
            """)
            result = await session.execute(query)
            return result.scalar() or 0

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()
