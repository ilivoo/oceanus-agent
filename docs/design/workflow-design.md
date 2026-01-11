# 工作流设计文档

## 1. LangGraph 工作流概述

本系统使用 LangGraph 构建诊断工作流，包含 5 个核心节点和条件路由。

## 2. 工作流状态

### 2.1 DiagnosisState

```python
class DiagnosisState(TypedDict):
    job_info: Optional[JobInfo]           # 当前处理的异常信息
    status: DiagnosisStatus               # 工作流状态
    retrieved_context: Optional[dict]     # RAG 检索结果
    diagnosis_result: Optional[dict]      # LLM 诊断结果
    start_time: str                       # 开始时间
    end_time: Optional[str]               # 结束时间
    error: Optional[str]                  # 错误信息
    retry_count: int                      # 重试次数
```

### 2.2 状态流转

```
PENDING → IN_PROGRESS → COMPLETED
                     ↘ FAILED
```

## 3. 工作流节点

### 3.1 collect (数据采集)

**职责:** 从 MySQL 获取一条待诊断的异常

**输入:** 初始状态
**输出:** 包含 job_info 的状态

**关键逻辑:**
```python
async def __call__(self, state):
    job_info = await self.mysql_service.get_pending_exception()
    if job_info is None:
        return {..., "status": COMPLETED}  # 无待处理任务
    return {..., "job_info": job_info, "status": IN_PROGRESS}
```

**数据库操作:**
- SELECT ... FOR UPDATE SKIP LOCKED (避免并发冲突)
- UPDATE status = 'in_progress'

### 3.2 retrieve (知识检索)

**职责:** 从 Milvus 检索相关知识上下文

**输入:** 包含 job_info 的状态
**输出:** 包含 retrieved_context 的状态

**关键逻辑:**
```python
async def __call__(self, state):
    # 1. 构建查询文本
    query = f"{error_type} {error_message}"

    # 2. 生成嵌入向量
    vector = await llm_service.generate_embedding(query)

    # 3. 并行检索案例和文档
    cases = await milvus.search_similar_cases(vector)
    docs = await milvus.search_doc_snippets(vector)

    return {..., "retrieved_context": {"cases": cases, "docs": docs}}
```

**检索参数:**
- 相似案例: top 3
- 相关文档: top 3
- 可按 error_type 过滤

### 3.3 diagnose (LLM 诊断)

**职责:** 调用 LLM 生成诊断结果

**输入:** 包含 job_info 和 retrieved_context 的状态
**输出:** 包含 diagnosis_result 的状态

**Prompt 结构:**
```
System: 你是 Flink 诊断专家...

User:
## 作业信息
- Job ID: xxx
- 错误类型: xxx

## 错误信息
{error_message}

## 作业配置
{job_config}

## 参考上下文
### 相似案例
...
### 相关文档
...

请诊断并输出结构化结果。
```

**结构化输出:**
```python
class DiagnosisOutput(BaseModel):
    root_cause: str
    detailed_analysis: str
    suggested_fix: str
    priority: Literal["high", "medium", "low"]
    confidence: float  # 0-1
    related_docs: List[str]
```

**重试机制:**
- 最多重试 3 次
- 指数退避等待

### 3.4 store (结果存储)

**职责:** 将诊断结果写入 MySQL

**输入:** 包含 diagnosis_result 的状态
**输出:** 更新 status 的状态

**关键逻辑:**
```python
async def __call__(self, state):
    if diagnosis_result:
        await mysql.update_diagnosis_result(
            exception_id=job_info["exception_id"],
            diagnosis=diagnosis_result,
            status="completed"
        )
    else:
        await mysql.mark_exception_failed(...)
```

### 3.5 accumulate (知识积累)

**职责:** 将高置信度诊断加入知识库

**输入:** 完成诊断的状态
**输出:** 原状态（副作用操作）

**触发条件:**
- diagnosis_result 存在
- confidence >= 0.8 (可配置)

**关键逻辑:**
```python
async def __call__(self, state):
    if confidence < threshold:
        return state  # 跳过

    # 1. 生成 case_id
    case_id = f"case_{uuid.uuid4().hex[:12]}"

    # 2. 提取错误模式
    pattern = extract_error_pattern(error_message)

    # 3. 生成嵌入
    embedding = await llm.generate_embedding(case_text)

    # 4. 写入 Milvus
    await milvus.insert_case(...)

    # 5. 写入 MySQL
    await mysql.insert_knowledge_case(...)
```

**错误模式提取:**
- 替换数字为 `<NUM>`
- 替换 UUID 为 `<UUID>`
- 替换时间戳为 `<TIMESTAMP>`
- 替换路径为 `<PATH>`

## 4. 条件路由

### 4.1 collect 后路由

```python
def should_continue_after_collect(state):
    if state.get("error"):
        return "handle_error"
    if state.get("job_info") is None:
        return END  # 无待处理任务
    return "retrieve"
```

### 4.2 diagnose 后路由

```python
def should_continue_after_diagnose(state):
    if state.get("error"):
        if state.get("retry_count", 0) < 3:
            return "diagnose"  # 重试
        return "handle_error"
    return "store"
```

## 5. 错误处理

### 5.1 节点级错误
- 每个节点内部 try-catch
- 记录错误到 state.error
- 不抛出异常，让路由决定处理

### 5.2 工作流级错误
- handle_error 节点统一处理
- 标记异常为 failed
- 记录错误日志

## 6. 监控与追踪

### 6.1 LangSmith 集成

每个节点使用 `@traceable` 装饰器：

```python
from langsmith import traceable

class JobCollector:
    @traceable(name="collect_job_exception")
    async def __call__(self, state):
        ...
```

### 6.2 追踪内容
- 节点执行时间
- 输入/输出状态
- LLM 调用详情
- 错误堆栈

## 7. 扩展点

### 7.1 添加新节点

1. 在 `workflow/nodes/` 创建节点类
2. 实现 `async def __call__(self, state)` 方法
3. 在 `workflow/graph.py` 注册节点
4. 定义边和路由

### 7.2 修改路由逻辑

1. 在 `workflow/graph.py` 添加路由函数
2. 使用 `add_conditional_edges()` 配置
