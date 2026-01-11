# 开发指南

## 1. 环境准备

### 1.1 系统要求
- Python 3.11+
- Docker & Docker Compose
- MySQL 8.0+
- Milvus 2.4+

### 1.2 安装依赖

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 1.3 配置环境变量

```bash
cp .env.example .env

# 编辑 .env 文件，填入：
# - OPENAI_API_KEY
# - LANGCHAIN_API_KEY (可选，用于 LangSmith)
# - MySQL 和 Milvus 连接信息
```

## 2. 本地开发

### 2.1 启动依赖服务

```bash
cd deploy/docker
docker-compose up -d mysql milvus etcd minio
```

### 2.2 初始化数据库

```bash
# MySQL
mysql -h localhost -u oceanus -p oceanus_agent < scripts/init_db.sql

# Milvus
python scripts/init_milvus.py
```

### 2.3 运行 Agent

```bash
python -m oceanus_agent
```

### 2.4 插入测试数据

```sql
INSERT INTO flink_job_exceptions
(job_id, job_name, job_type, error_message, error_type)
VALUES
('test-001', 'Test Job', 'streaming',
 'Checkpoint expired before completing.',
 'checkpoint_failure');
```

## 3. 代码结构

### 3.1 添加新服务

```python
# src/oceanus_agent/services/new_service.py

class NewService:
    def __init__(self, settings: NewSettings):
        self.settings = settings

    async def do_something(self) -> Result:
        ...
```

### 3.2 添加新节点

```python
# src/oceanus_agent/workflow/nodes/new_node.py

from langsmith import traceable
from oceanus_agent.models.state import DiagnosisState

class NewNode:
    def __init__(self, service: SomeService):
        self.service = service

    @traceable(name="new_node")
    async def __call__(self, state: DiagnosisState) -> DiagnosisState:
        # 处理逻辑
        result = await self.service.do_something()
        return {**state, "new_field": result}
```

### 3.3 注册节点到工作流

```python
# src/oceanus_agent/workflow/graph.py

def build_diagnosis_workflow(settings):
    ...
    new_node = NewNode(new_service)

    workflow.add_node("new_node", new_node)
    workflow.add_edge("previous_node", "new_node")
    ...
```

## 4. Prompt 调优

### 4.1 修改诊断 Prompt

编辑 `src/oceanus_agent/config/prompts.py`:

```python
DIAGNOSIS_SYSTEM_PROMPT = """
你是 Flink 诊断专家...

# 添加新的诊断领域
6. 新增诊断类型 - 说明

# 修改输出格式
...
"""
```

### 4.2 测试 Prompt

```python
# 直接测试 LLM 响应
from oceanus_agent.services.llm_service import LLMService
from oceanus_agent.config.settings import settings

llm = LLMService(settings.openai)
result = await llm.generate_diagnosis(test_job_info, test_context)
print(result)
```

## 5. 测试

### 5.1 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_workflow.py -v

# 带覆盖率
pytest tests/ --cov=oceanus_agent --cov-report=html
```

### 5.2 编写测试

```python
# tests/test_services/test_mysql_service.py

import pytest
from oceanus_agent.services.mysql_service import MySQLService

@pytest.fixture
async def mysql_service():
    service = MySQLService(test_settings.mysql)
    yield service
    await service.close()

@pytest.mark.asyncio
async def test_get_pending_exception(mysql_service):
    result = await mysql_service.get_pending_exception()
    assert result is None or "job_id" in result
```

## 6. 代码质量

### 6.1 代码检查

```bash
# Ruff 检查
ruff check src/

# 自动修复
ruff check --fix src/

# 类型检查
mypy src/
```

### 6.2 格式化

```bash
# 使用 Black
black src/

# 使用 isort
isort src/
```

## 7. 调试

### 7.1 启用调试日志

```bash
export LOG_LEVEL=DEBUG
python -m oceanus_agent
```

### 7.2 LangSmith 追踪

1. 设置 `LANGCHAIN_TRACING_V2=true`
2. 设置 `LANGCHAIN_API_KEY`
3. 访问 https://smith.langchain.com 查看追踪

### 7.3 单步调试

```python
# 直接调用工作流
from oceanus_agent.workflow.graph import DiagnosisWorkflow
from oceanus_agent.config.settings import settings

workflow = DiagnosisWorkflow(settings)
result = await workflow.run("debug-thread-1")
print(result)
```

## 8. 常见问题

### 8.1 MySQL 连接失败
```
检查:
1. MySQL 服务是否启动
2. 用户名密码是否正确
3. 数据库是否存在
```

### 8.2 Milvus 连接失败
```
检查:
1. Milvus 依赖服务 (etcd, minio) 是否启动
2. 端口 19530 是否可访问
```

### 8.3 OpenAI API 错误
```
检查:
1. API Key 是否有效
2. 余额是否充足
3. 网络是否可访问
```
