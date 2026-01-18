# 项目约定规范

## 1. 代码风格

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `DiagnosisService`, `JobCollector` |
| 函数/方法 | snake_case | `get_pending_exception`, `generate_diagnosis` |
| 变量 | snake_case | `job_info`, `retry_count` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| 私有成员 | _前缀 | `_client`, `_process` |
| 类型变量 | T/TResult 等 | `T`, `TModel`, `TResult` |

### 文件命名

- Python 模块: `snake_case.py`
- 测试文件: `test_module_name.py`
- 配置文件: `kebab-case.yaml`
- 文档: `kebab-case.md` 或 `UPPER_SNAKE.md` (README, CHANGELOG 等)

## 2. 目录结构约定

```text
src/oceanus_agent/
├── __init__.py          # 包初始化，导出公共 API
├── __main__.py          # CLI 入口点
├── api/                 # FastAPI 路由 (一个文件对应一组相关端点)
│   ├── __init__.py
│   ├── app.py           # FastAPI 应用实例
│   └── routes/
│       ├── diagnosis.py # /diagnosis 相关端点
│       └── health.py    # /health 相关端点
├── config/              # 配置定义
│   ├── settings.py      # Pydantic Settings
│   └── prompts.py       # LLM Prompt 模板
├── models/              # Pydantic 数据模型
│   ├── base.py          # 基础模型
│   ├── diagnosis.py     # 诊断相关模型
│   └── state.py         # 工作流状态
├── services/            # 外部服务封装 (每个服务一个文件)
│   ├── llm_service.py
│   ├── milvus_service.py
│   └── mysql_service.py
└── workflow/            # LangGraph 工作流
    ├── graph.py         # 图构建
    └── nodes/           # 节点实现
```

## 3. Git 提交规范

### Commit Message 格式

```text
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `docs` | 文档变更 |
| `style` | 代码格式 (不影响逻辑) |
| `refactor` | 重构 (非 feat/fix) |
| `perf` | 性能优化 |
| `test` | 测试相关 |
| `chore` | 构建/工具变更 |

### Scope 范围

- `workflow` - 工作流相关
- `api` - API 接口
- `services` - 服务层
- `models` - 数据模型
- `config` - 配置
- `deps` - 依赖

### 示例

```text
feat(workflow): add retry mechanism for diagnose node

- Implement exponential backoff with tenacity
- Add max_retry_count configuration
- Update state to track retry count

Closes #123
```

## 4. 分支管理

### 分支命名

```text
feat/add-xxx          # 新功能
fix/issue-123         # Bug 修复
refactor/xxx          # 重构
docs/update-xxx       # 文档
chore/update-deps     # 维护任务
```

### 工作流程

1. 从 `main` 创建特性分支
2. 开发并提交
3. 运行 `pre-commit run --all-files`
4. 创建 PR
5. Code Review
6. Squash Merge 到 `main`

## 5. 测试约定

### 测试文件组织

```text
tests/
├── unit/                    # 单元测试 (不依赖外部服务)
│   ├── test_models.py
│   ├── test_services.py
│   └── workflow/
│       └── test_nodes.py
├── integration/             # 集成测试 (需要 Docker)
│   └── test_full_workflow.py
└── conftest.py              # 共享 fixtures
```

### 测试命名

```python
def test_<method>_<scenario>_<expected>():
    """测试 [方法] 在 [场景] 时应该 [预期结果]"""
    pass

# 示例
def test_get_pending_exception_when_no_pending_returns_none():
    ...

def test_diagnose_with_invalid_input_raises_validation_error():
    ...
```

### Mock 约定

```python
# 使用 pytest-mock
def test_something(mocker):
    mock_llm = mocker.patch("oceanus_agent.services.llm_service.LLMService")
    ...

# 使用 AsyncMock 处理异步
mock_service.generate_diagnosis = AsyncMock(return_value=expected_result)
```

## 6. 文档约定

### Docstring 格式

```python
async def diagnose_exception(
    job_info: JobInfo,
    context: RetrievedContext,
) -> DiagnosisResult:
    """
    对作业异常进行诊断。

    使用 LLM 分析异常信息和检索到的上下文，生成结构化的诊断结果。

    Args:
        job_info: 作业异常信息
        context: RAG 检索的相关上下文

    Returns:
        结构化的诊断结果，包含根因、分析和修复建议

    Raises:
        DiagnosisError: LLM 调用失败或响应解析失败
        RetryableError: 可重试的临时错误

    Examples:
        >>> result = await diagnose_exception(job_info, context)
        >>> print(result.root_cause)
    """
```

### TODO 格式

```python
# TODO(author): 描述待办事项 - #issue_number
# FIXME(author): 描述需要修复的问题
# HACK(author): 描述临时方案和原因
```

## 7. 错误处理约定

### 异常层次

```text
OceanusError              # 基础异常
├── ConfigError           # 配置错误
├── ServiceError          # 服务层错误
│   ├── LLMError
│   ├── MilvusError
│   └── MySQLError
├── WorkflowError         # 工作流错误
│   ├── DiagnosisError
│   └── StateError
└── RetryableError        # 可重试错误
```

### 错误处理原则

1. 在边界处捕获异常
2. 记录完整上下文
3. 向上传递自定义异常
4. 避免吞掉异常
