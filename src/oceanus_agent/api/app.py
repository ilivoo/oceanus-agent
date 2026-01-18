from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI

from oceanus_agent.agent import DiagnosisAgent
from oceanus_agent.api.routes import router
from oceanus_agent.config.settings import settings

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle."""
    # Startup
    logger.info("Starting Oceanus Agent API")

    # Initialize the background agent
    agent = DiagnosisAgent(settings)
    app.state.agent = agent

    # Start the scheduler attached to the agent
    # We duplicate the start logic from Agent.start() but integrated into FastAPI
    # Or simpler: just call agent.start() as a background task?
    # agent.start() blocks with a while loop, so we can't await it directly in lifespan.
    # We should extract the scheduler part.

    # Let's modify the agent usage slightly.
    # We'll just start the scheduler here.

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        agent.run_diagnosis_batch,
        trigger=IntervalTrigger(seconds=settings.scheduler.interval_seconds),
        id="diagnosis_batch",
        name="Run Diagnosis Batch",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler

    # Run one batch immediately
    # asyncio.create_task(agent.run_diagnosis_batch())

    yield

    # Shutdown
    logger.info("Shutting down Oceanus Agent API")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await agent.workflow.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Oceanus Diagnosis Agent",
        description="Automated Flink Job Exception Diagnosis",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.include_router(router, prefix="/api/v1")

    return app


app = create_app()
