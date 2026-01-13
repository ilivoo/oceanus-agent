# Oceanus Agent

**Oceanus Agent** is an intelligent system designed to diagnose exceptions in Flink jobs using Large Language Models (LLMs). It automates the analysis of job failures, suggests fixes, and accumulates knowledge over time to improve future diagnoses.

## Project Overview

- **Purpose**: Automate diagnosis and repair suggestions for Flink job exceptions.
- **Core Logic**: Uses `LangGraph` to orchestrate a cyclic diagnosis workflow with state management and persistence.
- **Key Features**:
    - **RAG-enhanced Diagnosis**: Retrieves historical cases and documentation from Milvus to provide context-aware analysis.
    - **Self-improving Knowledge Base**: High-confidence diagnoses are automatically vectorized and stored back into the system.
    - **Robust Workflow**: Includes retry mechanisms, error handling, and state checkpointing.
    - **Structured Output**: Delivers standardized diagnosis results including root cause, detailed analysis, and actionable fix steps.

## Technical Stack

- **Language**: Python 3.11+
- **Agent Framework**: LangGraph, LangSmith
- **LLM Integration**: LangChain, OpenAI GPT-4o-mini
- **Vector Database**: Milvus (pymilvus)
- **Relational Database**: MySQL (Async via SQLAlchemy + aiomysql)
- **API/Server**: FastAPI, Uvicorn
- **Scheduling**: APScheduler
- **Configuration**: Pydantic Settings
- **Infrastructure**: Docker, Kubernetes

## Project Structure

```text
/home/debian/project/oceanus-agent/
├── src/oceanus_agent/
│   ├── config/             # Configuration and prompts
│   │   ├── settings.py     # Pydantic settings definition
│   │   └── prompts.py      # LLM system and user prompts
│   ├── models/             # Pydantic data models
│   │   ├── diagnosis.py    # Output structures
│   │   ├── state.py        # Workflow state definitions
│   │   └── knowledge.py    # Knowledge base entities
│   ├── services/           # External system integrations
│   │   ├── llm_service.py  # OpenAI wrapper for chat & embeddings
│   │   ├── milvus_service.py # Vector DB operations
│   │   └── mysql_service.py  # Relational DB operations
│   └── workflow/           # LangGraph workflow definition
│       ├── graph.py        # Main graph construction & routing
│       └── nodes/          # Individual workflow steps
│           ├── collector.py    # Fetches pending exceptions
│           ├── retriever.py    # RAG context retrieval
│           ├── diagnoser.py    # LLM analysis execution
│           ├── storer.py       # Result persistence
│           └── accumulator.py  # Knowledge base update
├── deploy/                 # Deployment configurations
├── scripts/                # Database initialization scripts
└── tests/                  # Unit and integration tests
```

## Workflow Architecture

The diagnosis process is modeled as a state graph with the following nodes:

1.  **Collect**: Fetches a pending job exception from MySQL.
    -   *Next*: `retrieve` if job found, else `END`.
2.  **Retrieve**: Searches Milvus for similar historical cases and relevant documentation snippets based on the error message.
    -   *Next*: `diagnose`.
3.  **Diagnose**: Uses LLM (GPT-4o-mini) to analyze the job info and retrieved context.
    -   *Retry Policy*: Retries up to 3 times on transient errors.
    -   *Next*: `store` on success, `handle_error` on failure.
4.  **Store**: Saves the structured diagnosis result to MySQL.
    -   *Next*: `accumulate`.
5.  **Accumulate**: If the diagnosis confidence > 0.8, vectorizes the result and adds it to Milvus for future reference.
    -   *Next*: `END`.
6.  **Handle Error**: Captures workflow errors and updates the job status to failed.

## Configuration

Configuration is managed via environment variables (loaded from `.env`).

| Prefix | Category | Key Settings |
| :--- | :--- | :--- |
| `APP_` | General | `ENV`, `DEBUG`, `LOG_LEVEL` |
| `MYSQL_` | Database | `HOST`, `PORT`, `USER`, `PASSWORD`, `DATABASE` |
| `MILVUS_` | Vector DB | `HOST`, `PORT`, `TOKEN`, `CASES_COLLECTION`, `DOCS_COLLECTION` |
| `OPENAI_` | LLM | `API_KEY`, `MODEL`, `EMBEDDING_MODEL`, `TEMPERATURE` |
| `LANGCHAIN_` | Tracing | `TRACING_V2`, `API_KEY`, `PROJECT` |
| `SCHEDULER_` | Job Control | `INTERVAL_SECONDS`, `BATCH_SIZE` |
| `KNOWLEDGE_` | RAG | `CONFIDENCE_THRESHOLD`, `MAX_SIMILAR_CASES` |

## Development

### Setup

1.  **Environment**:
    ```bash
    cp .env.example .env
    # Edit .env with your credentials
    ```

2.  **Dependencies**:
    ```bash
    pip install -e ".[dev]"
    pre-commit install  # Important: Install git hooks
    ```

3.  **Local Infrastructure**:
    ```bash
    cd deploy/docker
    docker compose up -d
    ```

4.  **Database Initialization**:
    ```bash
    # Initialize MySQL schema
    mysql -h 127.0.0.1 -P 3306 -u root -p oceanus_agent < scripts/init_db.sql

    # Initialize Milvus collections
    python scripts/init_milvus.py
    ```

### Common Commands

-   **Run Agent**: `python -m oceanus_agent`
-   **Run Tests**: `pytest tests/ -v`
-   **Code Quality**: `pre-commit run --all-files` (MANDATORY)

## AI Agent Rules

**Mandatory Workflow for AI Agents:**

### Step 1: Environment Setup
Always use `.venv/bin/python` or related binaries.

### Step 2: Code Formatting (MANDATORY)

> **CRITICAL**: You MUST format code before considering any task complete.
> Unformatted code will be REJECTED by CI.

After modifying any code:

```bash
# Format first
./.venv/bin/ruff format src/ tests/
./.venv/bin/ruff check --fix src/ tests/

# Then run full pre-commit
./.venv/bin/pre-commit run --all-files
```

**You MUST**:
- Run pre-commit after EVERY code modification
- Fix ALL reported errors (do not ignore them)
- Re-run until all checks pass

**You MUST NOT**:
- Claim a task is complete without running pre-commit
- Use `--no-verify` to skip checks
- Ignore linting or type errors

### Step 3: Testing
Run relevant tests using `pytest` to ensure no regressions.

### Formatting Standards
- Line length: 88 characters (Ruff/Black standard)
- Indentation: 4 spaces (Python)
- Quotes: Double quotes preferred
- Import ordering: isort rules (managed by Ruff)
