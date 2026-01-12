"""Application entry point for the Oceanus Diagnosis Agent."""

import asyncio
import logging
import signal
import sys
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from oceanus_agent.config.settings import Settings, settings
from oceanus_agent.models.state import DiagnosisStatus
from oceanus_agent.workflow.graph import DiagnosisWorkflow

# Configure basic logging first
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class DiagnosisAgent:
    """Main diagnosis agent application."""

    def __init__(self, app_settings: Settings | None = None):
        self.settings = app_settings or settings
        self.scheduler = AsyncIOScheduler()
        self.workflow = DiagnosisWorkflow(self.settings)
        self.running = False
        self._batch_count = 0

    async def run_diagnosis_batch(self) -> None:
        """Run a batch of diagnosis tasks."""
        self._batch_count += 1
        batch_id = (
            f"batch_{self._batch_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        logger.info(
            "Starting diagnosis batch",
            batch_id=batch_id,
            batch_size=self.settings.scheduler.batch_size,
        )

        processed = 0
        failed = 0

        for i in range(self.settings.scheduler.batch_size):
            try:
                thread_id = f"{batch_id}_{i}"
                result = await self.workflow.run(thread_id)

                job_info = result.get("job_info")
                diagnosis_result = result.get("diagnosis_result")

                if not job_info:
                    logger.info("No more pending exceptions")
                    break

                if result["status"] == DiagnosisStatus.COMPLETED:
                    processed += 1
                    logger.info(
                        "Diagnosis completed",
                        job_id=job_info["job_id"],
                        confidence=diagnosis_result["confidence"]
                        if diagnosis_result
                        else None,
                    )
                else:
                    failed += 1
                    logger.warning(
                        "Diagnosis failed",
                        job_id=job_info["job_id"],
                        error=result.get("error"),
                    )

            except Exception as e:
                failed += 1
                logger.exception("Error in diagnosis batch", error=str(e))

        logger.info(
            "Diagnosis batch completed",
            batch_id=batch_id,
            processed=processed,
            failed=failed,
        )

    async def start(self) -> None:
        """Start the diagnosis agent."""
        logger.info(
            "Starting Oceanus Diagnosis Agent",
            env=self.settings.app.env,
            interval_seconds=self.settings.scheduler.interval_seconds,
            batch_size=self.settings.scheduler.batch_size,
        )

        self.running = True

        # Configure scheduled job
        self.scheduler.add_job(
            self.run_diagnosis_batch,
            trigger=IntervalTrigger(seconds=self.settings.scheduler.interval_seconds),
            id="diagnosis_batch",
            name="Run Diagnosis Batch",
            replace_existing=True,
        )

        self.scheduler.start()

        # Run immediately on start
        await self.run_diagnosis_batch()

        # Keep running
        while self.running:
            await asyncio.sleep(1)

    async def stop(self) -> None:
        """Stop the diagnosis agent."""
        logger.info("Stopping Oceanus Diagnosis Agent")
        self.running = False

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        await self.workflow.close()


async def main() -> None:
    """Main entry point."""
    agent = DiagnosisAgent()

    # Setup signal handlers
    loop = asyncio.get_event_loop()

    def signal_handler() -> None:
        asyncio.create_task(agent.stop())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        await agent.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        await agent.stop()


def run() -> None:
    """Run the application."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
