"""Global pytest fixtures for Oceanus Agent tests."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import SecretStr

from oceanus_agent.config.settings import (
    KnowledgeSettings,
    MilvusSettings,
    MySQLSettings,
    OpenAISettings,
)
from oceanus_agent.models.state import (
    DiagnosisResult,
    DiagnosisState,
    DiagnosisStatus,
    JobInfo,
    RetrievedCase,
    RetrievedContext,
    RetrievedDoc,
)

# ============ Settings Fixtures ============


@pytest.fixture
def mysql_settings() -> MySQLSettings:
    """测试用 MySQL 配置."""
    return MySQLSettings(
        host="localhost",
        port=3306,
        user="test",
        password=SecretStr("test"),
        database="test_oceanus",
    )


@pytest.fixture
def milvus_settings() -> MilvusSettings:
    """测试用 Milvus 配置."""
    return MilvusSettings(
        host="localhost",
        port=19530,
        cases_collection="test_flink_cases",
        docs_collection="test_flink_docs",
    )


@pytest.fixture
def openai_settings() -> OpenAISettings:
    """测试用 OpenAI 配置."""
    return OpenAISettings(
        api_key=SecretStr("test-api-key"),
        model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
    )


@pytest.fixture
def knowledge_settings() -> KnowledgeSettings:
    """测试用知识配置."""
    return KnowledgeSettings(
        confidence_threshold=0.8,
        max_similar_cases=3,
        max_doc_snippets=3,
    )


# ============ Mock Service Fixtures ============


@pytest.fixture
def mock_mysql_service() -> AsyncMock:
    """Mock MySQL Service."""
    service = AsyncMock()
    service.get_pending_exception = AsyncMock(return_value=None)
    service.update_diagnosis_result = AsyncMock()
    service.mark_exception_failed = AsyncMock()
    service.insert_knowledge_case = AsyncMock()
    service.close = AsyncMock()
    return service


@pytest.fixture
def mock_milvus_service() -> MagicMock:
    """Mock Milvus Service."""
    service = MagicMock()
    service.search_similar_cases = AsyncMock(return_value=[])
    service.search_doc_snippets = AsyncMock(return_value=[])
    service.insert_case = AsyncMock()
    service.close = MagicMock()
    return service


@pytest.fixture
def mock_llm_service() -> AsyncMock:
    """Mock LLM Service."""
    service = AsyncMock()
    service.generate_embedding = AsyncMock(return_value=[0.1] * 1536)
    service.generate_diagnosis = AsyncMock(
        return_value={
            "root_cause": "Test root cause",
            "detailed_analysis": "Test analysis",
            "suggested_fix": "Test fix",
            "priority": "medium",
            "confidence": 0.85,
            "related_docs": [],
        }
    )
    service.classify_error = AsyncMock(return_value="checkpoint_failure")
    service.close = AsyncMock()
    return service


# ============ State Fixtures ============


@pytest.fixture
def sample_job_info() -> JobInfo:
    """示例作业信息."""
    return JobInfo(
        exception_id=1,
        job_id="job-123",
        job_name="Test Flink Job",
        job_type="streaming",
        job_config={"parallelism": 4},
        error_message="Checkpoint failed after 10 retries",
        error_type="checkpoint_failure",
        created_at="2024-01-01T00:00:00",
    )


@pytest.fixture
def sample_diagnosis_result() -> DiagnosisResult:
    """示例诊断结果."""
    return DiagnosisResult(
        root_cause="State backend timeout",
        detailed_analysis="The checkpoint failed due to state backend timeout...",
        suggested_fix="Increase checkpoint timeout to 10 minutes",
        priority="high",
        confidence=0.9,
        related_docs=["https://flink.apache.org/docs/checkpoint"],
    )


@pytest.fixture
def sample_retrieved_case() -> RetrievedCase:
    """示例检索案例."""
    return RetrievedCase(
        case_id="case_001",
        error_type="checkpoint_failure",
        error_pattern="Checkpoint failed after <NUM> retries",
        root_cause="State backend timeout",
        solution="Increase timeout",
        similarity_score=0.95,
    )


@pytest.fixture
def sample_retrieved_doc() -> RetrievedDoc:
    """示例检索文档."""
    return RetrievedDoc(
        doc_id="doc_001",
        title="Checkpoint Configuration",
        content="Flink checkpoint configuration...",
        doc_url="https://flink.apache.org/docs",
        category="configuration",
        similarity_score=0.88,
    )


@pytest.fixture
def sample_retrieved_context(
    sample_retrieved_case: RetrievedCase,
    sample_retrieved_doc: RetrievedDoc,
) -> RetrievedContext:
    """示例检索上下文."""
    return RetrievedContext(
        similar_cases=[sample_retrieved_case],
        doc_snippets=[sample_retrieved_doc],
    )


@pytest.fixture
def initial_state() -> DiagnosisState:
    """初始工作流状态."""
    return DiagnosisState(
        job_info=None,
        status=DiagnosisStatus.PENDING,
        retrieved_context=None,
        diagnosis_result=None,
        start_time=datetime.now().isoformat(),
        end_time=None,
        error=None,
        retry_count=0,
    )


@pytest.fixture
def state_with_job(
    initial_state: DiagnosisState,
    sample_job_info: JobInfo,
) -> DiagnosisState:
    """包含作业信息的状态."""
    return {
        **initial_state,
        "job_info": sample_job_info,
        "status": DiagnosisStatus.IN_PROGRESS,
    }


@pytest.fixture
def state_with_context(
    state_with_job: DiagnosisState,
    sample_retrieved_context: RetrievedContext,
) -> DiagnosisState:
    """包含检索上下文的状态."""
    return {
        **state_with_job,
        "retrieved_context": sample_retrieved_context,
    }
