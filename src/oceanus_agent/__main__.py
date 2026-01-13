"""Application entry point for the Oceanus Diagnosis Agent."""

import logging
import sys

import structlog
import uvicorn

from oceanus_agent.config.settings import settings

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


def main() -> None:
    """Main entry point starting the FastAPI server and background agent."""
    logger.info("Starting Oceanus Agent Server", debug=settings.app.debug)

    uvicorn.run(
        "oceanus_agent.api.app:app",
        host="0.0.0.0",  # nosec
        port=8000,
        reload=settings.app.debug,
        log_level=settings.app.log_level.lower(),
    )


if __name__ == "__main__":
    main()
