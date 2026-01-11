# Oceanus Agent

**Oceanus Agent** is an intelligent system designed to diagnose exceptions in Flink jobs using Large Language Models (LLMs). It automates the analysis of job failures (checkpoint failures, backpressure, etc.), suggests fixes, and accumulates knowledge over time.

## Project Overview

- **Purpose**: Automate diagnosis and repair suggestions for Flink job exceptions.
- **Core Logic**: Uses `LangGraph` to orchestrate a diagnosis workflow (`collect` -> `retrieve` -> `diagnose` -> `store` -> `accumulate`).
- **Key Features**:
    - **RAG-enhanced diagnosis**: Retrieves historical cases and documentation from Milvus.
    - **Self-improving**: High-confidence diagnoses are added back to the knowledge base.
    - **Structured output**: Provides root causes, fix steps, and priority levels.

## Technical Stack

- **Language**: Python 3.11+
- **Agent Framework**: LangGraph, LangSmith
- **LLM**: OpenAI GPT-4o-mini (default)
- **Vector DB**: Milvus
- **Relational DB**: MySQL (Async/Sync)
- **Infrastructure**: Docker, Kubernetes

## Key Files & Directories

- `src/oceanus_agent/workflow/graph.py`: Defines the LangGraph workflow structure.
- `src/oceanus_agent/workflow/nodes/`: Implementation of individual workflow steps (Collector, Retriever, Diagnoser, Storer, Accumulator).
- `src/oceanus_agent/config/settings.py`: Configuration using Pydantic Settings.
- `src/oceanus_agent/config/prompts.py`: LLM prompts for diagnosis.
- `deploy/docker/docker-compose.yml`: Local development infrastructure (MySQL, Milvus, MinIO, Etcd).
- `scripts/`: Database initialization scripts (`init_db.sql`, `init_milvus.py`).

## Workflow

The diagnosis process follows this state graph:
1.  **Collect**: Fetches job info and exception details from MySQL.
2.  **Retrieve**: Searches Milvus for similar historical cases and relevant documentation.
3.  **Diagnose**: Uses LLM to analyze the context and generate a diagnosis.
    -   *Retry mechanism*: Retries up to 3 times on error.
4.  **Store**: Saves the diagnosis result to MySQL.
5.  **Accumulate**: If confidence is high (>0.8), vectorizes the result and stores it in Milvus for future RAG.

## Development

### Setup

1.  **Environment**:
    ```bash
    cp .env.example .env
    # Configure OPENAI_API_KEY, MYSQL_*, MILVUS_* in .env
    ```

2.  **Dependencies**:
    ```bash
    pip install -e ".[dev]"
    # OR
    pip install -r requirements-dev.txt
    ```

3.  **Infrastructure (Local)**:
    ```bash
    cd deploy/docker
    docker compose up -d
    ```

4.  **Database Init**:
    ```bash
    mysql -h localhost -u oceanus -p oceanus_agent < scripts/init_db.sql
    python scripts/init_milvus.py
    ```

### Common Commands

-   **Run Agent**:
    ```bash
    python -m oceanus_agent
    ```

-   **Run Tests**:
    ```bash
    pytest tests/ -v
    ```

-   **Linting**:
    ```bash
    ruff check src/
    ```

## Configuration

Configuration is handled via environment variables (loaded from `.env`). Key prefixes:
-   `APP_`: General app settings (env, debug, log_level).
-   `MYSQL_`: Database credentials.
-   `MILVUS_`: Vector DB connection and collection names.
-   `OPENAI_`: API key, model, and embedding model.
-   `LANGCHAIN_`: LangSmith tracing.
-   `SCHEDULER_`: Job polling interval.
-   `KNOWLEDGE_`: Thresholds for RAG and accumulation.
