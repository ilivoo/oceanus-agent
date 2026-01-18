# /test 命令

生成符合项目规范的测试骨架，支持 TDD（测试驱动开发）流程。

## 使用方式

```text
/test [目标]                     # 为模块或功能生成测试
/test [目标] --type=unit        # 生成单元测试 (默认)
/test [目标] --type=integration # 生成集成测试
/test [目标] --type=bug         # 为 Bug 修复生成回归测试
```

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `目标` | 模块路径或功能描述 | `src/oceanus_agent/services/kafka_service.py` |
| `--type` | 测试类型 | `unit` (默认), `integration`, `bug` |

## 执行流程

1. **解析目标**
   - 如果是文件路径：分析模块结构和公开接口
   - 如果是功能描述：根据上下文推断测试需求

2. **检索上下文**
   - 阅读目标模块代码（如存在）
   - 查看同目录现有测试文件
   - 参考 `tests/conftest.py` 中的 fixtures

3. **生成测试骨架**
   - 遵循 `test_<method>_<scenario>_<expected>()` 命名规范
   - 包含必要的 imports 和 fixtures
   - 按正常路径 / 边界条件 / 错误处理分组

4. **输出测试文件**
   - 使用 Write 工具创建测试文件
   - 位置根据源文件路径自动推断

## 测试文件位置规则

| 源文件路径 | 测试文件路径 |
|-----------|-------------|
| `src/oceanus_agent/services/xxx.py` | `tests/unit/services/test_xxx.py` |
| `src/oceanus_agent/workflow/nodes/xxx.py` | `tests/unit/workflow/nodes/test_xxx.py` |
| `src/oceanus_agent/models/xxx.py` | `tests/unit/models/test_xxx.py` |
| `src/oceanus_agent/api/xxx.py` | `tests/unit/api/test_xxx.py` |

## 测试骨架模板

### 单元测试模板

```python
"""Unit tests for [ModuleName]."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from oceanus_agent.xxx import TargetClass


class TestTargetClass:
    """Test suite for TargetClass."""

    @pytest.fixture
    def mock_dependency(self) -> MagicMock:
        """Mock dependency service."""
        service = MagicMock()
        # TODO: 配置 mock 返回值
        return service

    @pytest.fixture
    def target(self, mock_dependency: MagicMock) -> TargetClass:
        """Create TargetClass instance with mocked dependencies."""
        return TargetClass(mock_dependency)

    # === 正常路径测试 ===

    @pytest.mark.asyncio
    async def test_method_name_with_valid_input_returns_expected(
        self,
        target: TargetClass,
    ) -> None:
        """测试 [方法] 在 [正常输入] 时应该 [返回预期结果]."""
        # Arrange
        # TODO: 设置测试数据

        # Act
        result = await target.method_name(...)

        # Assert
        assert result == expected

    # === 边界条件测试 ===

    @pytest.mark.asyncio
    async def test_method_name_with_empty_input_returns_empty(
        self,
        target: TargetClass,
    ) -> None:
        """测试 [方法] 在 [空输入] 时应该 [返回空结果]."""
        # TODO: 实现边界条件测试
        pass

    # === 错误处理测试 ===

    @pytest.mark.asyncio
    async def test_method_name_with_invalid_input_raises_error(
        self,
        target: TargetClass,
    ) -> None:
        """测试 [方法] 在 [无效输入] 时应该 [抛出异常]."""
        with pytest.raises(ValueError):
            await target.method_name(invalid_input)
```

### Bug 修复测试模板

```python
"""Regression tests for [Bug Description]."""

import pytest


class TestBugFixIssueXXX:
    """Regression test for issue #XXX."""

    @pytest.mark.asyncio
    async def test_bug_reproduction_issue_xxx(self) -> None:
        """复现 Bug: [Bug 描述].

        Issue: #XXX
        原因: [根因分析]
        修复: [修复方案]
        """
        # Arrange: 设置触发 Bug 的条件
        # TODO: 实现 Bug 复现场景

        # Act: 执行触发 Bug 的操作
        # TODO: 执行操作

        # Assert: 验证 Bug 已修复
        # TODO: 添加断言
        pass
```

### 集成测试模板

```python
"""Integration tests for [Feature]."""

import pytest

from oceanus_agent.config.settings import settings
# TODO: 根据实际测试的服务替换下面的导入
# from oceanus_agent.services.xxx_service import XxxService as RealService


@pytest.fixture(scope="module")
async def real_service():
    """Create real service with test configuration.

    注意：请将 RealService 替换为实际测试的服务类，例如：
    - MilvusService
    - MySQLService
    - LLMService
    """
    # TODO: 替换为实际的服务类
    # service = RealService(settings)
    # await service.connect()
    # yield service
    # await service.disconnect()
    raise NotImplementedError("请替换 RealService 为实际的服务类")


class TestFeatureIntegration:
    """Integration tests for [Feature]."""

    @pytest.mark.asyncio
    async def test_end_to_end_scenario(self, real_service) -> None:
        """测试端到端场景."""
        # TODO: 实现集成测试
        pass
```

## 使用示例

### 示例 1: 为现有模块生成测试

```bash
/test src/oceanus_agent/services/llm_service.py
```

输出：根据 `llm_service.py` 的公开方法生成测试骨架。

### 示例 2: 为新功能生成测试

```bash
/test 添加 Kafka 消费者健康检查功能
```

输出：根据功能描述生成测试骨架，包含健康检查相关测试用例。

### 示例 3: 为 Bug 修复生成测试

```bash
/test fix: MySQL 连接超时问题 --type=bug
```

输出：生成回归测试骨架，包含 Bug 复现场景。

## TDD 工作流程

```text
1. /test [功能描述]        # 生成测试骨架
       ↓
2. 完善测试用例             # 编写具体断言
       ↓
3. pytest tests/unit/xxx   # 运行测试 (预期失败 - Red)
       ↓
4. 实现功能代码             # 让测试通过
       ↓
5. pytest tests/unit/xxx   # 运行测试 (预期通过 - Green)
       ↓
6. 重构优化                 # 在测试保护下重构
```

## 关联知识库

| 知识库 | 用途 |
|--------|------|
| [conventions.md](../knowledge/conventions.md) | 测试命名规范 (第 118-159 行) |
| [patterns.md](../knowledge/patterns.md) | Mock 模式、异步测试模式 |
| [architecture.md](../knowledge/architecture.md) | 了解模块依赖关系 |

## 相关文档

- [命令总览](README.md)
- [TDD 开发指南](../../docs/guides/tdd.md)
- [现有 fixtures](../../tests/conftest.py)
- [端到端示例](../../docs/guides/workflow-example.md)
