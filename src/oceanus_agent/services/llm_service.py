"""LLM service for diagnosis using OpenAI."""

import json

import structlog
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from oceanus_agent.config.prompts import (
    CASE_TEMPLATE,
    CONTEXT_TEMPLATE,
    DIAGNOSIS_SYSTEM_PROMPT,
    DIAGNOSIS_USER_PROMPT,
    DOC_TEMPLATE,
    ERROR_CLASSIFICATION_PROMPT,
)
from oceanus_agent.config.settings import OpenAISettings
from oceanus_agent.models.diagnosis import DiagnosisOutput
from oceanus_agent.models.state import (
    DiagnosisResult,
    JobInfo,
    RetrievedContext,
)

logger = structlog.get_logger()


class LLMService:
    """Service for LLM-based diagnosis."""

    def __init__(self, settings: OpenAISettings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.api_key.get_secret_value(),
            base_url=settings.base_url,
            timeout=settings.timeout
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector.
        """
        response = await self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=text[:8000]  # Truncate to avoid token limit
        )
        return response.data[0].embedding

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def generate_diagnosis(
        self,
        job_info: JobInfo,
        context: RetrievedContext | None = None
    ) -> DiagnosisResult:
        """Generate diagnosis for a job exception.

        Args:
            job_info: Information about the job exception.
            context: Retrieved context from knowledge base.

        Returns:
            Diagnosis result.
        """
        # Build context string
        context_str = self._build_context_string(context)

        # Build user prompt
        user_prompt = DIAGNOSIS_USER_PROMPT.format(
            job_id=job_info["job_id"],
            job_name=job_info.get("job_name") or "Unknown",
            job_type=job_info.get("job_type") or "Unknown",
            error_type=job_info.get("error_type") or "Unknown",
            error_message=job_info["error_message"][:4000],
            job_config=json.dumps(
                job_info.get("job_config") or {},
                indent=2,
                ensure_ascii=False
            )[:2000],
            context=context_str
        )

        logger.debug(
            "Generating diagnosis",
            job_id=job_info["job_id"],
            context_cases=len(context["similar_cases"]) if context else 0,
            context_docs=len(context["doc_snippets"]) if context else 0
        )

        response = await self.client.beta.chat.completions.parse(
            model=self.settings.model,
            messages=[
                {"role": "system", "content": DIAGNOSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.settings.temperature,
            max_tokens=self.settings.max_tokens,
            response_format=DiagnosisOutput
        )

        parsed = response.choices[0].message.parsed

        if not parsed:
            raise ValueError("Failed to parse LLM response")

        result: DiagnosisResult = {
            "root_cause": parsed.root_cause,
            "detailed_analysis": parsed.detailed_analysis,
            "suggested_fix": parsed.suggested_fix,
            "priority": parsed.priority.value,
            "confidence": parsed.confidence,
            "related_docs": parsed.related_docs
        }

        logger.info(
            "Generated diagnosis",
            job_id=job_info["job_id"],
            confidence=result["confidence"],
            priority=result["priority"]
        )

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def classify_error(self, error_message: str) -> str:
        """Classify error type from error message.

        Args:
            error_message: Error message to classify.

        Returns:
            Error type string.
        """
        prompt = ERROR_CLASSIFICATION_PROMPT.format(
            error_message=error_message[:2000]
        )

        response = await self.client.chat.completions.create(
            model=self.settings.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )

        error_type = response.choices[0].message.content.strip().lower()

        valid_types = [
            "checkpoint_failure",
            "backpressure",
            "deserialization_error",
            "oom",
            "network",
            "other"
        ]

        if error_type not in valid_types:
            error_type = "other"

        logger.debug(
            "Classified error",
            error_type=error_type
        )

        return error_type

    def _build_context_string(
        self,
        context: RetrievedContext | None
    ) -> str:
        """Build context string from retrieved context.

        Args:
            context: Retrieved context from knowledge base.

        Returns:
            Formatted context string.
        """
        if not context:
            return "No reference context available."

        cases_section = ""
        if context.get("similar_cases"):
            cases_parts = []
            for i, case in enumerate(context["similar_cases"][:3], 1):
                cases_parts.append(CASE_TEMPLATE.format(
                    index=i,
                    error_type=case["error_type"],
                    error_pattern=case["error_pattern"][:500],
                    root_cause=case["root_cause"],
                    solution=case["solution"][:1000]
                ))
            cases_section = "\n".join(cases_parts)
        else:
            cases_section = "No similar historical cases found."

        docs_section = ""
        if context.get("doc_snippets"):
            docs_parts = []
            for i, doc in enumerate(context["doc_snippets"][:3], 1):
                docs_parts.append(DOC_TEMPLATE.format(
                    index=i,
                    title=doc["title"],
                    content=doc["content"][:1000],
                    doc_url=doc.get("doc_url") or "N/A"
                ))
            docs_section = "\n".join(docs_parts)
        else:
            docs_section = "No related documentation found."

        return CONTEXT_TEMPLATE.format(
            cases_section=cases_section,
            docs_section=docs_section
        )

    async def close(self) -> None:
        """Close the client."""
        await self.client.close()
