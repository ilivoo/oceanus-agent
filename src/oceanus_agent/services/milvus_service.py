"""Milvus vector database service for knowledge retrieval."""

import structlog
from pymilvus import (
    DataType,
    MilvusClient,
)

from oceanus_agent.config.settings import MilvusSettings
from oceanus_agent.models.state import RetrievedCase, RetrievedDoc

logger = structlog.get_logger()


class MilvusService:
    """Service for Milvus vector database operations."""

    def __init__(self, settings: MilvusSettings):
        self.settings = settings
        self.client = MilvusClient(uri=settings.uri, token=settings.token_value)
        self._ensure_collections()

    def _ensure_collections(self) -> None:
        """Ensure required collections exist."""
        # Check and create cases collection
        if not self.client.has_collection(self.settings.cases_collection):
            self._create_cases_collection()
            logger.info(
                "Created cases collection", collection=self.settings.cases_collection
            )

        # Check and create docs collection
        if not self.client.has_collection(self.settings.docs_collection):
            self._create_docs_collection()
            logger.info(
                "Created docs collection", collection=self.settings.docs_collection
            )

    def _create_cases_collection(self) -> None:
        """Create the flink_cases collection."""
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=False)

        schema.add_field(
            field_name="case_id",
            datatype=DataType.VARCHAR,
            max_length=64,
            is_primary=True,
        )
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.settings.vector_dim,
        )
        schema.add_field(
            field_name="error_type", datatype=DataType.VARCHAR, max_length=64
        )
        schema.add_field(
            field_name="error_pattern", datatype=DataType.VARCHAR, max_length=2000
        )
        schema.add_field(
            field_name="root_cause", datatype=DataType.VARCHAR, max_length=2000
        )
        schema.add_field(
            field_name="solution", datatype=DataType.VARCHAR, max_length=4000
        )

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128},
        )

        self.client.create_collection(
            collection_name=self.settings.cases_collection,
            schema=schema,
            index_params=index_params,
        )

    def _create_docs_collection(self) -> None:
        """Create the flink_docs collection."""
        schema = self.client.create_schema(auto_id=False, enable_dynamic_field=False)

        schema.add_field(
            field_name="doc_id",
            datatype=DataType.VARCHAR,
            max_length=64,
            is_primary=True,
        )
        schema.add_field(
            field_name="vector",
            datatype=DataType.FLOAT_VECTOR,
            dim=self.settings.vector_dim,
        )
        schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=512)
        schema.add_field(
            field_name="content", datatype=DataType.VARCHAR, max_length=8000
        )
        schema.add_field(
            field_name="doc_url", datatype=DataType.VARCHAR, max_length=512
        )
        schema.add_field(
            field_name="category", datatype=DataType.VARCHAR, max_length=64
        )

        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            index_type="IVF_FLAT",
            metric_type="COSINE",
            params={"nlist": 128},
        )

        self.client.create_collection(
            collection_name=self.settings.docs_collection,
            schema=schema,
            index_params=index_params,
        )

    async def search_similar_cases(
        self, query_vector: list[float], error_type: str | None = None, limit: int = 3
    ) -> list[RetrievedCase]:
        """Search for similar historical cases.

        Args:
            query_vector: Query embedding vector.
            error_type: Optional filter by error type.
            limit: Maximum number of results.

        Returns:
            List of similar cases.
        """
        filter_expr = ""
        if error_type:
            filter_expr = f'error_type == "{error_type}"'

        results = self.client.search(
            collection_name=self.settings.cases_collection,
            data=[query_vector],
            limit=limit,
            filter=filter_expr if filter_expr else None,
            output_fields=[
                "case_id",
                "error_type",
                "error_pattern",
                "root_cause",
                "solution",
            ],
        )

        cases = []
        for hits in results:
            for hit in hits:
                entity = hit.get("entity", {})
                cases.append(
                    RetrievedCase(
                        case_id=entity.get("case_id", ""),
                        error_type=entity.get("error_type", ""),
                        error_pattern=entity.get("error_pattern", ""),
                        root_cause=entity.get("root_cause", ""),
                        solution=entity.get("solution", ""),
                        similarity_score=hit.get("distance", 0.0),
                    )
                )

        logger.debug("Found similar cases", count=len(cases), error_type=error_type)
        return cases

    async def search_doc_snippets(
        self, query_vector: list[float], category: str | None = None, limit: int = 3
    ) -> list[RetrievedDoc]:
        """Search for relevant documentation snippets.

        Args:
            query_vector: Query embedding vector.
            category: Optional filter by category.
            limit: Maximum number of results.

        Returns:
            List of relevant documents.
        """
        filter_expr = ""
        if category:
            filter_expr = f'category == "{category}"'

        results = self.client.search(
            collection_name=self.settings.docs_collection,
            data=[query_vector],
            limit=limit,
            filter=filter_expr if filter_expr else None,
            output_fields=["doc_id", "title", "content", "doc_url", "category"],
        )

        docs = []
        for hits in results:
            for hit in hits:
                entity = hit.get("entity", {})
                docs.append(
                    RetrievedDoc(
                        doc_id=entity.get("doc_id", ""),
                        title=entity.get("title", ""),
                        content=entity.get("content", ""),
                        doc_url=entity.get("doc_url"),
                        category=entity.get("category"),
                        similarity_score=hit.get("distance", 0.0),
                    )
                )

        logger.debug("Found doc snippets", count=len(docs), category=category)
        return docs

    async def insert_case(
        self,
        case_id: str,
        vector: list[float],
        error_type: str,
        error_pattern: str,
        root_cause: str,
        solution: str,
    ) -> None:
        """Insert a new case into the knowledge base.

        Args:
            case_id: Unique case identifier.
            vector: Embedding vector.
            error_type: Type of error.
            error_pattern: Generalized error pattern.
            root_cause: Root cause of the error.
            solution: Solution to fix the error.
        """
        data = [
            {
                "case_id": case_id,
                "vector": vector,
                "error_type": error_type,
                "error_pattern": error_pattern[:2000],
                "root_cause": root_cause[:2000],
                "solution": solution[:4000],
            }
        ]

        self.client.insert(collection_name=self.settings.cases_collection, data=data)

        logger.info("Inserted case to Milvus", case_id=case_id, error_type=error_type)

    async def insert_doc(
        self,
        doc_id: str,
        vector: list[float],
        title: str,
        content: str,
        doc_url: str | None = None,
        category: str | None = None,
    ) -> None:
        """Insert a new document into the knowledge base.

        Args:
            doc_id: Unique document identifier.
            vector: Embedding vector.
            title: Document title.
            content: Document content.
            doc_url: URL to original document.
            category: Document category.
        """
        data = [
            {
                "doc_id": doc_id,
                "vector": vector,
                "title": title[:512],
                "content": content[:8000],
                "doc_url": doc_url or "",
                "category": category or "",
            }
        ]

        self.client.insert(collection_name=self.settings.docs_collection, data=data)

        logger.info("Inserted doc to Milvus", doc_id=doc_id, title=title)

    def get_collection_stats(self) -> dict:
        """Get statistics for all collections.

        Returns:
            Dictionary with collection statistics.
        """
        stats = {}

        for collection_name in [
            self.settings.cases_collection,
            self.settings.docs_collection,
        ]:
            if self.client.has_collection(collection_name):
                info = self.client.describe_collection(collection_name)

                # Use query to get count as num_entities is not available on MilvusClient
                primary_key = (
                    "case_id"
                    if collection_name == self.settings.cases_collection
                    else "doc_id"
                )
                res = self.client.query(
                    collection_name=collection_name,
                    filter=f'{primary_key} != ""',
                    output_fields=["count(*)"],
                )
                count = res[0]["count(*)"] if res else 0

                stats[collection_name] = {
                    "num_entities": count,
                    "description": info.get("description", ""),
                }

        return stats

    def close(self) -> None:
        """Close the Milvus connection."""
        self.client.close()
