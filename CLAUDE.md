# Oceanus Agent 项目开发指南

**Oceanus Agent** 是一个基于大语言模型（LLM）的 Flink 作业异常诊断智能系统。它通过自动化分析作业失败信息、检索历史案例和知识库，提供精准的根因分析和修复建议，并能通过自学习机制不断积累诊断知识。

## 1. 项目概览

- **核心目标**: 自动化诊断 Flink 作业异常（如 Checkpoint 失败、反序列化错误、资源不足等）并提供修复方案。
- **核心逻辑**: 使用 `LangGraph` 编排循环诊断工作流，包含状态管理和持久化。
- **关键特性**:
    - **RAG 增强诊断**: 利用 Milvus 检索相似历史案例和技术文档，提供上下文感知的分析。
    - **知识库自进化**: 高置信度的诊断结果会自动向量化并回流至 Milvus 知识库。
    - **健壮的工作流**: 内置重试机制、错误处理和状态断点保存。
    - **结构化输出**: 提供标准化的诊断报告，包含根因、分析详情和可执行的修复步骤。

## 2. 技术栈

| 领域 | 技术选型 | 说明 |
| :--- | :--- | :--- |
| **语言** | Python 3.11+ | 核心开发语言 |
| **Agent 框架** | LangGraph, LangSmith | 工作流编排与追踪 |
| **LLM 集成** | LangChain, OpenAI GPT-4o-mini | 模型调用与 Embedding |
| **向量数据库** | Milvus (pymilvus) | 存储案例与文档向量 |
| **关系型数据库** | MySQL (Async SQLAlchemy + aiomysql) | 存储任务状态与结果 |
| **Web 框架** | FastAPI, Uvicorn | 提供 API 服务 |
| **配置管理** | Pydantic Settings | 强类型的环境变量管理 |
| **基础设施** | Docker, Kubernetes | 容器化部署 |

## 3. 项目结构

```text
/home/debian/project/oceanus-agent/
├── src/
│   └── oceanus_agent/
│       ├── api/                # FastAPI 路由与应用入口
│       ├── config/             # 配置中心
│       │   ├── settings.py     # Pydantic 配置定义
│       │   └── prompts.py      # LLM 提示词模板
│       ├── models/             # Pydantic 数据模型
│       │   ├── diagnosis.py    # 诊断结果模型
│       │   ├── state.py        # 工作流状态定义
│       │   └── knowledge.py    # 知识库实体
│       ├── services/           # 外部服务集成层
│       │   ├── llm_service.py  # OpenAI 接口封装
│       │   ├── milvus_service.py # 向量检索服务
│       │   ├── mysql_service.py  # 数据库操作服务
│       └── workflow/           # LangGraph 工作流定义
│           ├── graph.py        # 图构建与路由逻辑
│           └── nodes/          # 工作流节点实现
│               ├── collector.py    # 异常采集
│               ├── retriever.py    # RAG 检索
│               ├── diagnoser.py    # LLM 诊断
│               ├── storer.py       # 结果存储
│               └── accumulator.py  # 知识积累
├── deploy/                     # 部署配置 (Docker/K8s)
├── docs/                       # 项目文档 (设计/API/指南)
├── scripts/                    # 数据库初始化与调试脚本
├── tests/                      # 测试套件 (Unit/Integration/E2E)
├── .env.example                # 环境变量模版
├── pyproject.toml              # 项目依赖与工具配置
├── CLAUDE.md                   # Claude 开发辅助文档
└── GEMINI.md                   # Gemini 项目背景文档
```

## 4. 工作流架构

诊断过程被建模为一个状态图（State Graph），包含以下节点：

1.  **Collect (采集)**: 从 MySQL 拉取待处理的作业异常。
    *   *流向*: 成功 -> `Retrieve`; 无任务 -> `END`
2.  **Retrieve (检索)**: 基于错误信息，从 Milvus 检索相似案例和文档。
    *   *流向*: -> `Diagnose`
3.  **Diagnose (诊断)**: 调用 LLM (GPT-4o-mini) 结合上下文进行分析。
    *   *重试策略*: 遇到临时错误最多重试 3 次。
    *   *流向*: 成功 -> `Store`; 失败 -> `Handle Error`
4.  **Store (存储)**: 将结构化的诊断结果存入 MySQL。
    *   *流向*: -> `Accumulate`
5.  **Accumulate (积累)**: 若诊断置信度 > 0.8，将结果向量化存入 Milvus。
    *   *流向*: -> `END`
6.  **Handle Error (错误处理)**: 捕获工作流异常并更新作业状态为失败。

## 5. 开发规范与 Agent 准则

**针对 AI 助手 (Claude/Gemini) 与开发者的核心准则：**

### 环境与执行
*   **虚拟环境**: 必须使用 `.venv/` 目录下的环境。
    *   Python: `./.venv/bin/python`
    *   工具链: `./.venv/bin/ruff`, `./.venv/bin/mypy`, `./.venv/bin/pytest`
*   **依赖管理**: 所有依赖定义在 `pyproject.toml`，严禁假设全局包存在。

### 代码格式化 (强制要求)

> **关键规则**: 任何代码修改后，必须在提交前运行格式化检查。不遵守此规则的代码将被 CI 拒绝。

**工作流程**:

1. **编写/修改代码**
2. **格式化代码** (在提交前):
   ```bash
   ./.venv/bin/ruff format src/ tests/
   ./.venv/bin/ruff check --fix src/ tests/
   ```
3. **运行完整检查**:
   ```bash
   ./.venv/bin/pre-commit run --all-files
   ```
4. **确认所有检查通过后**，再进行 git commit

**禁止行为**:
- 不运行 pre-commit 就声称任务完成
- 使用 `--no-verify` 跳过检查
- 忽略 ruff/mypy 的警告或错误

**格式化标准**:
- 行长度: 88 字符
- 缩进: 4 空格 (Python)
- 引号: 双引号
- Import 排序: isort 规则 (由 ruff 管理)

### 代码风格
*   **数据模型**: **强制使用 Pydantic v2**。所有配置、API 交互、内部数据流转必须使用 Pydantic Model，禁止使用裸字典。
*   **数据库交互**: 必须使用 `sqlalchemy.ext.asyncio` 配合 `aiomysql` 进行全异步操作。
*   **类型安全**: 所有函数必须包含 Type Hints (类型提示)，并通过 `mypy` 检查。
*   **日志**: 使用 `structlog` 进行结构化日志记录。

### 命名规范
*   **类名**: `PascalCase`
*   **函数/变量**: `snake_case`
*   **常量**: `UPPER_SNAKE_CASE`

### 测试规范
*   **单元测试**: 位于 `tests/unit/`，不得依赖外部服务，使用 `unittest.mock` 进行模拟。
*   **集成测试**: 位于 `tests/integration/`，依赖 Docker 环境 (MySQL/Milvus)。

## 6. 常用命令

```bash
# 1. 环境配置 (首次运行)
cp .env.example .env  # 并填入 API Key 和数据库配置
pip install -e ".[dev]"

# 2. 启动基础设施 (Docker)
cd deploy/docker && docker compose up -d

# 3. 初始化数据库
# MySQL
mysql -h 127.0.0.1 -P 3306 -u root -p oceanus_agent < scripts/init_db.sql
# Milvus
python scripts/init_milvus.py

# 4. 运行 Agent
python -m oceanus_agent

# 5. 代码质量检查
pre-commit run --all-files  # 运行所有检查 (推荐)
ruff check src/             # 仅 Linting
mypy src/                   # 仅 Type Checking

# 6. 运行测试
pytest tests/ -v
```

## 7. 维护与扩展指南

| 任务类型 | 相关文件/路径 |
| :--- | :--- |
| **修改 Prompt** | `src/oceanus_agent/config/prompts.py` |
| **新增异常类型** | `src/oceanus_agent/models/diagnosis.py` |
| **调整工作流逻辑** | `src/oceanus_agent/workflow/graph.py` |
| **添加新的知识源** | `src/oceanus_agent/services/milvus_service.py` |
| **API 接口开发** | `src/oceanus_agent/api/` |

## 8. 研发流程与 GitHub 集成

本项目遵循标准的 GitHub Flow 研发流程，并集成了 GitHub Actions 进行自动化检查。

### 分支管理
- **main**: 主分支，保持随时可部署状态，受保护分支。
- **feat/***: 新功能开发分支 (e.g., `feat/add-milvus-retriever`)。
- **fix/***: Bug 修复分支 (e.g., `fix/connection-timeout`)。
- **refactor/***: 代码重构分支。

### 贡献指南
1.  **Issue**: 提交 Issue 描述 Bug 或新功能（建议使用 `.github/ISSUE_TEMPLATE`）。
2.  **Branch**: 从 `main` 切出开发分支。
3.  **Commit**: 遵循 Conventional Commits 规范 (e.g., `feat: implement ragnarok module`)。
4.  **Pull Request**: 提交 PR 到 `main`。
    - 必须填写 PR 描述（系统会自动加载 `.github/PULL_REQUEST_TEMPLATE.md`）。
    - 必须通过 CI 检查 (Lint, Type Check, Tests)。
    - 必须经过至少一次 Code Review。

### CI/CD 集成 (.github/workflows)
- **CI (`ci.yml`)**: 每次 Push 或 PR 时自动触发。
    - 运行 `ruff` 代码风格检查。
    - 运行 `mypy` 类型检查。
    - 运行 `pytest` 单元测试。
- **Release (`semantic-release.yml`)**: 每月基于 Conventional Commits 自动发布版本 (Tag, Release, Changelog)。
- **Docker (`release.yml`)**: 自动检测到 Release 发布后，构建并推送 Docker 镜像。
- **Dependabot**: 自动检测并更新依赖 (`.github/dependabot.yml`)。

## 9. AI 驱动开发流程

本项目采用 AI 驱动的文档驱动开发 (AI-DDD) 流程，以下是 AI 助手参与开发的标准流程。

### 9.1 Issue 处理流程

```text
新 Issue 创建
    |
    v
+------------------+
| AI 自动分析       | <- 解析 Issue 内容，评估复杂度
+--------+---------+
         |
         v
    +------------+
    | 需要设计？  |
    +-----+------+
          |
    +-----+-----+
    |           |
    v Yes       v No
生成设计文档   直接实现
    |           |
    v           |
设计评审 <------+
    |
    v
代码实现
    |
    v
AI Code Review (CodeRabbit)
    |
    v
人工最终确认
    |
    v
合并到 main
```

### 9.2 设计文档要求

对于中等以上复杂度的功能，必须先创建设计文档:

| 复杂度 | 代码行数估计 | 是否需要设计文档 |
|--------|--------------|------------------|
| 低     | < 50 行      | 否 |
| 中     | 50-200 行    | 推荐 |
| 高     | > 200 行     | 必须 |

**设计文档位置**: `docs/design/[feature-name].md`
**设计模板**: `docs/templates/design-template.md`

### 9.3 架构决策记录 (ADR)

涉及以下情况时，必须创建 ADR:

- 引入新的核心依赖
- 变更系统架构
- 重大技术选型
- 打破现有约定

**ADR 位置**: `docs/design/adr/NNN-title.md`
**ADR 模板**: `docs/design/adr/template.md`

### 9.4 Claude 自定义命令

项目提供以下自定义命令加速开发:

| 命令 | 说明 | 示例 |
|------|------|------|
| `/design` | 生成设计文档 | `/design 添加 Kafka 消息消费` |
| `/review` | 代码审查 | `/review --staged` |
| `/diagnose` | 问题诊断 | `/diagnose MySQL 连接超时` |

命令定义位于 `.claude/commands/`。

### 9.5 知识库结构

```text
.claude/
├── commands/           # 自定义命令
├── knowledge/          # 项目知识库
|   ├── architecture.md # 架构知识
|   ├── patterns.md     # 代码模式
|   ├── troubleshooting.md # 故障排除
|   └── conventions.md  # 约定规范
└── memory/             # 项目记忆
    └── decisions.md    # 历史决策
```

**重要**: 在进行开发前，请阅读 `.claude/knowledge/` 中的相关文档。

---

## 10. Code Review 集成

### 10.1 CodeRabbit 自动审查

本项目集成 CodeRabbit 进行自动化代码审查。配置文件: `.coderabbit.yaml`

**审查重点**:

- 代码质量和最佳实践
- 安全漏洞检测
- 性能问题识别
- 文档完整性

**与 CodeRabbit 交互**:

```text
# 在 PR 评论中
@coderabbitai review          # 请求审查
@coderabbitai summary         # 生成变更摘要
@coderabbitai resolve         # 标记问题已解决
```

### 10.2 人工审查清单

即使 AI 审查通过，人工审查仍需检查:

- [ ] 设计是否符合项目架构
- [ ] 是否有潜在的安全风险
- [ ] 是否影响系统稳定性
- [ ] 是否需要更新文档

---

## 11. PR 自动化

### 11.1 自动生成的内容

PR 创建时会自动添加:

- 变更统计 (文件数、代码行数)
- Commit 列表
- 变更文件分类

### 11.2 自动标签

基于变更文件自动添加标签:

| 路径模式 | 标签 |
|----------|------|
| `workflow/**` | `area/workflow` |
| `services/**` | `area/services` |
| `api/**` | `area/api` |
| `tests/**` | `area/tests` |
| `**/*.md` | `type/documentation` |

配置文件: `.github/labeler.yml`
