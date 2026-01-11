"""Unit tests for MySQL service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oceanus_agent.models.state import DiagnosisResult
from oceanus_agent.services.mysql_service import MySQLService


class TestMySQLService:
    """MySQL Service 单元测试."""

    @pytest.fixture
    def mysql_service(self, mysql_settings: MagicMock) -> MySQLService:
        """Create MySQL service with mocked engine."""
        with patch(
            "oceanus_agent.services.mysql_service.create_async_engine"
        ):
            service = MySQLService(mysql_settings)
            return service

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create mock database session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_pending_exception_found(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试获取待处理异常 - 找到记录."""
        # 模拟数据库返回结果
        mock_row = (
            1,  # id
            "job-123",  # job_id
            "Test Job",  # job_name
            "streaming",  # job_type
            '{"parallelism": 4}',  # job_config (JSON string)
            "Checkpoint failed",  # error_message
            "checkpoint_failure",  # error_type
            datetime(2024, 1, 1),  # created_at
        )
        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        # 使用 context manager mock
        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        result = await mysql_service.get_pending_exception()

        assert result is not None
        assert result["exception_id"] == 1
        assert result["job_id"] == "job-123"
        assert result["job_name"] == "Test Job"
        assert result["job_config"] == {"parallelism": 4}
        assert result["error_type"] == "checkpoint_failure"

    @pytest.mark.asyncio
    async def test_get_pending_exception_not_found(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试获取待处理异常 - 无记录."""
        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        result = await mysql_service.get_pending_exception()

        assert result is None

    @pytest.mark.asyncio
    async def test_get_pending_exception_handles_invalid_json(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试处理无效的 JSON config."""
        mock_row = (
            1,
            "job-123",
            "Test Job",
            "streaming",
            "invalid json",  # 无效的 JSON
            "Error message",
            "other",
            datetime(2024, 1, 1),
        )
        mock_result = MagicMock()
        mock_result.fetchone = MagicMock(return_value=mock_row)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        result = await mysql_service.get_pending_exception()

        assert result is not None
        assert result["job_config"] == {}  # 应该返回空字典

    @pytest.mark.asyncio
    async def test_update_diagnosis_result(
        self,
        mysql_service: MySQLService,
        mock_session: AsyncMock,
        sample_diagnosis_result: DiagnosisResult,
    ) -> None:
        """测试更新诊断结果."""
        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        await mysql_service.update_diagnosis_result(
            exception_id=1,
            diagnosis=sample_diagnosis_result,
            status="completed",
        )

        # 验证 execute 被调用
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

        # 验证传入的参数
        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["id"] == 1
        assert params["status"] == "completed"
        assert params["confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_mark_exception_failed(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试标记异常失败."""
        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        await mysql_service.mark_exception_failed(
            exception_id=1,
            error_message="LLM timeout",
        )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

        # 验证错误消息被序列化为 JSON
        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["id"] == 1
        assert "LLM timeout" in params["error_message"]

    @pytest.mark.asyncio
    async def test_insert_knowledge_case(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试插入知识案例."""
        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        await mysql_service.insert_knowledge_case(
            case_id="case-001",
            error_type="checkpoint_failure",
            error_pattern="Checkpoint failed after <NUM> retries",
            root_cause="State backend timeout",
            solution="Increase timeout",
            source_exception_id=1,
            source_type="auto",
        )

        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["case_id"] == "case-001"
        assert params["error_type"] == "checkpoint_failure"
        assert params["source_type"] == "auto"

    @pytest.mark.asyncio
    async def test_insert_knowledge_case_manual(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试插入手工知识案例."""
        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        await mysql_service.insert_knowledge_case(
            case_id="case-002",
            error_type="oom",
            error_pattern="OutOfMemoryError",
            root_cause="Heap size too small",
            solution="Increase heap size",
            source_type="manual",
        )

        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert params["source_type"] == "manual"
        assert params["source_exception_id"] is None

    @pytest.mark.asyncio
    async def test_get_pending_count(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试获取待处理数量."""
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=5)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        count = await mysql_service.get_pending_count()

        assert count == 5

    @pytest.mark.asyncio
    async def test_get_pending_count_zero(
        self, mysql_service: MySQLService, mock_session: AsyncMock
    ) -> None:
        """测试获取待处理数量为零."""
        mock_result = MagicMock()
        mock_result.scalar = MagicMock(return_value=None)
        mock_session.execute = AsyncMock(return_value=mock_result)

        mysql_service.async_session = MagicMock(
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_session),
                __aexit__=AsyncMock(return_value=None),
            )
        )

        count = await mysql_service.get_pending_count()

        assert count == 0

    @pytest.mark.asyncio
    async def test_close(self, mysql_service: MySQLService) -> None:
        """测试关闭连接."""
        mysql_service.engine = AsyncMock()
        mysql_service.engine.dispose = AsyncMock()

        await mysql_service.close()

        mysql_service.engine.dispose.assert_called_once()
