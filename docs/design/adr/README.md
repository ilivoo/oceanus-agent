# 架构决策记录 (ADR) 索引

本目录记录 Oceanus Agent 项目的重要架构决策。

## ADR 状态说明

| 状态 | 含义 |
|------|------|
| Proposed | 正在讨论中的决策 |
| Accepted | 已批准并实施的决策 |
| Deprecated | 不再相关的决策 |
| Superseded | 被新决策取代 |

## ADR 列表

| 编号 | 标题 | 状态 | 日期 |
|------|------|------|------|
| [ADR-001](./001-langgraph-workflow-engine.md) | 采用 LangGraph 作为工作流引擎 | Accepted | 2024-01-01 |
| [ADR-002](./002-milvus-vector-database.md) | 采用 Milvus 作为向量数据库 | Accepted | 2024-01-01 |

## 如何创建新 ADR

1. 复制模板: `cp template.md NNN-title.md`
2. 使用下一个可用编号
3. 填写决策内容
4. 提交 PR 进行评审
5. 评审通过后更新状态为 "Accepted"

## 命名规范

- 文件名格式: `NNN-kebab-case-title.md`
- 编号从 001 开始，递增
- 标题使用小写字母和连字符
