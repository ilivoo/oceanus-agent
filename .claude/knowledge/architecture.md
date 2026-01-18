# Oceanus Agent 架构知识

## 系统架构

### 核心层次

```text
+-------------------------------------------------------------+
|                      API Layer (FastAPI)                     |
|  +-------------+  +-------------+  +---------------------+  |
|  | /diagnosis  |  | /knowledge  |  | /health             |  |
|  +------+------+  +------+------+  +----------+----------+  |
+---------|--------------|--------------------|---------------+
          |              |                    |
          v              v                    v
+-------------------------------------------------------------+
|                   Workflow Layer (LangGraph)                 |
|                                                              |
|  collect -> retrieve -> diagnose -> store -> accumulate      |
|                                                              |
+---------------------------+---------------------------------+
                            |
                            v
+-------------------------------------------------------------+
|                      Service Layer                           |
|  +---------------+  +---------------+  +-----------------+  |
|  | LLMService    |  | MilvusService |  | MySQLService    |  |
|  +-------+-------+  +-------+-------+  +--------+--------+  |
+-----------|-----------------|--------------------|----------+
            |                 |                    |
            v                 v                    v
      +----------+      +-----------+       +----------+
      | OpenAI   |      |  Milvus   |       |  MySQL   |
      +----------+      +-----------+       +----------+
```

### 数据流

1. **异常输入**: Flink Platform -> MySQL (job_exception 表)
2. **定时拉取**: Agent 每 60s 扫描待处理异常
3. **知识检索**: error_message -> Embedding -> Milvus 相似性搜索
4. **LLM 诊断**: context + prompt -> GPT-4o-mini -> 结构化诊断
5. **结果存储**: diagnosis_result -> MySQL (diagnosis_result 表)
6. **知识积累**: confidence > 0.8 -> Milvus (cases 集合)

## 关键设计决策

### 1. 为什么选择 LangGraph?

- 支持循环工作流 (重试机制)
- 内置状态管理和持久化
- 与 LangSmith 深度集成 (可观测性)
- 比 LangChain Agent 更可控

### 2. 为什么使用 Milvus 而非 Pinecone/Weaviate?

- 开源自托管，数据安全可控
- 性能优秀，支持大规模检索
- 社区活跃，文档完善

### 3. 为什么异步优先?

- 大量 I/O 操作 (LLM API, 数据库)
- 支持并发处理多个诊断任务
- 更好的资源利用率

## 扩展点

| 扩展需求 | 修改位置 | 说明 |
|----------|----------|------|
| 新增工作流节点 | workflow/nodes/ + graph.py | 创建节点类，注册到图 |
| 新增 LLM Provider | services/ + config/settings.py | 实现相同接口 |
| 新增知识源 | services/milvus_service.py | 添加新的 collection 查询 |
| 新增 API 端点 | api/routes/ | FastAPI 路由 |
