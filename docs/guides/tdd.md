# TDD 测试驱动开发指南

本文档定义了 oceanus-agent 项目的测试驱动开发（TDD）实践规范。

> **强制要求**: 所有新功能必须遵循 TDD 流程。缺少对应测试文件的 PR 将触发 CI 警告并添加评论提醒。

---

## 1. TDD 概述

### 1.1 什么是 TDD

测试驱动开发（Test-Driven Development）是一种软件开发方法，核心理念是**先写测试，后写代码**。

### 1.2 TDD 的三个阶段

```text
┌─────────────────────────────────────────────────────────────┐
│                    TDD 开发循环                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ 1. Red  │ -> │  测试   │ -> │ 2.Green │ -> │3.Refactor│  │
│  │ 写测试  │    │  失败   │    │  写代码  │    │  重构    │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       ^                                              |       │
│       └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

| 阶段 | 说明 | 目标 |
|------|------|------|
| **Red** | 编写测试用例，运行测试 | 测试失败（因为功能尚未实现） |
| **Green** | 编写最小实现代码 | 让测试通过（不追求完美） |
| **Refactor** | 重构优化代码 | 在测试保护下改进代码质量 |

### 1.3 为什么采用 TDD

| 收益 | 说明 |
|------|------|
| **更高的代码质量** | 测试先行确保代码可测试性 |
| **更少的 Bug** | 早期发现问题，降低修复成本 |
| **更好的设计** | 测试驱动产生更清晰的接口设计 |
| **文档化** | 测试即文档，展示预期行为 |
| **重构信心** | 有测试保护，可以放心重构 |

---

## 2. 测试基础设施

### 2.1 测试框架配置

项目使用以下测试工具链：

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    "pytest>=8.1.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "pytest-mock>=3.14.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "-v --cov=oceanus_agent --cov-report=term-missing"
```

### 2.2 测试目录结构

```text
tests/
├── __init__.py
├── conftest.py              # 全局共享 fixtures
├── unit/                    # 单元测试 (不依赖外部服务)
│   ├── __init__.py
│   ├── models/              # 模型测试
│   ├── services/            # 服务测试
│   │   ├── test_llm_service.py
│   │   ├── test_milvus_service.py
│   │   └── test_mysql_service.py
│   └── workflow/            # 工作流测试
│       ├── test_graph.py
│       └── nodes/
│           ├── test_collector.py
│           ├── test_retriever.py
│           ├── test_diagnoser.py
│           ├── test_storer.py
│           └── test_accumulator.py
├── integration/             # 集成测试 (需要 Docker)
│   ├── conftest.py
│   ├── test_mysql_integration.py
│   ├── test_milvus_integration.py
│   └── test_workflow_integration.py
└── e2e/                     # 端到端测试
    └── test_api.py
```

### 2.3 测试类型说明

| 类型 | 位置 | 依赖 | CI 运行 |
|------|------|------|---------|
| 单元测试 | `tests/unit/` | 无外部依赖，使用 Mock | 每次 PR |
| 集成测试 | `tests/integration/` | Docker (MySQL/Milvus) | 手动触发 |
| 端到端测试 | `tests/e2e/` | 完整服务栈 | Release 前 |

---

## 3. 测试命名规范

### 3.1 命名格式

```python
def test_<method>_<scenario>_<expected>():
    """测试 [方法] 在 [场景] 时应该 [预期结果]."""
    pass
```

### 3.2 命名示例

| 测试名称 | 含义 |
|----------|------|
| `test_get_pending_exception_when_no_pending_returns_none` | 获取待处理异常，无待处理时返回 None |
| `test_diagnose_with_invalid_input_raises_validation_error` | 诊断方法，无效输入时抛出验证错误 |
| `test_generate_embedding_success` | 生成嵌入向量，成功场景 |
| `test_generate_embedding_truncates_long_text` | 生成嵌入向量，长文本截断 |
| `test_collect_job_found` | 采集节点，找到作业 |
| `test_collect_error` | 采集节点，错误场景 |

### 3.3 测试类组织

```python
class TestLLMService:
    """Test suite for LLMService."""

    # === 正常路径测试 ===

    @pytest.mark.asyncio
    async def test_generate_diagnosis_success(self): ...

    @pytest.mark.asyncio
    async def test_generate_embedding_success(self): ...

    # === 边界条件测试 ===

    @pytest.mark.asyncio
    async def test_generate_embedding_truncates_long_text(self): ...

    @pytest.mark.asyncio
    async def test_generate_diagnosis_with_empty_context(self): ...

    # === 错误处理测试 ===

    @pytest.mark.asyncio
    async def test_generate_diagnosis_api_error_raises(self): ...

    @pytest.mark.asyncio
    async def test_generate_embedding_timeout_raises(self): ...
```

---

## 4. TDD 实践流程

### 4.1 使用 /test 命令

```bash
# 为新模块生成测试骨架
/test src/oceanus_agent/services/new_service.py

# 为功能描述生成测试
/test 添加 Kafka 消费者健康检查功能

# 为 Bug 修复生成回归测试
/test fix: MySQL 连接超时问题 --type=bug
```

### 4.2 完整 TDD 流程

```bash
# 1. 创建分支
git checkout -b feat/new-feature

# 2. 生成测试骨架
/test src/oceanus_agent/services/new_service.py

# 3. 完善测试用例 (编写具体断言)
# 编辑 tests/unit/services/test_new_service.py

# 4. 运行测试确认失败 (Red)
./.venv/bin/pytest tests/unit/services/test_new_service.py -v
# 预期: FAILED (因为功能尚未实现)

# 5. 实现功能代码
# 编辑 src/oceanus_agent/services/new_service.py

# 6. 运行测试确认通过 (Green)
./.venv/bin/pytest tests/unit/services/test_new_service.py -v
# 预期: PASSED

# 7. 重构优化 (Refactor)
# 在测试保护下优化代码

# 8. 最终验证
./.venv/bin/pre-commit run --all-files
./.venv/bin/pytest tests/unit -v --cov --cov-fail-under=70

# 9. 提交代码
git add .
git commit -m "feat(services): add new service with tests"
```

### 4.3 AI 辅助 TDD 流程

```text
┌─────────────────────────────────────────────────────────────┐
│                  AI 辅助 TDD 流程                            │
│                                                              │
│  需求分析 ──→ /test 生成骨架 ──→ 完善测试用例 ──→ 确认 Red   │
│                       │                              │       │
│                       └──────────────────────────────│       │
│                                                      v       │
│            提交 PR ←── 重构优化 ←── 确认 Green ←── AI 实现   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. 测试模式与技巧

### 5.1 Mock 服务依赖

```python
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestDiagnoser:
    @pytest.fixture
    def mock_llm_service(self) -> MagicMock:
        """Mock LLM service."""
        service = MagicMock()
        service.classify_error = AsyncMock(return_value="checkpoint_failure")
        service.generate_diagnosis = AsyncMock(return_value={
            "root_cause": "network timeout",
            "confidence": 0.9,
        })
        return service

    @pytest.mark.asyncio
    async def test_diagnose_success(self, mock_llm_service):
        diagnoser = LLMDiagnoser(mock_llm_service)
        result = await diagnoser(state)
        assert result["diagnosis_result"]["confidence"] == 0.9
```

### 5.2 使用 conftest.py 共享 Fixtures

```python
# tests/conftest.py

@pytest.fixture
def sample_job_info() -> JobInfo:
    """示例作业信息."""
    return JobInfo(
        exception_id=1,
        job_id="job-123",
        job_name="Test Flink Job",
        error_message="Checkpoint failed",
    )

@pytest.fixture
def mock_mysql_service() -> AsyncMock:
    """Mock MySQL Service."""
    service = AsyncMock()
    service.get_pending_exception = AsyncMock(return_value=None)
    return service
```

### 5.3 测试异步代码

```python
import pytest

@pytest.mark.asyncio
async def test_async_method():
    """测试异步方法."""
    service = MyAsyncService()
    result = await service.async_method()
    assert result is not None
```

### 5.4 测试 Pydantic 模型

```python
import pytest
from pydantic import ValidationError

from oceanus_agent.models.diagnosis import DiagnosisResult


def test_diagnosis_result_valid():
    """测试有效的诊断结果."""
    result = DiagnosisResult(
        root_cause="network timeout",
        confidence=0.9,
    )
    assert result.confidence == 0.9


def test_diagnosis_result_invalid_confidence():
    """测试无效的置信度."""
    with pytest.raises(ValidationError):
        DiagnosisResult(
            root_cause="test",
            confidence=1.5,  # 超出范围
        )
```

### 5.5 参数化测试

```python
import pytest


@pytest.mark.parametrize("input,expected", [
    ("checkpoint_failure", "high"),
    ("memory_exceeded", "high"),
    ("network_timeout", "medium"),
    ("unknown_error", "low"),
])
def test_classify_priority(input, expected):
    """测试不同错误类型的优先级分类."""
    result = classify_priority(input)
    assert result == expected
```

---

## 6. 覆盖率要求

### 6.1 覆盖率目标

| 范围 | 最低要求 | 推荐目标 |
|------|----------|----------|
| 整体项目 | 70% | 80% |
| 新增代码 | 80% | 90% |
| 核心模块 (workflow, services) | 80% | 90% |

### 6.2 查看覆盖率报告

```bash
# 生成覆盖率报告
./.venv/bin/pytest tests/unit -v --cov=oceanus_agent --cov-report=html

# 查看 HTML 报告
open htmlcov/index.html

# 仅查看未覆盖的行
./.venv/bin/pytest tests/unit --cov=oceanus_agent --cov-report=term-missing
```

### 6.3 CI 覆盖率检查

```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: |
    pytest tests/unit -v \
      --cov=oceanus_agent \
      --cov-report=xml \
      --cov-fail-under=70  # 低于 70% 则失败
```

---

## 7. CI 中的测试检查

### 7.1 PR 测试文件检查

每个 PR 都会自动检查：

1. **源代码变更是否有对应测试**
   - 修改 `src/oceanus_agent/services/xxx.py`
   - 必须有 `tests/unit/services/test_xxx.py`

2. **检查失败处理**
   - CI 添加评论提醒
   - 阻止 PR 合并

### 7.2 测试检查清单

PR 模板包含以下检查项：

- [ ] **测试先行**: 测试文件早于实现代码创建
- [ ] **测试命名**: 遵循 `test_<method>_<scenario>_<expected>()` 规范
- [ ] **测试覆盖**: 包含正常路径、边界条件、错误处理
- [ ] **覆盖率达标**: 新代码覆盖率 >= 80%

---

## 8. 常见问题

### 8.1 测试难以编写的代码

**问题**: 代码耦合度高，难以 Mock

**解决方案**:
- 使用依赖注入
- 拆分大函数为小函数
- 提取接口层

### 8.2 测试运行缓慢

**问题**: 测试执行时间长

**解决方案**:
```bash
# 只运行相关测试
pytest tests/unit/services/test_llm_service.py -v

# 并行运行测试
pip install pytest-xdist
pytest tests/unit -n auto

# 跳过慢速测试
pytest tests/unit -m "not slow"
```

### 8.3 Flaky Tests 处理

**问题**: 测试时而通过时而失败

**解决方案**:
- 使用 `pytest-rerunfailures` 自动重试
- 检查是否有时间依赖
- 确保测试隔离性

```python
# 标记为 flaky 测试
@pytest.mark.flaky(reruns=3, reruns_delay=1)
async def test_network_call():
    ...
```

---

## 9. 参考资源

- [pytest 官方文档](https://docs.pytest.org/)
- [pytest-asyncio 文档](https://pytest-asyncio.readthedocs.io/)
- [Kent Beck - Test-Driven Development](https://www.amazon.com/Test-Driven-Development-Kent-Beck/dp/0321146530)
- 项目测试约定: `.claude/knowledge/conventions.md`
- /test 命令: `.claude/commands/test.md`
