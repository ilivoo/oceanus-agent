"""Integration tests for Milvus service."""

import pytest
from oceanus_agent.services.milvus_service import MilvusService

@pytest.mark.asyncio
class TestMilvusIntegration:
    """Milvus Service 集成测试."""

    async def test_milvus_collection_and_search(self, real_milvus_service: MilvusService):
        """测试 Milvus 集合创建、数据插入和搜索功能."""
        
        # 1. 验证集合已创建
        stats = real_milvus_service.get_collection_stats()
        assert real_milvus_service.settings.cases_collection in stats
        assert real_milvus_service.settings.docs_collection in stats

        # 2. 插入测试数据
        case_id = "test-case-123"
        vector = [0.1] * 1536
        await real_milvus_service.insert_case(
            case_id=case_id,
            vector=vector,
            error_type="backpressure",
            error_pattern="High backpressure in <PATH>",
            root_cause="Skewed data distribution",
            solution="Add more partitions"
        )

        # 3. 搜索相似案例
        # 由于 Milvus 插入后可能需要秒级索引可见性（默认是异步的），
        # 但 MilvusClient.insert 默认会有一定的保证，或者我们可以稍微等待或强制刷新。
        # 简单起见，我们直接搜索。
        results = await real_milvus_service.search_similar_cases(
            query_vector=vector,
            limit=1
        )

        assert len(results) > 0
        assert results[0]["case_id"] == case_id
        assert results[0]["error_type"] == "backpressure"

    async def test_milvus_doc_search(self, real_milvus_service: MilvusService):
        """测试文档片段的搜索."""
        
        doc_id = "test-doc-001"
        vector = [0.5] * 1536
        await real_milvus_service.insert_doc(
            doc_id=doc_id,
            vector=vector,
            title="Flink Performance Tuning",
            content="To tune performance, adjust memory settings...",
            category="tuning"
        )

        # 搜索
        results = await real_milvus_service.search_doc_snippets(
            query_vector=vector,
            category="tuning",
            limit=1
        )

        assert len(results) > 0
        assert results[0]["doc_id"] == doc_id
        assert results[0]["category"] == "tuning"
        assert "Performance" in results[0]["title"]
