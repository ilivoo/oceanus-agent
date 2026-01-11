"""Unit tests for LLM service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oceanus_agent.models.diagnosis import DiagnosisOutput, Priority
from oceanus_agent.models.state import RetrievedContext
from oceanus_agent.services.llm_service import LLMService


class TestLLMService:
    """LLM Service 单元测试."""

    @pytest.fixture
    def llm_service(self, openai_settings: MagicMock) -> LLMService:
        """Create LLM service with mocked client."""
        with patch("oceanus_agent.services.llm_service.AsyncOpenAI"):
            service = LLMService(openai_settings)
            service.client = AsyncMock()
            return service

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self, llm_service: LLMService) -> None:
        """测试 embedding 生成成功."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        llm_service.client.embeddings.create = AsyncMock(return_value=mock_response)

        result = await llm_service.generate_embedding("test text")

        assert len(result) == 1536
        llm_service.client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_embedding_truncates_long_text(
        self, llm_service: LLMService
    ) -> None:
        """测试长文本会被截断."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * 1536)]
        llm_service.client.embeddings.create = AsyncMock(return_value=mock_response)

        long_text = "x" * 10000
        await llm_service.generate_embedding(long_text)

        # 验证传入的文本被截断到 8000 字符
        call_args = llm_service.client.embeddings.create.call_args
        assert len(call_args.kwargs["input"]) == 8000

    @pytest.mark.asyncio
    async def test_generate_diagnosis_success(
        self, llm_service: LLMService, sample_job_info: dict
    ) -> None:
        """测试诊断生成成功."""
        mock_parsed = DiagnosisOutput(
            root_cause="Test cause",
            detailed_analysis="Test analysis",
            suggested_fix="Test fix",
            priority=Priority.MEDIUM,
            confidence=0.85,
            related_docs=[],
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(parsed=mock_parsed))]
        llm_service.client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.generate_diagnosis(sample_job_info)

        assert result["root_cause"] == "Test cause"
        assert result["confidence"] == 0.85
        assert result["priority"] == "medium"

    @pytest.mark.asyncio
    async def test_generate_diagnosis_with_context(
        self,
        llm_service: LLMService,
        sample_job_info: dict,
        sample_retrieved_context: RetrievedContext,
    ) -> None:
        """测试带上下文的诊断生成."""
        mock_parsed = DiagnosisOutput(
            root_cause="Context-based cause",
            detailed_analysis="Analysis with context",
            suggested_fix="Contextual fix",
            priority=Priority.HIGH,
            confidence=0.95,
            related_docs=["https://example.com"],
        )
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(parsed=mock_parsed))]
        llm_service.client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.generate_diagnosis(
            sample_job_info, sample_retrieved_context
        )

        assert result["root_cause"] == "Context-based cause"
        assert result["confidence"] == 0.95
        assert result["priority"] == "high"
        assert len(result["related_docs"]) == 1

    @pytest.mark.asyncio
    async def test_generate_diagnosis_raises_on_parse_failure(
        self, llm_service: LLMService, sample_job_info: dict
    ) -> None:
        """测试解析失败时抛出异常（经过重试后）."""
        from tenacity import RetryError

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(parsed=None))]
        llm_service.client.beta.chat.completions.parse = AsyncMock(
            return_value=mock_response
        )

        # 由于有 tenacity 重试，最终会抛出 RetryError
        with pytest.raises(RetryError):
            await llm_service.generate_diagnosis(sample_job_info)

    @pytest.mark.asyncio
    async def test_classify_error_returns_valid_type(
        self, llm_service: LLMService
    ) -> None:
        """测试错误分类返回有效类型."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="checkpoint_failure"))
        ]
        llm_service.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.classify_error("Checkpoint failed")

        assert result == "checkpoint_failure"

    @pytest.mark.asyncio
    async def test_classify_error_normalizes_case(
        self, llm_service: LLMService
    ) -> None:
        """测试错误分类会转换为小写."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="BACKPRESSURE"))]
        llm_service.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.classify_error("High backpressure detected")

        assert result == "backpressure"

    @pytest.mark.asyncio
    async def test_classify_error_invalid_returns_other(
        self, llm_service: LLMService
    ) -> None:
        """测试无效分类返回 other."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="invalid_type"))]
        llm_service.client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await llm_service.classify_error("Unknown error")

        assert result == "other"

    @pytest.mark.asyncio
    async def test_classify_error_all_valid_types(
        self, llm_service: LLMService
    ) -> None:
        """测试所有有效的错误类型."""
        valid_types = [
            "checkpoint_failure",
            "backpressure",
            "deserialization_error",
            "oom",
            "network",
            "other",
        ]

        for error_type in valid_types:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content=error_type))]
            llm_service.client.chat.completions.create = AsyncMock(
                return_value=mock_response
            )

            result = await llm_service.classify_error("test error")
            assert result == error_type


class TestBuildContextString:
    """测试上下文字符串构建."""

    @pytest.fixture
    def llm_service(self, openai_settings: MagicMock) -> LLMService:
        """Create LLM service for testing."""
        with patch("oceanus_agent.services.llm_service.AsyncOpenAI"):
            return LLMService(openai_settings)

    def test_build_context_string_with_empty_context(
        self, llm_service: LLMService
    ) -> None:
        """测试空上下文."""
        result = llm_service._build_context_string(None)

        assert "No reference context available" in result

    def test_build_context_string_with_cases_only(
        self, llm_service: LLMService, sample_retrieved_case: dict
    ) -> None:
        """测试只有案例的上下文."""
        context: RetrievedContext = {
            "similar_cases": [sample_retrieved_case],
            "doc_snippets": [],
        }

        result = llm_service._build_context_string(context)

        assert "checkpoint_failure" in result
        assert "State backend timeout" in result
        assert "No related documentation found" in result

    def test_build_context_string_with_docs_only(
        self, llm_service: LLMService, sample_retrieved_doc: dict
    ) -> None:
        """测试只有文档的上下文."""
        context: RetrievedContext = {
            "similar_cases": [],
            "doc_snippets": [sample_retrieved_doc],
        }

        result = llm_service._build_context_string(context)

        assert "Checkpoint Configuration" in result
        assert "No similar historical cases found" in result

    def test_build_context_string_with_full_context(
        self, llm_service: LLMService, sample_retrieved_context: RetrievedContext
    ) -> None:
        """测试完整上下文."""
        result = llm_service._build_context_string(sample_retrieved_context)

        # 验证案例部分
        assert "checkpoint_failure" in result
        assert "State backend timeout" in result

        # 验证文档部分
        assert "Checkpoint Configuration" in result
        assert "flink.apache.org" in result

    def test_build_context_string_limits_cases(
        self, llm_service: LLMService, sample_retrieved_case: dict
    ) -> None:
        """测试案例数量限制为3个."""
        cases = [{**sample_retrieved_case, "case_id": f"case_{i}"} for i in range(5)]
        context: RetrievedContext = {
            "similar_cases": cases,
            "doc_snippets": [],
        }

        result = llm_service._build_context_string(context)

        # 应该只包含前3个案例 (Case 1, Case 2, Case 3)
        assert result.count("### Case") == 3
