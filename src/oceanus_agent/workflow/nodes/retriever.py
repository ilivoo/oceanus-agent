"""Knowledge retrieval node for the diagnosis workflow."""

import structlog
from langsmith import traceable

from oceanus_agent.config.settings import KnowledgeSettings
from oceanus_agent.models.state import DiagnosisState, RetrievedContext
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.services.milvus_service import MilvusService

logger = structlog.get_logger()


class KnowledgeRetriever:
    """Node for retrieving relevant knowledge from Milvus."""

    def __init__(
        self,
        milvus_service: MilvusService,
        llm_service: LLMService,
        settings: KnowledgeSettings
    ):
        self.milvus_service = milvus_service
        self.llm_service = llm_service
        self.settings = settings

    @traceable(name="retrieve_knowledge")
    async def __call__(self, state: DiagnosisState) -> DiagnosisState:
        """Retrieve relevant knowledge for the job exception.

        Args:
            state: Current workflow state.

        Returns:
            Updated state with retrieved context.
        """
        job_info = state.get("job_info")

        if not job_info:
            return state

        try:
            # Build query text from error message
            query_text = f"{job_info.get('error_type', '')} {job_info['error_message'][:1000]}"

            # Generate embedding
            query_vector = await self.llm_service.generate_embedding(query_text)

            # Search for similar cases
            similar_cases = await self.milvus_service.search_similar_cases(
                query_vector=query_vector,
                error_type=job_info.get("error_type"),
                limit=self.settings.max_similar_cases
            )

            # Search for relevant documentation
            doc_snippets = await self.milvus_service.search_doc_snippets(
                query_vector=query_vector,
                limit=self.settings.max_doc_snippets
            )

            context: RetrievedContext = {
                "similar_cases": similar_cases,
                "doc_snippets": doc_snippets
            }

            logger.info(
                "Retrieved knowledge context",
                job_id=job_info["job_id"],
                cases_found=len(similar_cases),
                docs_found=len(doc_snippets)
            )

            return {
                **state,
                "retrieved_context": context
            }

        except Exception as e:
            logger.warning(
                "Error retrieving knowledge, continuing without context",
                job_id=job_info["job_id"],
                error=str(e)
            )
            # Continue without context - diagnosis can still proceed
            return {
                **state,
                "retrieved_context": {
                    "similar_cases": [],
                    "doc_snippets": []
                }
            }
