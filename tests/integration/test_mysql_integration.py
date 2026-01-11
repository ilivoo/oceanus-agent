"""Integration tests for MySQL service."""

import pytest
from sqlalchemy import text
from oceanus_agent.services.mysql_service import MySQLService
from oceanus_agent.models.state import DiagnosisResult

@pytest.mark.asyncio
class TestMySQLIntegration:
    """MySQL Service 集成测试."""

    async def test_get_pending_exception_lifecycle(self, real_mysql_service: MySQLService):
        """测试异常任务的完整生命周期：插入 -> 获取 -> 更新."""
        
        # 1. 准备数据：手动插入一个 pending 异常
        async with real_mysql_service.async_session() as session:
            query = text("""
                INSERT INTO flink_job_exceptions 
                (job_id, job_name, job_type, error_message, status, job_config)
                VALUES 
                (:job_id, :job_name, :job_type, :error_message, 'pending', :job_config)
            """)
            await session.execute(query, {
                "job_id": "int-test-001",
                "job_name": "Integration Test Job",
                "job_type": "streaming",
                "error_message": "Test error message for integration",
                "job_config": '{"parallelism": 2}'
            })
            await session.commit()

        # 2. 调用服务获取待处理任务
        job_info = await real_mysql_service.get_pending_exception()
        
        assert job_info is not None
        assert job_info["job_id"] == "int-test-001"
        assert job_info["job_config"] == {"parallelism": 2}

        # 验证数据库中状态已变为 in_progress
        async with real_mysql_service.async_session() as session:
            res = await session.execute(
                text("SELECT status FROM flink_job_exceptions WHERE job_id = 'int-test-001'")
            )
            status = res.scalar()
            assert status == "in_progress"

        # 3. 更新诊断结果
        diagnosis: DiagnosisResult = {
            "root_cause": "Network partitioning",
            "detailed_analysis": "The nodes were unable to communicate...",
            "suggested_fix": "Check network stability",
            "priority": "high",
            "confidence": 0.95,
            "related_docs": ["http://example.com/doc"]
        }
        
        await real_mysql_service.update_diagnosis_result(
            exception_id=job_info["exception_id"],
            diagnosis=diagnosis
        )

        # 4. 验证最终结果
        async with real_mysql_service.async_session() as session:
            res = await session.execute(
                text("SELECT status, diagnosis_confidence FROM flink_job_exceptions WHERE job_id = 'int-test-001'")
            )
            row = res.fetchone()
            assert row is not None
            assert row[0] == "completed"
            assert row[1] == 0.95

    async def test_knowledge_case_persistence(self, real_mysql_service: MySQLService):
        """测试知识库案例的持久化."""
        
        # 插入知识案例
        await real_mysql_service.insert_knowledge_case(
            case_id="int-case-001",
            error_type="checkpoint_failure",
            error_pattern="Checkpoint timeout after <NUM>ms",
            root_cause="S3 latency",
            solution="Use local state backend",
            source_type="auto"
        )

        # 验证插入成功
        async with real_mysql_service.async_session() as session:
            res = await session.execute(
                text("SELECT error_type, source_type FROM knowledge_cases WHERE case_id = 'int-case-001'")
            )
            row = res.fetchone()
            assert row is not None
            assert row[0] == "checkpoint_failure"
            assert row[1] == "auto"

    async def test_get_pending_count(self, real_mysql_service: MySQLService):
        """测试获取待处理任务计数."""
        
        # 插入 3 条记录
        async with real_mysql_service.async_session() as session:
            for i in range(3):
                await session.execute(
                    text("INSERT INTO flink_job_exceptions (job_id, error_message, status) VALUES (:j, :e, 'pending')"),
                    {"j": f"job-{i}", "e": "err"}
                )
            await session.commit()

        count = await real_mysql_service.get_pending_count()
        assert count == 3
