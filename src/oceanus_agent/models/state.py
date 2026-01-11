"""LangGraph state definitions for the diagnosis workflow."""

from typing import TypedDict, Optional, List, Any
from enum import Enum
from datetime import datetime


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
    job_name: Optional[str]
    job_type: Optional[str]
    job_config: Optional[dict]
    error_message: str
    error_type: Optional[str]
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
    doc_url: Optional[str]
    category: Optional[str]
    similarity_score: float


class RetrievedContext(TypedDict):
    """Context retrieved from the knowledge base."""
    similar_cases: List[RetrievedCase]
    doc_snippets: List[RetrievedDoc]


class DiagnosisResult(TypedDict):
    """Result of the LLM diagnosis."""
    root_cause: str
    detailed_analysis: str
    suggested_fix: str
    priority: str  # high, medium, low
    confidence: float  # 0-1
    related_docs: List[str]


class DiagnosisState(TypedDict):
    """State for the diagnosis workflow.

    This is the main state object that flows through the LangGraph workflow.
    Each node can read and update fields in this state.
    """
    job_info: Optional[JobInfo]
    status: DiagnosisStatus
    retrieved_context: Optional[RetrievedContext]
    diagnosis_result: Optional[DiagnosisResult]
    start_time: str
    end_time: Optional[str]
    error: Optional[str]
    retry_count: int
