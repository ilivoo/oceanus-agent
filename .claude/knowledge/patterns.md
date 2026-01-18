# 代码模式指南

## 1. Pydantic 模型模式

### 配置模型

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class ServiceSettings(BaseSettings):
    """服务配置"""

    host: str = Field(default="localhost", description="服务地址")
    port: int = Field(default=8080, ge=1, le=65535)
    timeout_seconds: int = Field(default=30, ge=1)

    model_config = ConfigDict(
        env_prefix="SERVICE_",
        env_file=".env",
    )
```

### API 请求/响应模型

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class DiagnosisRequest(BaseModel):
    """诊断请求"""

    exception_id: str = Field(..., description="异常 ID")
    priority: str = Field(default="medium", pattern="^(high|medium|low)$")

class DiagnosisResponse(BaseModel):
    """诊断响应"""

    request_id: str
    status: str
    result: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

## 2. 异步数据库操作模式

### 查询模式

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

async def get_pending_exception(session: AsyncSession) -> Optional[JobException]:
    """获取待处理异常 (带行锁)"""
    stmt = (
        select(JobException)
        .where(JobException.status == "pending")
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

### 事务模式

```python
async def update_with_transaction(
    session: AsyncSession,
    exception_id: str,
    diagnosis: dict,
) -> None:
    """事务更新"""
    async with session.begin():
        # 更新异常状态
        await session.execute(
            update(JobException)
            .where(JobException.id == exception_id)
            .values(status="completed")
        )
        # 插入诊断结果
        session.add(DiagnosisResult(**diagnosis))
```

## 3. LangGraph 节点模式

### 节点类定义

```python
from typing import Any
from langsmith import traceable

class WorkflowNode:
    """工作流节点基类"""

    def __init__(self, service: SomeService):
        self.service = service

    @traceable(name="node_name")
    async def __call__(self, state: DiagnosisState) -> dict[str, Any]:
        """
        执行节点逻辑

        Args:
            state: 当前工作流状态

        Returns:
            更新后的状态字段
        """
        try:
            result = await self._process(state)
            return {"result": result, "error": None}
        except Exception as e:
            logger.error("node_failed", error=str(e))
            return {"error": str(e)}

    async def _process(self, state: DiagnosisState) -> Any:
        """实际处理逻辑 (子类实现)"""
        raise NotImplementedError
```

## 4. 服务层模式

### 服务类定义

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

class MilvusService:
    """Milvus 向量服务"""

    def __init__(self, settings: MilvusSettings):
        self.settings = settings
        self._client: Optional[MilvusClient] = None

    async def connect(self) -> None:
        """建立连接"""
        self._client = await MilvusClient.connect(
            host=self.settings.host,
            port=self.settings.port,
        )

    async def disconnect(self) -> None:
        """关闭连接"""
        if self._client:
            await self._client.close()
            self._client = None

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[MilvusClient, None]:
        """会话上下文管理器"""
        await self.connect()
        try:
            yield self._client
        finally:
            await self.disconnect()
```

## 5. 错误处理模式

### 自定义异常

```python
class OceanusError(Exception):
    """基础异常类"""

    def __init__(self, message: str, code: str = "UNKNOWN"):
        self.message = message
        self.code = code
        super().__init__(message)

class DiagnosisError(OceanusError):
    """诊断相关异常"""

    pass

class RetryableError(OceanusError):
    """可重试异常"""

    pass
```

### 重试装饰器

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def call_llm_with_retry(prompt: str) -> str:
    """带重试的 LLM 调用"""
    return await llm_service.generate(prompt)
```

## 6. 日志模式

### Structlog 配置

```python
import structlog

logger = structlog.get_logger(__name__)

# 使用示例
logger.info(
    "diagnosis_completed",
    exception_id=exc_id,
    duration_ms=duration,
    confidence=result.confidence,
)

logger.error(
    "llm_call_failed",
    error=str(e),
    retry_count=retry_count,
    exc_info=True,
)
```
