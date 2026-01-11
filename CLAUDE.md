# Claude Code 开发指南

本项目使用 Claude Code 进行开发，请遵循以下规范。

## 项目概述

Oceanus Agent 是一个基于 LLM 的 Flink 作业异常诊断系统。当 Flink 作业出现异常（Checkpoint失败、背压、反序列化报错等）时，自动诊断原因并给出修复建议。

## 技术栈

- **语言**: Python 3.11+
- **Agent框架**: LangGraph + LangSmith
- **LLM**: OpenAI GPT-4o-mini
- **向量数据库**: Milvus
- **关系型数据库**: MySQL
- **部署**: K8s + Docker

## 项目结构

```
.
├── src/oceanus_agent/      # 主代码目录
│   ├── config/             # 配置管理
│   ├── models/             # 数据模型
│   ├── services/           # 服务层（MySQL/Milvus/LLM）
│   └── workflow/           # LangGraph工作流
│       └── nodes/          # 工作流节点
├── tests/                  # 测试目录
├── deploy/                 # 部署配置
│   ├── docker/
│   └── k8s/
├── scripts/                # 初始化脚本
└── docs/                   # 文档目录
    ├── design/             # 设计文档
    ├── api/                # API文档
    └── guides/             # 开发指南
```

## 开发规范

### 代码风格
- 使用 ruff 进行代码检查
- 行宽限制 88 字符
- 使用 type hints
- 使用 structlog 进行日志记录

### 命名规范
- 类名: PascalCase
- 函数/变量: snake_case
- 常量: UPPER_SNAKE_CASE

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- refactor: 重构
- test: 测试相关

## 关键文件说明

| 文件 | 说明 | 修改频率 |
|------|------|----------|
| `workflow/graph.py` | LangGraph工作流核心 | 低 |
| `workflow/nodes/*.py` | 工作流节点实现 | 中 |
| `services/*.py` | 外部服务封装 | 中 |
| `config/prompts.py` | LLM Prompt模板 | 高 |
| `config/settings.py` | 配置项 | 低 |
| `models/state.py` | 状态定义 | 低 |

## 常用命令

```bash
# 本地运行
python -m oceanus_agent

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/

# Docker本地测试
cd deploy/docker && docker-compose up -d
```

## 开发任务参考

当需要进行以下开发时，参考相应文档：

- **添加新的异常类型支持**: 修改 `config/prompts.py` 和 `models/diagnosis.py`
- **优化诊断准确率**: 修改 `config/prompts.py` 中的 Prompt
- **添加新的知识来源**: 扩展 `services/milvus_service.py`
- **修改工作流逻辑**: 修改 `workflow/graph.py` 和相应节点
- **添加API接口**: 在 `src/oceanus_agent/` 下新建 `api/` 模块

## 文档索引

- [系统设计文档](docs/design/system-design.md)
- [数据库设计](docs/design/database-design.md)
- [工作流设计](docs/design/workflow-design.md)
- [开发指南](docs/guides/development.md)
- [部署指南](docs/guides/deployment.md)
