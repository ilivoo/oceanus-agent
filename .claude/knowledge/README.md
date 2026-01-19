# Claude 知识库说明

本目录包含 Oceanus Agent 项目的知识库文件，供 Claude AI 助手在开发过程中参考。

## 知识库文件

| 文件 | 用途 | 主要内容 |
|------|------|----------|
| [architecture.md](architecture.md) | 系统架构 | 层次结构、数据流、设计决策、扩展点 |
| [patterns.md](patterns.md) | 代码模式 | 常用代码模式、异步模式、错误处理模式 |
| [conventions.md](conventions.md) | 项目约定 | 命名规范、Git 规范、测试约定、文档约定 |
| [troubleshooting.md](troubleshooting.md) | 故障排除 | 常见问题、解决方案、诊断步骤 |

## 使用场景映射

### 按开发阶段

| 阶段 | 推荐阅读 | 说明 |
|------|----------|------|
| 需求分析 | `architecture.md` | 了解系统结构，评估影响范围 |
| 设计阶段 | `architecture.md`, `patterns.md` | 参考现有架构和代码模式 |
| 编码阶段 | `conventions.md`, `patterns.md` | 遵循命名规范和代码模式 |
| 测试阶段 | `conventions.md` (第 118-159 行) | 测试命名和 Mock 约定 |
| 故障排除 | `troubleshooting.md` | 快速定位常见问题 |

### 按命令关联

| 命令 | 关联知识库 | 用途 |
|------|-----------|------|
| `/analyze-issue` | `architecture.md`, `patterns.md` | 评估技术方案和影响范围 |
| `/design` | `architecture.md`, `patterns.md` | 参考架构设计和代码模式 |
| `/test` | `conventions.md` | 测试命名规范和 Mock 约定 |
| `/review` | `conventions.md`, `patterns.md` | 代码风格和最佳实践检查 |
| `/diagnose` | `troubleshooting.md` | 故障诊断和解决方案 |

## 文件详解

### architecture.md - 系统架构

**核心内容**:
- **三层架构**: API Layer → Workflow Layer → Service Layer
- **数据流**: Flink → MySQL → Agent → Milvus/LLM → MySQL
- **设计决策**: 为什么选择 LangGraph、Milvus、异步优先
- **扩展点**: 新增节点、Provider、知识源、API 的方法

**适用场景**:
- 评估新功能对现有架构的影响
- 设计新模块时参考层次结构
- 了解系统数据流和依赖关系

### patterns.md - 代码模式

**核心内容**:
- **服务层模式**: 异步初始化、连接管理、重试策略
- **工作流模式**: 节点定义、状态传递、条件路由
- **数据模式**: Pydantic 模型定义、验证规则

**适用场景**:
- 实现新服务时参考现有模式
- 编写工作流节点时参考结构
- 定义数据模型时参考风格

### conventions.md - 项目约定

**核心内容**:
- **命名规范** (第 1-50 行): 类名、函数、变量、文件命名
- **Git 规范** (第 51-117 行): Commit Message、分支管理
- **测试约定** (第 118-159 行): 测试命名、Mock 使用
- **文档约定** (第 160-198 行): Docstring 格式、TODO 格式
- **错误处理** (第 199-223 行): 异常层次、处理原则

**适用场景**:
- 编写代码时遵循命名规范
- 提交代码时遵循 Commit 规范
- 编写测试时遵循测试约定

### troubleshooting.md - 故障排除

**核心内容**:
- **数据库问题**: MySQL 连接、Milvus 集合、事务死锁
- **LLM 问题**: API 限流、Token 超限、响应解析
- **工作流问题**: 状态不一致、节点重试、无限循环

**适用场景**:
- CI 检查失败时快速定位
- 运行时异常诊断
- 生产环境问题排查

## 知识库维护指南

### 更新原则

1. **及时性**: 架构变更后立即更新 `architecture.md`
2. **完整性**: 新增代码模式后补充 `patterns.md`
3. **准确性**: 发现新问题后补充 `troubleshooting.md`

### 更新流程

1. 在相应知识库文件中添加内容
2. 遵循现有格式和风格
3. 在 PR 描述中说明知识库更新

### 版本追踪

知识库的重大更新应在 PR 描述或 Commit Message 中标注：

```text
docs(knowledge): update architecture.md with new retriever pattern
```

## 相关文档

- [Claude 命令指南](../commands/README.md)
- [AI Code 研发全流程](../../docs/guides/ai-code-workflow.md)
- [TDD 开发指南](../../docs/guides/tdd.md)
