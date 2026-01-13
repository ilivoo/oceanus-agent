"""Integration tests for the diagnosis workflow."""

from unittest.mock import patch

import pytest

from oceanus_agent.config.settings import settings
from oceanus_agent.models.state import DiagnosisStatus
from oceanus_agent.workflow.graph import DiagnosisWorkflow


@pytest.mark.asyncio
class TestWorkflowIntegration:
    """Workflow 级别集成测试."""

    async def test_complete_workflow_flow(
        self,
        real_mysql_service,
        real_milvus_service,
        mock_llm_service
    ):
        """测试从异常发现到结果存储的完整流程."""

        # 1. Setup: 插入待处理异常和相关知识案例
        # 1.1 在 Milvus 插入向量 (模拟已有知识)
        await real_milvus_service.insert_case(
            case_id="kn-001",
            vector=[0.1]*1536,
            error_type="checkpoint_failure",
            error_pattern="...",
            root_cause="Old cause",
            solution="Old solution"
        )

        # 1.2 在 MySQL 插入对应的元数据 (可选，取决于 Retriever 是否依赖 MySQL，目前看只依赖 Milvus)
        # 但为了完整性，我们也可以插一条
        await real_mysql_service.insert_knowledge_case(
            case_id="kn-001",
            error_type="checkpoint_failure",
            error_pattern="...",
            root_cause="Old cause",
            solution="Old solution",
            source_type="manual"
        )

        # 1.3 插入待处理的任务
        from sqlalchemy import text
        async with real_mysql_service.async_session() as session:
            await session.execute(text("""
                INSERT INTO flink_job_exceptions
                (job_id, job_name, error_message, status)
                VALUES ('wf-test-001', 'Test Job', 'Checkpoint timeout', 'pending')
            """))
            await session.commit()

        # 2. 初始化工作流并替换服务为真实/模拟服务
        # 我们通过 patch 来确保 build_diagnosis_workflow 使用我们的 real services
        with patch("oceanus_agent.workflow.graph.MySQLService", return_value=real_mysql_service), \
             patch("oceanus_agent.workflow.graph.MilvusService", return_value=real_milvus_service), \
             patch("oceanus_agent.workflow.graph.LLMService", return_value=mock_llm_service):

            workflow = DiagnosisWorkflow(settings)

            # 3. 运行工作流
            result = await workflow.run(thread_id="test-thread-1")

            # 4. 断言工作流状态
            assert result["status"] == DiagnosisStatus.COMPLETED
            assert result["job_info"]["job_id"] == "wf-test-001"
            assert result["diagnosis_result"] is not None

            # 5. 断言数据库已更新
            async with real_mysql_service.async_session() as session:
                res = await session.execute(text(
                    "SELECT status FROM flink_job_exceptions WHERE job_id = 'wf-test-001'"
                ))
                assert res.scalar() == "completed"

            # 6. 断言知识积累 (如果 confidence > 0.8)
            # 在 mock_llm_service 中默认返回 confidence 0.85

            # 6.1 验证 MySQL 中有两条知识案例 (1条 setup, 1条 accumulated)
            async with real_mysql_service.async_session() as session:
                res = await session.execute(text("SELECT COUNT(*) FROM knowledge_cases"))
                count = res.scalar()
                assert count == 2

            # 6.2 验证 Milvus 能搜到新案例 (使用 Strong Consistency)
            # 我们用刚才 Mock LLM 生成的 embedding 进行搜索
            search_res = await real_milvus_service.search_similar_cases(
                query_vector=[0.1]*1536,
                limit=10  # 获取所有
            )
            # 应该能搜到至少 2 条 (setup 的和 accumulated 的)
            assert len(search_res) >= 2
