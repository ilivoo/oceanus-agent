"""Pydantic models for diagnosis results with structured output."""

from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    """Priority level of a diagnosis."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiagnosisOutput(BaseModel):
    """Structured output from the LLM diagnosis.

    This model is used for structured output parsing from the LLM.
    """
    root_cause: str = Field(
        description="Brief description of the root cause (1-2 sentences)"
    )
    detailed_analysis: str = Field(
        description="Detailed analysis process and reasoning"
    )
    suggested_fix: str = Field(
        description="Specific repair steps including configuration changes"
    )
    priority: Priority = Field(
        description="Priority based on impact and urgency"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level of the diagnosis (0-1)"
    )
    related_docs: list[str] = Field(
        default_factory=list,
        description="List of related documentation URLs"
    )


class ErrorClassification(BaseModel):
    """Classification of error type."""
    error_type: str = Field(
        description="Type of error: checkpoint_failure, backpressure, deserialization_error, oom, network, other"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level of the classification"
    )


class DiagnosisRequest(BaseModel):
    """Request model for diagnosis API (optional)."""
    job_id: str
    job_name: str | None = None
    job_type: str | None = None
    job_config: dict | None = None
    error_message: str
    error_type: str | None = None


class DiagnosisResponse(BaseModel):
    """Response model for diagnosis API (optional)."""
    exception_id: int
    job_id: str
    status: str
    diagnosis: DiagnosisOutput | None = None
    error: str | None = None
    processing_time_ms: int | None = None
