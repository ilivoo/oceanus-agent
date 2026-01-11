# 数据库设计文档

## 1. MySQL 表设计

### 1.1 异常表 (flink_job_exceptions)

存储 Flink 作业异常记录和诊断结果。

```sql
CREATE TABLE flink_job_exceptions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    job_id VARCHAR(64) NOT NULL,           -- Flink 作业 ID
    job_name VARCHAR(256),                 -- 作业名称
    job_type VARCHAR(32),                  -- 作业类型 (streaming/batch)
    job_config JSON,                       -- 作业配置
    error_message TEXT NOT NULL,           -- 错误信息
    error_type VARCHAR(64),                -- 错误类型（自动分类）
    status VARCHAR(32) DEFAULT 'pending',  -- 状态
    suggested_fix TEXT,                    -- 诊断结果（JSON）
    diagnosis_confidence FLOAT,            -- 诊断置信度
    diagnosed_at DATETIME,                 -- 诊断完成时间
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW() ON UPDATE NOW(),

    INDEX idx_status (status),
    INDEX idx_job_id (job_id),
    INDEX idx_error_type (error_type),
    INDEX idx_created_at (created_at)
);
```

**字段说明:**

| 字段 | 类型 | 说明 |
|------|------|------|
| status | VARCHAR | pending/in_progress/completed/failed |
| error_type | VARCHAR | checkpoint_failure/backpressure/deserialization_error/oom/network/other |
| suggested_fix | TEXT | JSON 格式诊断结果 |
| diagnosis_confidence | FLOAT | 0-1 之间的置信度 |

**suggested_fix JSON 结构:**

```json
{
  "root_cause": "根本原因描述",
  "detailed_analysis": "详细分析过程",
  "suggested_fix": "修复建议步骤",
  "priority": "high|medium|low",
  "related_docs": ["url1", "url2"]
}
```

### 1.2 知识案例表 (knowledge_cases)

存储诊断知识库的案例元数据。

```sql
CREATE TABLE knowledge_cases (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    case_id VARCHAR(32) UNIQUE NOT NULL,   -- 案例唯一标识
    error_type VARCHAR(64) NOT NULL,       -- 错误类型
    error_pattern TEXT,                    -- 错误模式（泛化后）
    root_cause TEXT NOT NULL,              -- 根本原因
    solution TEXT NOT NULL,                -- 解决方案
    source_exception_id BIGINT,            -- 来源异常 ID
    source_type ENUM('manual','auto'),     -- 来源类型
    verified BOOLEAN DEFAULT FALSE,        -- 人工审核标记
    created_at DATETIME DEFAULT NOW(),
    updated_at DATETIME DEFAULT NOW() ON UPDATE NOW(),

    INDEX idx_error_type (error_type),
    INDEX idx_source_type (source_type),
    INDEX idx_verified (verified),
    FOREIGN KEY (source_exception_id)
        REFERENCES flink_job_exceptions(id) ON DELETE SET NULL
);
```

**来源类型说明:**
- `manual`: 人工整理添加
- `auto`: 系统自动从高置信度诊断积累

## 2. Milvus 集合设计

### 2.1 案例集合 (flink_cases)

存储历史案例的向量表示，用于相似性检索。

| 字段 | 类型 | 说明 |
|------|------|------|
| case_id | VARCHAR(64) | 主键，关联 MySQL |
| vector | FLOAT_VECTOR[1536] | 案例文本嵌入 |
| error_type | VARCHAR(64) | 错误类型（过滤用） |
| error_pattern | VARCHAR(2000) | 错误模式 |
| root_cause | VARCHAR(2000) | 根本原因 |
| solution | VARCHAR(4000) | 解决方案 |

**索引配置:**
- 索引类型: IVF_FLAT
- 距离度量: COSINE
- nlist: 128

### 2.2 文档集合 (flink_docs)

存储 Flink 官方文档片段，用于 RAG 增强。

| 字段 | 类型 | 说明 |
|------|------|------|
| doc_id | VARCHAR(64) | 主键 |
| vector | FLOAT_VECTOR[1536] | 文档嵌入 |
| title | VARCHAR(512) | 文档标题 |
| content | VARCHAR(8000) | 文档内容 |
| doc_url | VARCHAR(512) | 原文链接 |
| category | VARCHAR(64) | 分类（checkpoint/state/network等） |

## 3. 数据流转

### 3.1 异常处理流程

```
┌────────────────┐
│ 新异常写入     │  status = 'pending'
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ Agent 获取     │  status = 'in_progress' (加锁)
└───────┬────────┘
        │
        ▼
┌────────────────┐
│ 诊断完成       │  status = 'completed'
│                │  suggested_fix = {...}
│                │  diagnosis_confidence = 0.85
└───────┬────────┘
        │
        ▼ (confidence >= 0.8)
┌────────────────┐
│ 知识积累       │  写入 knowledge_cases
│                │  写入 Milvus flink_cases
└────────────────┘
```

### 3.2 知识检索流程

```
异常信息
    │
    ▼ LLM Embedding
┌────────────────┐
│ 生成查询向量   │
└───────┬────────┘
        │
        ├─────────────────────┐
        ▼                     ▼
┌────────────────┐    ┌────────────────┐
│ flink_cases    │    │ flink_docs     │
│ 相似案例检索   │    │ 相关文档检索   │
└───────┬────────┘    └───────┬────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
           ┌─────────────┐
           │ 合并上下文  │
           └─────────────┘
```

## 4. 索引策略

### 4.1 MySQL 索引

```sql
-- 状态查询优化（最常用）
INDEX idx_status (status)

-- 作业维度查询
INDEX idx_job_id (job_id)

-- 错误类型统计
INDEX idx_error_type (error_type)

-- 时间范围查询
INDEX idx_created_at (created_at)
```

### 4.2 Milvus 索引

- 使用 IVF_FLAT 索引，适合中等规模数据
- 后期数据量增大可升级为 HNSW

## 5. 数据保留策略

| 数据类型 | 保留策略 |
|----------|----------|
| 异常记录 | 保留 90 天，可归档 |
| 诊断结果 | 随异常记录保留 |
| 知识案例 | 永久保留 |
| 文档向量 | 定期更新（跟随 Flink 版本） |

## 6. 备份策略

- MySQL: 每日全量备份 + binlog 增量
- Milvus: 每周全量备份（集合导出）
