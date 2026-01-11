"""Models for knowledge base entities."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Source type of a knowledge case."""
    MANUAL = "manual"
    AUTO = "auto"


class KnowledgeCase(BaseModel):
    """A knowledge case in the database."""
    case_id: str = Field(description="Unique identifier for the case")
    error_type: str = Field(description="Type of error")
    error_pattern: str = Field(description="Generalized error pattern")
    root_cause: str = Field(description="Root cause of the error")
    solution: str = Field(description="Solution to fix the error")
    source_exception_id: int | None = Field(
        default=None,
        description="ID of the source exception if auto-generated"
    )
    source_type: SourceType = Field(description="How this case was created")
    verified: bool = Field(
        default=False,
        description="Whether this case has been verified by humans"
    )
    created_at: datetime | None = None


class FlinkDocument(BaseModel):
    """A Flink documentation entry."""
    doc_id: str = Field(description="Unique identifier for the document")
    title: str = Field(description="Document title")
    content: str = Field(description="Document content or snippet")
    doc_url: str | None = Field(
        default=None,
        description="URL to the original document"
    )
    category: str | None = Field(
        default=None,
        description="Document category (e.g., checkpoint, state, networking)"
    )
    created_at: datetime | None = None


class MilvusCaseRecord(BaseModel):
    """Record structure for Milvus case collection."""
    case_id: str
    vector: list[float]
    error_type: str
    error_pattern: str
    root_cause: str
    solution: str


class MilvusDocRecord(BaseModel):
    """Record structure for Milvus document collection."""
    doc_id: str
    vector: list[float]
    title: str
    content: str
    doc_url: str | None = None
    category: str | None = None
