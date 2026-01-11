"""Unit tests for workflow graph routing logic."""

from datetime import datetime

from langgraph.graph import END

from oceanus_agent.models.state import DiagnosisState, DiagnosisStatus
from oceanus_agent.workflow.graph import (
    handle_error,
    should_continue_after_collect,
    should_continue_after_diagnose,
)


class TestShouldContinueAfterCollect:
    """测试 collect 节点后的路由逻辑."""

    def test_returns_handle_error_when_error_present(
        self, initial_state: DiagnosisState
    ) -> None:
        """有错误时应路由到 handle_error."""
        state = {**initial_state, "error": "Some error occurred"}

        result = should_continue_after_collect(state)

        assert result == "handle_error"

    def test_returns_end_when_no_job(
        self, initial_state: DiagnosisState
    ) -> None:
        """无待处理作业时应结束."""
        result = should_continue_after_collect(initial_state)

        assert result == END

    def test_returns_retrieve_when_job_present(
        self, state_with_job: DiagnosisState
    ) -> None:
        """有作业时应路由到 retrieve."""
        result = should_continue_after_collect(state_with_job)

        assert result == "retrieve"

    def test_error_takes_precedence_over_job(
        self, state_with_job: DiagnosisState
    ) -> None:
        """错误优先于作业."""
        state = {**state_with_job, "error": "Error message"}

        result = should_continue_after_collect(state)

        assert result == "handle_error"


class TestShouldContinueAfterDiagnose:
    """测试 diagnose 节点后的路由逻辑."""

    def test_returns_store_on_success(
        self, state_with_job: DiagnosisState, sample_diagnosis_result: dict
    ) -> None:
        """诊断成功应路由到 store."""
        state = {
            **state_with_job,
            "diagnosis_result": sample_diagnosis_result,
        }

        result = should_continue_after_diagnose(state)

        assert result == "store"

    def test_returns_diagnose_on_first_retry(
        self, state_with_job: DiagnosisState
    ) -> None:
        """第一次重试时应重新诊断."""
        state = {
            **state_with_job,
            "error": "LLM error",
            "retry_count": 0,
        }

        result = should_continue_after_diagnose(state)

        assert result == "diagnose"

    def test_returns_diagnose_on_second_retry(
        self, state_with_job: DiagnosisState
    ) -> None:
        """第二次重试时应重新诊断."""
        state = {
            **state_with_job,
            "error": "LLM error",
            "retry_count": 1,
        }

        result = should_continue_after_diagnose(state)

        assert result == "diagnose"

    def test_returns_diagnose_on_third_retry(
        self, state_with_job: DiagnosisState
    ) -> None:
        """第三次重试时应重新诊断."""
        state = {
            **state_with_job,
            "error": "LLM error",
            "retry_count": 2,
        }

        result = should_continue_after_diagnose(state)

        assert result == "diagnose"

    def test_returns_handle_error_after_max_retries(
        self, state_with_job: DiagnosisState
    ) -> None:
        """重试次数达上限时应路由到 handle_error."""
        state = {
            **state_with_job,
            "error": "LLM error",
            "retry_count": 3,
        }

        result = should_continue_after_diagnose(state)

        assert result == "handle_error"

    def test_returns_handle_error_on_retry_count_exceeds_max(
        self, state_with_job: DiagnosisState
    ) -> None:
        """重试次数超过上限时应路由到 handle_error."""
        state = {
            **state_with_job,
            "error": "LLM error",
            "retry_count": 5,
        }

        result = should_continue_after_diagnose(state)

        assert result == "handle_error"


class TestHandleError:
    """测试错误处理函数."""

    def test_sets_failed_status(
        self, state_with_job: DiagnosisState
    ) -> None:
        """错误处理应设置失败状态."""
        state = {**state_with_job, "error": "Test error"}

        result = handle_error(state)

        assert result["status"] == DiagnosisStatus.FAILED

    def test_sets_end_time(
        self, state_with_job: DiagnosisState
    ) -> None:
        """错误处理应设置结束时间."""
        state = {**state_with_job, "error": "Test error"}

        result = handle_error(state)

        assert result["end_time"] is not None
        # 验证是有效的 ISO 格式时间戳
        datetime.fromisoformat(result["end_time"])

    def test_preserves_other_state_fields(
        self, state_with_job: DiagnosisState
    ) -> None:
        """错误处理应保留其他状态字段."""
        state = {**state_with_job, "error": "Test error"}

        result = handle_error(state)

        assert result["job_info"] == state_with_job["job_info"]
        assert result["error"] == "Test error"

    def test_handles_missing_job_info(
        self, initial_state: DiagnosisState
    ) -> None:
        """应处理无作业信息的情况."""
        state = {**initial_state, "error": "Early error"}

        result = handle_error(state)

        assert result["status"] == DiagnosisStatus.FAILED
        assert result["job_info"] is None

    def test_handles_none_job_id(
        self, initial_state: DiagnosisState
    ) -> None:
        """应处理 job_id 为 None 的情况."""
        state = {
            **initial_state,
            "error": "Error",
            "job_info": {"job_id": None},  # type: ignore
        }

        # 不应抛出异常
        result = handle_error(state)

        assert result["status"] == DiagnosisStatus.FAILED


class TestRoutingEdgeCases:
    """路由逻辑边界情况测试."""

    def test_collect_with_empty_error_string_continues(
        self, state_with_job: DiagnosisState
    ) -> None:
        """空错误字符串不应触发错误处理."""
        state = {**state_with_job, "error": ""}

        result = should_continue_after_collect(state)

        # 空字符串是 falsy，所以应该继续
        assert result == "retrieve"

    def test_collect_with_none_error_continues(
        self, state_with_job: DiagnosisState
    ) -> None:
        """None 错误不应触发错误处理."""
        state = {**state_with_job, "error": None}

        result = should_continue_after_collect(state)

        assert result == "retrieve"

    def test_diagnose_no_error_no_result(
        self, state_with_job: DiagnosisState
    ) -> None:
        """无错误无结果时应路由到 store."""
        state = {**state_with_job, "diagnosis_result": None}

        result = should_continue_after_diagnose(state)

        # 即使没有结果，只要没错误就继续
        assert result == "store"

    def test_diagnose_default_retry_count(
        self, state_with_job: DiagnosisState
    ) -> None:
        """测试默认重试计数."""
        state = {
            **state_with_job,
            "error": "Some error",
        }
        # 不设置 retry_count，应该使用默认值 0
        del state["retry_count"]

        result = should_continue_after_diagnose(state)

        assert result == "diagnose"  # 应该重试
