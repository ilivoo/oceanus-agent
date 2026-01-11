"""LangGraph state definitions for the diagnosis workflow."""

from enum import Enum
from typing import TypedDict


class DiagnosisStatus(str, Enum):
    """Status of a diagnosis task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo(TypedDict):
    """Information about a Flink job exception."""

    exception_id: int
    job_id: str
    job_name: str | None
    job_type: str | None
    job_config: dict | None
    error_message: str
    error_type: str | None
    created_at: str


class RetrievedCase(TypedDict):
    """A retrieved historical case from the knowledge base."""

    case_id: str
    error_type: str
    error_pattern: str
    root_cause: str
    solution: str
    similarity_score: float


class RetrievedDoc(TypedDict):
    """A retrieved document snippet from the knowledge base."""

    doc_id: str
    title: str
    content: str
    doc_url: str | None
    category: str | None
    similarity_score: float


class RetrievedContext(TypedDict):
    """Context retrieved from the knowledge base."""

    similar_cases: list[RetrievedCase]
    doc_snippets: list[RetrievedDoc]


class DiagnosisResult(TypedDict):
    """Result of the LLM diagnosis."""

    root_cause: str
    detailed_analysis: str
    suggested_fix: str
    priority: str  # high, medium, low
    confidence: float  # 0-1
    related_docs: list[str]


class DiagnosisState(TypedDict):
    """State for the diagnosis workflow.

    This is the main state object that flows through the LangGraph workflow.
    Each node can read and update fields in this state.
    """

    job_info: JobInfo | None
    status: DiagnosisStatus
    retrieved_context: RetrievedContext | None
    diagnosis_result: DiagnosisResult | None
    start_time: str
    end_time: str | None
    error: str | None
    retry_count: int
