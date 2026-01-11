# Oceanus Agent

基于 LLM 的 Flink 作业异常智能诊断系统。

## 功能特性

- **自动诊断**: 当 Flink 作业出现异常时，自动分析原因并给出修复建议
- **知识积累**: 高置信度诊断自动加入知识库，持续学习
- **RAG 增强**: 结合历史案例和 Flink 文档提升诊断准确率
- **结构化输出**: 诊断结果包含根因分析、修复步骤、优先级等

## 支持的异常类型

- Checkpoint 失败
- 背压问题
- 反序列化错误
- OOM 问题
- 网络问题

## 快速开始

### 1. 配置环境

```bash
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY 等配置
```

### 2. 启动依赖服务

```bash
cd deploy/docker
docker compose up -d mysql milvus etcd minio
```

### 3. 初始化数据库

```bash
mysql -h localhost -u oceanus -p oceanus_agent < scripts/init_db.sql
python scripts/init_milvus.py
```

### 4. 运行 Agent

```bash
python -m oceanus_agent
```

## 技术栈

- **语言**: Python 3.11+
- **Agent 框架**: LangGraph + LangSmith
- **LLM**: OpenAI GPT-4o-mini
- **向量数据库**: Milvus
- **关系型数据库**: MySQL
- **部署**: K8s + Docker

## 文档

- [系统设计](docs/design/system-design.md)
- [数据库设计](docs/design/database-design.md)
- [工作流设计](docs/design/workflow-design.md)
- [开发指南](docs/guides/development.md)
- [部署指南](docs/guides/deployment.md)

## 项目结构

```
.
├── src/oceanus_agent/      # 源代码
│   ├── config/             # 配置管理
│   ├── models/             # 数据模型
│   ├── services/           # 服务层
│   └── workflow/           # LangGraph 工作流
├── tests/                  # 测试
├── deploy/                 # 部署配置
├── scripts/                # 初始化脚本
└── docs/                   # 文档
```

## License

MIT
