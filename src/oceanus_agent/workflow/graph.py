"""LangGraph workflow definition for diagnosis."""

import structlog
from typing import Any, cast
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langchain_core.runnables import RunnableConfig

from oceanus_agent.config.settings import Settings
from oceanus_agent.models.state import DiagnosisState, DiagnosisStatus
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.services.milvus_service import MilvusService
from oceanus_agent.services.mysql_service import MySQLService
from oceanus_agent.workflow.nodes.accumulator import KnowledgeAccumulator
from oceanus_agent.workflow.nodes.collector import JobCollector
from oceanus_agent.workflow.nodes.diagnoser import LLMDiagnoser
from oceanus_agent.workflow.nodes.retriever import KnowledgeRetriever
from oceanus_agent.workflow.nodes.storer import ResultStorer

logger = structlog.get_logger()


def should_continue_after_collect(state: DiagnosisState) -> str:
    """Routing logic after collection.

    Args:
        state: Current workflow state.

    Returns:
        Next node name or END.
    """
    if state.get("error"):
        return "handle_error"

    if state.get("job_info") is None:
        return END

    return "retrieve"


def should_continue_after_diagnose(state: DiagnosisState) -> str:
    """Routing logic after diagnosis.

    Args:
        state: Current workflow state.

    Returns:
        Next node name.
    """
    if state.get("error"):
        retry_count = state.get("retry_count", 0)
        if retry_count < 3:
            return "diagnose"  # Retry
        return "handle_error"

    return "store"


def handle_error(state: DiagnosisState) -> DiagnosisState:
    """Handle error state.

    Args:
        state: Current workflow state.

    Returns:
        Updated state with failed status.
    """
    from datetime import datetime

    job_info = state.get("job_info")
    job_id = job_info.get("job_id") if job_info else "unknown"

    logger.error("Workflow error", job_id=job_id, error=state.get("error"))

    return {
        **state,
        "status": DiagnosisStatus.FAILED,
        "end_time": datetime.now().isoformat(),
    }


def build_diagnosis_workflow(settings: Settings) -> CompiledStateGraph:
    """Build the diagnosis workflow graph.

    Args:
        settings: Application settings.

    Returns:
        Compiled workflow graph.
    """
    # Initialize services
    mysql_service = MySQLService(settings.mysql)
    milvus_service = MilvusService(settings.milvus)
    llm_service = LLMService(settings.openai)

    # Initialize nodes
    collector = JobCollector(mysql_service)
    retriever = KnowledgeRetriever(milvus_service, llm_service, settings.knowledge)
    diagnoser = LLMDiagnoser(llm_service)
    storer = ResultStorer(mysql_service)
    accumulator = KnowledgeAccumulator(
        mysql_service, milvus_service, llm_service, settings.knowledge
    )

    # Build workflow
    workflow = StateGraph(DiagnosisState)

    # Add nodes
    workflow.add_node("collect", collector)
    workflow.add_node("retrieve", retriever)
    workflow.add_node("diagnose", diagnoser)
    workflow.add_node("store", storer)
    workflow.add_node("accumulate", accumulator)
    workflow.add_node("handle_error", handle_error)

    # Define edges
    workflow.add_edge(START, "collect")

    workflow.add_conditional_edges(
        "collect",
        should_continue_after_collect,
        {"retrieve": "retrieve", "handle_error": "handle_error", END: END},
    )

    workflow.add_edge("retrieve", "diagnose")

    workflow.add_conditional_edges(
        "diagnose",
        should_continue_after_diagnose,
        {
            "diagnose": "diagnose",  # Retry
            "store": "store",
            "handle_error": "handle_error",
        },
    )

    workflow.add_edge("store", "accumulate")
    workflow.add_edge("accumulate", END)
    workflow.add_edge("handle_error", END)

    # Compile workflow with checkpointer
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    logger.info("Built diagnosis workflow")

    return app


class DiagnosisWorkflow:
    """Wrapper class for the diagnosis workflow."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.app = build_diagnosis_workflow(settings)
        self._services_initialized = False

    async def run(self, thread_id: str) -> DiagnosisState:
        """Run a single diagnosis iteration.

        Args:
            thread_id: Unique thread ID for checkpointing.

        Returns:
            Final workflow state.
        """
        from datetime import datetime

        initial_state: DiagnosisState = {
            "job_info": None,
            "status": DiagnosisStatus.PENDING,
            "retrieved_context": None,
            "diagnosis_result": None,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "error": None,
            "retry_count": 0,
        }

        config = cast(RunnableConfig, {"configurable": {"thread_id": thread_id}})
        result = await self.app.ainvoke(initial_state, config)

        return cast(DiagnosisState, result)

    async def close(self) -> None:
        """Close all services."""
        # Services are created inside build_diagnosis_workflow
        # They would need to be tracked for proper cleanup
        pass
