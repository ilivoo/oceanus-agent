# AI 驱动开发流程完整示例

本文档提供从 Issue 到 Merge 的完整开发流程示例，帮助开发者理解和掌握标准化的 TDD/DDD/AI 驱动开发流程。

## 示例 1: 新功能开发 - 添加 Kafka 消费者服务

### Step 1: 需求分析

**场景**: 收到 GitHub Issue，要求添加 Kafka 消费者服务以接收实时异常事件。

**执行命令**:
```bash
/analyze-issue 添加 Kafka 消费者服务以接收 Flink 作业异常事件
```

**输出示例**:
```markdown
## 需求分析报告

### 1. 需求概述
添加 Kafka 消费者服务，替代现有的 MySQL 轮询方式，实现实时接收 Flink 作业异常事件。

### 2. 功能边界
**包含**：
- Kafka 消费者连接管理
- 消息反序列化（JSON → JobException）
- 消息确认机制（手动 commit）
- 健康检查端点

**不包含**：
- Kafka 生产者功能
- 消息重试队列

### 3. 验收标准
- [ ] 能够连接到 Kafka 集群并订阅指定 Topic
- [ ] 正确解析 JSON 消息为 JobException 模型
- [ ] 消费失败时不丢失消息（手动 commit）
- [ ] 提供 /health/kafka 健康检查端点
- [ ] 单元测试覆盖率 > 80%

### 4. 复杂度评估
- **级别**：中
- **预估代码量**：约 150 行
- **涉及模块**：services/, api/routes/, models/

### 5. 技术要点
- 使用 aiokafka 库进行异步消费
- 实现优雅关闭（graceful shutdown）
- 配置通过 Pydantic Settings 管理

### 6. 风险识别
- Kafka 连接不稳定时的重连机制
- 消息反序列化失败的错误处理

### 7. 下一步建议
- [ ] 是否需要设计文档：是
- [ ] 是否需要 ADR：否
- [ ] 建议的分支名：`feat/kafka-consumer`
```

---

### Step 2: 创建分支

```bash
git checkout -b feat/kafka-consumer
```

---

### Step 3: 生成设计文档

**执行命令**:
```bash
/design 添加 Kafka 消费者服务
```

**输出文件**: `docs/design/kafka-consumer.md`

**设计文档示例**:
```markdown
# Kafka 消费者服务设计文档

## 1. 概述
实现异步 Kafka 消费者服务，用于实时接收 Flink 作业异常事件。

## 2. 架构设计

### 2.1 组件位置
```
src/oceanus_agent/
├── services/
│   └── kafka_service.py    # 新增
├── config/
│   └── settings.py         # 修改：添加 Kafka 配置
└── api/routes/
    └── health.py           # 修改：添加 Kafka 健康检查
```

### 2.2 类图
```
┌─────────────────────────────────┐
│         KafkaService            │
├─────────────────────────────────┤
│ - _consumer: AIOKafkaConsumer   │
│ - _running: bool                │
├─────────────────────────────────┤
│ + connect()                     │
│ + disconnect()                  │
│ + consume() -> AsyncIterator    │
│ + health_check() -> bool        │
└─────────────────────────────────┘
```

## 3. 数据模型

```python
class KafkaSettings(BaseSettings):
    """Kafka 配置."""

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "flink-exceptions"
    kafka_group_id: str = "oceanus-agent"
    kafka_auto_offset_reset: str = "earliest"
```

## 4. 接口设计

### 4.1 KafkaService 接口

```python
class KafkaService:
    async def connect(self) -> None:
        """建立 Kafka 连接."""

    async def disconnect(self) -> None:
        """关闭 Kafka 连接."""

    async def consume(self) -> AsyncIterator[JobException]:
        """消费消息并返回解析后的异常对象."""

    async def health_check(self) -> bool:
        """检查 Kafka 连接健康状态."""
```

## 5. 测试策略

- 单元测试：Mock AIOKafkaConsumer
- 集成测试：使用 testcontainers-kafka

## 6. 影响评估

| 影响范围 | 变更类型 | 说明 |
|----------|----------|------|
| settings.py | 新增配置 | KafkaSettings |
| health.py | 新增端点 | /health/kafka |
| 依赖 | 新增库 | aiokafka |
```

---

### Step 4: 生成测试骨架 (TDD - Red Phase)

**执行命令**:
```bash
/test src/oceanus_agent/services/kafka_service.py
```

**输出文件**: `tests/unit/services/test_kafka_service.py`

**测试骨架示例**:
```python
"""Unit tests for KafkaService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from oceanus_agent.services.kafka_service import KafkaService


class TestKafkaService:
    """Test suite for KafkaService."""

    @pytest.fixture
    def mock_consumer(self) -> MagicMock:
        """Mock AIOKafkaConsumer."""
        consumer = MagicMock()
        consumer.start = AsyncMock()
        consumer.stop = AsyncMock()
        consumer.getone = AsyncMock()
        return consumer

    @pytest.fixture
    def kafka_service(self, mock_consumer: MagicMock) -> KafkaService:
        """Create KafkaService with mocked consumer."""
        with patch(
            "oceanus_agent.services.kafka_service.AIOKafkaConsumer",
            return_value=mock_consumer,
        ):
            return KafkaService()

    # === 连接管理测试 ===

    @pytest.mark.asyncio
    async def test_connect_when_not_connected_starts_consumer(
        self,
        kafka_service: KafkaService,
        mock_consumer: MagicMock,
    ) -> None:
        """测试 connect 在未连接时启动消费者."""
        await kafka_service.connect()
        mock_consumer.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_when_connected_stops_consumer(
        self,
        kafka_service: KafkaService,
        mock_consumer: MagicMock,
    ) -> None:
        """测试 disconnect 在已连接时停止消费者."""
        await kafka_service.connect()
        await kafka_service.disconnect()
        mock_consumer.stop.assert_called_once()

    # === 消息消费测试 ===

    @pytest.mark.asyncio
    async def test_consume_with_valid_message_returns_job_exception(
        self,
        kafka_service: KafkaService,
        mock_consumer: MagicMock,
    ) -> None:
        """测试 consume 解析有效消息返回 JobException."""
        # Arrange
        mock_message = MagicMock()
        mock_message.value = b'{"job_id": "123", "error": "OOM"}'
        mock_consumer.getone = AsyncMock(return_value=mock_message)

        # Act
        await kafka_service.connect()
        result = await kafka_service.consume().__anext__()

        # Assert
        assert result.job_id == "123"

    @pytest.mark.asyncio
    async def test_consume_with_invalid_json_skips_message(
        self,
        kafka_service: KafkaService,
        mock_consumer: MagicMock,
    ) -> None:
        """测试 consume 遇到无效 JSON 时跳过消息."""
        # TODO: 实现测试逻辑
        pass

    # === 健康检查测试 ===

    @pytest.mark.asyncio
    async def test_health_check_when_connected_returns_true(
        self,
        kafka_service: KafkaService,
    ) -> None:
        """测试 health_check 在已连接时返回 True."""
        await kafka_service.connect()
        result = await kafka_service.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_when_not_connected_returns_false(
        self,
        kafka_service: KafkaService,
    ) -> None:
        """测试 health_check 在未连接时返回 False."""
        result = await kafka_service.health_check()
        assert result is False
```

---

### Step 5: 运行测试确认失败 (Red)

```bash
pytest tests/unit/services/test_kafka_service.py -v
```

**预期输出**:
```
FAILED tests/unit/services/test_kafka_service.py::TestKafkaService::test_connect_when_not_connected_starts_consumer
  ModuleNotFoundError: No module named 'oceanus_agent.services.kafka_service'
```

---

### Step 6: 实现功能代码 (Green Phase)

**创建文件**: `src/oceanus_agent/services/kafka_service.py`

```python
"""Kafka consumer service for receiving Flink job exceptions."""

from collections.abc import AsyncIterator
from typing import Any

import structlog
from aiokafka import AIOKafkaConsumer

from oceanus_agent.config.settings import settings
from oceanus_agent.models.diagnosis import JobException

logger = structlog.get_logger(__name__)


class KafkaService:
    """Async Kafka consumer service."""

    def __init__(self) -> None:
        """Initialize Kafka service."""
        self._consumer: AIOKafkaConsumer | None = None
        self._running: bool = False

    async def connect(self) -> None:
        """Establish Kafka connection."""
        if self._consumer is not None:
            return

        self._consumer = AIOKafkaConsumer(
            settings.kafka_topic,
            bootstrap_servers=settings.kafka_bootstrap_servers,
            group_id=settings.kafka_group_id,
            auto_offset_reset=settings.kafka_auto_offset_reset,
            enable_auto_commit=False,
        )
        await self._consumer.start()
        self._running = True
        logger.info("kafka_connected", topic=settings.kafka_topic)

    async def disconnect(self) -> None:
        """Close Kafka connection."""
        if self._consumer is None:
            return

        self._running = False
        await self._consumer.stop()
        self._consumer = None
        logger.info("kafka_disconnected")

    async def consume(self) -> AsyncIterator[JobException]:
        """Consume messages and yield parsed JobException objects."""
        if self._consumer is None:
            raise RuntimeError("Not connected to Kafka")

        while self._running:
            try:
                message = await self._consumer.getone()
                data = self._parse_message(message.value)
                if data:
                    yield JobException(**data)
                    await self._consumer.commit()
            except Exception as e:
                logger.error("kafka_consume_error", error=str(e))

    def _parse_message(self, value: bytes) -> dict[str, Any] | None:
        """Parse message value to dict."""
        import json

        try:
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("kafka_parse_error", error=str(e))
            return None

    async def health_check(self) -> bool:
        """Check Kafka connection health."""
        return self._running and self._consumer is not None
```

---

### Step 7: 运行测试确认通过 (Green)

```bash
pytest tests/unit/services/test_kafka_service.py -v
```

**预期输出**:
```
tests/unit/services/test_kafka_service.py::TestKafkaService::test_connect_when_not_connected_starts_consumer PASSED
tests/unit/services/test_kafka_service.py::TestKafkaService::test_disconnect_when_connected_stops_consumer PASSED
tests/unit/services/test_kafka_service.py::TestKafkaService::test_consume_with_valid_message_returns_job_exception PASSED
tests/unit/services/test_kafka_service.py::TestKafkaService::test_health_check_when_connected_returns_true PASSED
tests/unit/services/test_kafka_service.py::TestKafkaService::test_health_check_when_not_connected_returns_false PASSED
```

---

### Step 8: 代码审查

**执行命令**:
```bash
/review --staged
```

**输出示例**:
```markdown
## 审查结果

### 发现的问题
无严重问题

### 改进建议
1. [INFO] kafka_service.py:45 - 考虑添加连接重试机制
2. [INFO] kafka_service.py:62 - 考虑限制单次消费的消息数量

### 总体评价
代码结构清晰，遵循项目规范。测试覆盖完整。建议合并。
```

---

### Step 9: 代码格式化和检查

```bash
# 格式化
./.venv/bin/ruff format src/ tests/
./.venv/bin/ruff check --fix src/ tests/

# 完整检查
./.venv/bin/pre-commit run --all-files

# 覆盖率检查
pytest tests/unit -v --cov=oceanus_agent --cov-fail-under=70
```

---

### Step 10: 提交代码

```bash
git add .
git commit -m "feat(services): add Kafka consumer service

- Implement async Kafka consumer with aiokafka
- Add connection management and graceful shutdown
- Add health check endpoint support
- Include comprehensive unit tests

Closes #42"
```

---

### Step 11: 创建 PR

```bash
git push origin feat/kafka-consumer
```

在 GitHub 创建 PR，填写描述：

```markdown
## Summary
- 添加 Kafka 消费者服务以实时接收 Flink 作业异常
- 实现连接管理、消息解析、健康检查功能

## Test plan
- [x] 单元测试通过
- [x] 覆盖率 > 70%
- [ ] 集成测试（需要 Kafka 环境）

## Checklist
- [x] 遵循 TDD 流程
- [x] 代码格式化通过
- [x] 类型检查通过
```

---

### Step 12: CI 检查和审查

等待以下检查通过：
- [ ] Code Quality (pre-commit)
- [ ] Unit Tests
- [ ] Security Scan
- [ ] Build Docker Image
- [ ] CodeRabbit AI Review

---

### Step 13: 合并

人工 Review 通过后，Squash Merge 到 main。

---

## 示例 2: Bug 修复 - MySQL 连接超时

### Step 1: 分析问题

**执行命令**:
```bash
/analyze-issue fix: MySQL 连接在高负载下超时 #123
```

**输出**:
```markdown
### 复杂度评估
- **级别**：低
- **预估代码量**：约 20 行
- **涉及模块**：services/mysql_service.py

### 下一步建议
- [ ] 是否需要设计文档：否
- [ ] 建议的分支名：`fix/mysql-timeout`
```

---

### Step 2: 生成回归测试

```bash
git checkout -b fix/mysql-timeout
/test fix: MySQL 连接超时 --type=bug
```

**测试骨架**:
```python
"""Regression tests for MySQL connection timeout fix."""

import pytest
from unittest.mock import AsyncMock, patch


class TestMySQLTimeoutFix:
    """Regression test for issue #123."""

    @pytest.mark.asyncio
    async def test_connection_timeout_with_high_load(self) -> None:
        """复现 Bug: 高负载下 MySQL 连接超时.

        Issue: #123
        原因: 连接池 size 过小，未设置合适的超时时间
        修复: 增加连接池 size，添加 connect_timeout 配置
        """
        # Arrange: 模拟高负载场景
        # Act: 并发执行多个数据库操作
        # Assert: 所有操作应在合理时间内完成，无超时异常
        pass
```

---

### Step 3: 完善测试并实现修复

```python
# 测试用例
@pytest.mark.asyncio
async def test_connection_pool_handles_concurrent_requests(self) -> None:
    """测试连接池能处理并发请求."""
    service = MySQLService()

    # 并发执行 20 个查询
    tasks = [service.get_pending_exception() for _ in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 所有请求应成功完成，无超时
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0
```

---

### Step 4: 提交修复

```bash
./.venv/bin/pre-commit run --all-files
git add .
git commit -m "fix(services): resolve MySQL connection timeout under load

- Increase connection pool size from 5 to 20
- Add connect_timeout configuration (default: 10s)
- Add pool_recycle to prevent stale connections

Fixes #123"
```

---

## 示例 3: CI 失败诊断

### 场景

CI 检查失败，错误信息：
```
FAILED tests/unit/workflow/test_nodes.py::test_diagnose_node
TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'
```

### 诊断

```bash
/diagnose "TypeError: unsupported operand type(s) for +: 'NoneType' and 'str' in test_nodes.py"
```

**输出**:
```markdown
## 诊断报告

### 根因分析
- 错误位置: `workflow/nodes/diagnoser.py:45`
- 原因: `state.context` 为 None 时未做空值检查
- 触发条件: 当 retriever 节点未返回任何结果时

### 修复建议
```python
# 修改前
prompt = state.context + state.error_message

# 修改后
context = state.context or ""
prompt = context + state.error_message
```

### 预防措施
- 添加空值检查测试用例
- 考虑使用 Optional 类型提示
```

---

## 流程检查清单

### 新功能开发
- [ ] `/analyze-issue` 分析需求
- [ ] 评估复杂度，决定是否需要设计文档
- [ ] 创建 feature 分支
- [ ] `/design` 生成设计文档（中/高复杂度）
- [ ] `/test` 生成测试骨架
- [ ] TDD 循环：Red → Green → Refactor
- [ ] `/review` 代码审查
- [ ] `pre-commit run --all-files`
- [ ] 创建 PR
- [ ] 等待 CI 和 CodeRabbit 审查
- [ ] 人工 Review
- [ ] 合并到 main

### Bug 修复
- [ ] `/analyze-issue` 分析问题
- [ ] 创建 fix 分支
- [ ] `/test --type=bug` 生成回归测试
- [ ] TDD 循环
- [ ] `/review` 审查
- [ ] 提交并创建 PR
- [ ] 合并

### CI 失败处理
- [ ] `/diagnose` 分析错误
- [ ] 根据建议修复
- [ ] 重新运行检查
- [ ] 更新 PR

---

## 相关文档

- [Claude 命令指南](../../.claude/commands/README.md)
- [知识库说明](../../.claude/knowledge/README.md)
- [TDD 开发指南](tdd.md)
- [AI Code 研发全流程](ai-code-workflow.md)
