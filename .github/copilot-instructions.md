# Oceanus Agent - GitHub Copilot Instructions

## Project Overview

Oceanus Agent is an LLM-powered intelligent diagnostic system for Flink job exceptions. It uses LangGraph for workflow orchestration, automatically analyzes job failures, retrieves historical cases from a knowledge base, and provides root cause analysis with repair suggestions.

## Tech Stack

- **Language**: Python 3.11+
- **Agent Framework**: LangGraph, LangSmith
- **LLM Integration**: LangChain, OpenAI GPT-4o-mini
- **Vector Database**: Milvus (pymilvus)
- **Relational Database**: MySQL (Async SQLAlchemy + aiomysql)
- **Web Framework**: FastAPI, Uvicorn
- **Configuration**: Pydantic Settings

## Code Style Guidelines

### Type Annotations (Required)

All functions must include complete type hints:

```python
# Correct
async def process_job(
    session: AsyncSession,
    job_id: str,
    options: ProcessOptions | None = None,
) -> DiagnosisResult:
    ...

# Incorrect - missing type hints
async def process_job(session, job_id, options=None):
    ...
```

### Async First

All database and external API operations must use async/await:

```python
# Correct
async def get_pending_jobs(session: AsyncSession) -> list[JobInfo]:
    result = await session.execute(select(Job).where(Job.status == "pending"))
    return [JobInfo.model_validate(row) for row in result.scalars()]

# Incorrect - synchronous operation
def get_pending_jobs(session: Session) -> list[JobInfo]:
    result = session.execute(select(Job).where(Job.status == "pending"))
    ...
```

### Pydantic Models (Required)

All data transfer must use Pydantic Models. Never use raw dictionaries:

```python
# Correct
class JobInfo(BaseModel):
    job_id: str = Field(..., description="Flink job ID")
    error_message: str = Field(..., description="Error message")
    timestamp: datetime = Field(default_factory=datetime.now)

async def process(job: JobInfo) -> DiagnosisResult:
    ...

# Incorrect - raw dictionary
async def process(job: dict) -> dict:
    ...
```

### Formatting Standards

- **Line length**: 88 characters
- **Indentation**: 4 spaces (no tabs)
- **Quotes**: Double quotes for strings
- **Trailing commas**: Required for multi-line collections
- **Import order**: stdlib -> third-party -> local (blank line between groups)

```python
# Correct import order
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from oceanus_agent.models.diagnosis import DiagnosisResult
from oceanus_agent.services.llm_service import LLMService
```

### Naming Conventions

- **Classes**: PascalCase (`DiagnosisResult`, `LLMService`)
- **Functions/Variables**: snake_case (`get_pending_jobs`, `error_message`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT`)

## Project Structure

```
src/oceanus_agent/
├── api/              # FastAPI routes and application entry
├── config/           # Configuration center
│   ├── settings.py   # Pydantic settings definitions
│   └── prompts.py    # LLM prompt templates
├── models/           # Pydantic data models
│   ├── diagnosis.py  # Diagnosis result models
│   ├── state.py      # Workflow state definitions
│   └── knowledge.py  # Knowledge base entities
├── services/         # External service integrations
│   ├── llm_service.py    # OpenAI API wrapper
│   ├── milvus_service.py # Vector retrieval service
│   └── mysql_service.py  # Database operations
└── workflow/         # LangGraph workflow definitions
    ├── graph.py      # Graph construction and routing
    └── nodes/        # Workflow node implementations
```

## Common Patterns

### Service Class Pattern

```python
class MyService:
    """Service class for external integrations."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: Client | None = None

    async def initialize(self) -> None:
        """Initialize the service connection."""
        self._client = await Client.connect(self.settings.endpoint)

    async def close(self) -> None:
        """Clean up resources."""
        if self._client:
            await self._client.close()

    async def process(self, input_data: InputModel) -> OutputModel:
        """Process input and return output."""
        if not self._client:
            raise RuntimeError("Service not initialized")
        result = await self._client.execute(input_data.to_request())
        return OutputModel.model_validate(result)
```

### Workflow Node Pattern

```python
async def my_node(state: DiagnosisState) -> dict[str, Any]:
    """
    Workflow node for processing diagnosis step.

    Args:
        state: Current workflow state

    Returns:
        State updates to apply
    """
    # Extract input from state
    job_info = state["job_info"]
    if not job_info:
        return {"error": "No job info available"}

    # Process logic
    try:
        result = await process_job(job_info)
    except Exception as e:
        logger.error("processing_failed", error=str(e), job_id=job_info.job_id)
        return {"error": str(e), "retry_count": state["retry_count"] + 1}

    # Return state updates
    return {
        "diagnosis_result": result,
        "status": DiagnosisStatus.COMPLETED,
    }
```

### Error Handling Pattern

```python
from oceanus_agent.models.errors import DiagnosisError, RetryableError

async def robust_operation(data: InputModel) -> OutputModel:
    """Operation with proper error handling."""
    try:
        result = await external_api.call(data)
    except TimeoutError as e:
        # Retryable error
        raise RetryableError(f"API timeout: {e}") from e
    except ValidationError as e:
        # Non-retryable error
        raise DiagnosisError(f"Invalid response: {e}") from e

    return OutputModel.model_validate(result)
```

### Structured Logging Pattern

```python
import structlog

logger = structlog.get_logger(__name__)

async def process_job(job: JobInfo) -> DiagnosisResult:
    """Process job with structured logging."""
    logger.info(
        "job_processing_started",
        job_id=job.job_id,
        error_type=job.error_type,
    )

    try:
        result = await diagnose(job)
        logger.info(
            "job_processing_completed",
            job_id=job.job_id,
            confidence=result.confidence,
            duration_ms=result.duration_ms,
        )
        return result
    except Exception as e:
        logger.error(
            "job_processing_failed",
            job_id=job.job_id,
            error=str(e),
            exc_info=True,
        )
        raise
```

## Prohibited Practices

1. **No raw dictionaries** for data transfer - use Pydantic models
2. **No synchronous database operations** - always use async
3. **No hardcoded secrets** - use environment variables via Settings
4. **No ignored type errors** - fix all mypy warnings
5. **No wildcard imports** - never use `from xxx import *`
6. **No bare except** - always specify exception types
7. **No mutable default arguments** - use `Field(default_factory=list)`

```python
# Incorrect examples - DO NOT DO THIS
data = {"key": "value"}  # Use Pydantic model instead
session.execute(query)   # Use await session.execute()
API_KEY = "sk-xxx"       # Use settings.api_key
except:                  # Use except Exception:
def func(items=[]):      # Use items: list | None = None
```

## Testing Guidelines

- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/`
- Use pytest and unittest.mock
- Target 70% code coverage
- Mock all external services in unit tests

```python
# Test example
import pytest
from unittest.mock import AsyncMock, patch

from oceanus_agent.services.llm_service import LLMService


@pytest.fixture
def mock_openai():
    with patch("oceanus_agent.services.llm_service.AsyncOpenAI") as mock:
        mock.return_value.chat.completions.create = AsyncMock(
            return_value=MockResponse(content="diagnosis result")
        )
        yield mock


async def test_generate_diagnosis(mock_openai):
    service = LLMService(settings)
    result = await service.generate_diagnosis(job_info)
    assert result.confidence > 0.5
```

## Commit Message Format

Use Conventional Commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Build/tooling changes

Example: `feat(workflow): add retry mechanism for diagnosis node`

## Additional Resources

- Project documentation: `docs/`
- Design documents: `docs/design/`
- API documentation: `docs/api/`
- Configuration example: `.env.example`
