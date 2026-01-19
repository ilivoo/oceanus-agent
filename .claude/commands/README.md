# Claude 自定义命令指南

本目录包含 Oceanus Agent 项目的 Claude 自定义命令，用于支持 AI 驱动的标准化开发流程。

## 命令总览

| 命令 | 用途 | 触发时机 |
|------|------|----------|
| `/analyze-issue` | 分析需求，评估复杂度 | 收到新 Issue 或需求时 |
| `/design` | 生成设计文档 | 中/高复杂度功能开发前 |
| `/test` | 生成测试骨架 (TDD) | 设计完成后，编码前 |
| `/review` | 代码审查 | 提交 PR 前 |
| `/diagnose` | 问题诊断 | CI 失败或系统异常时 |

## 标准开发流程

```text
┌─────────────────────────────────────────────────────────────────┐
│                        标准开发流程                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  GitHub Issue                                                    │
│       │                                                          │
│       ▼                                                          │
│  /analyze-issue ─────────────────────────────────────┐          │
│       │                                              │          │
│       ├─ 低复杂度 ───────────────────────┐          │          │
│       │                                  │          │          │
│       └─ 中/高复杂度                      │          │          │
│              │                           │          │          │
│              ▼                           │          │          │
│         /design                          │          │          │
│              │                           │          │          │
│              ▼                           ▼          │          │
│          设计评审 ─────────────────► /test          │          │
│                                         │          │          │
│                                         ▼          │          │
│                                   TDD 循环          │          │
│                                   (Red-Green-      │          │
│                                    Refactor)       │          │
│                                         │          │          │
│                                         ▼          │          │
│                                    /review          │          │
│                                         │          │          │
│                                         ▼          │          │
│                                   git commit        │          │
│                                         │          │          │
│                                         ▼          │          │
│                                    创建 PR          │          │
│                                         │          │          │
│                                         ▼          │          │
│                                CI + CodeRabbit      │          │
│                                         │          │          │
│                     ┌───────────────────┴─────────┐│          │
│                     │                             ││          │
│                 通过 │                         失败 ││          │
│                     │                             ││          │
│                     ▼                             ▼│          │
│               人工 Review ◄───────────── /diagnose │          │
│                     │                              │          │
│                     ▼                              │          │
│               合并到 main                           │          │
│                                                    │          │
└────────────────────────────────────────────────────┴──────────┘
```

## 命令详解

### 1. /analyze-issue - 需求分析

**作用**: 分析 Issue 或需求描述，输出结构化的需求分析报告。

**使用方式**:
```bash
/analyze-issue [Issue 链接或需求描述]
```

**输出内容**:
- 需求概述和功能边界
- 验收标准
- 复杂度评估（低/中/高）
- 技术要点和风险识别
- 下一步建议（是否需要设计文档、ADR、分支名）

**复杂度判定**:

| 复杂度 | 代码行数 | 后续动作 |
|--------|----------|----------|
| 低 | < 50 行 | 直接 → `/test` |
| 中 | 50-200 行 | 推荐 → `/design` |
| 高 | > 200 行 | 必须 → `/design` + ADR（如涉及架构） |

---

### 2. /design - 设计文档生成

**作用**: 为中/高复杂度功能生成设计文档。

**使用方式**:
```bash
/design [功能描述]
```

**输出位置**: `docs/design/[feature-name].md`

**设计文档包含**:
- 功能概述
- 架构图（ASCII 或 Mermaid）
- Pydantic 数据模型定义
- API 设计（如适用）
- 测试策略
- 影响评估

---

### 3. /test - 测试骨架生成 (TDD)

**作用**: 支持测试驱动开发，生成测试骨架。

**使用方式**:
```bash
/test [目标]                     # 默认单元测试
/test [目标] --type=unit        # 单元测试
/test [目标] --type=integration # 集成测试
/test [目标] --type=bug         # Bug 修复测试
```

**目标类型**:
- 模块路径: `src/oceanus_agent/services/xxx.py`
- 功能描述: `添加 Kafka 消费者健康检查`

**TDD 工作流**:

```text
1. /test [功能]          → 生成测试骨架
2. 完善测试用例           → 编写断言
3. pytest tests/...      → Red (失败)
4. 实现功能代码           → 让测试通过
5. pytest tests/...      → Green (通过)
6. 重构优化              → Refactor
```

---

### 4. /review - 代码审查

**作用**: 在 PR 前进行代码自检。

**使用方式**:
```bash
/review                    # 审查 staged 变更
/review [file_path]        # 审查指定文件
/review --staged           # 审查 staged 变更
/review --last-commit      # 审查最后一次 commit
```

**审查维度**:
- 代码质量（命名、类型、错误处理）
- 异步安全（await、连接管理）
- 测试覆盖（是否有对应测试）
- 安全检查（敏感信息、SQL 注入）

---

### 5. /diagnose - 问题诊断

**作用**: 诊断代码问题或系统故障。

**使用方式**:
```bash
/diagnose [错误信息或问题描述]
```

**使用场景**:
- CI 检查失败
- 运行时异常
- 性能问题
- 配置错误

**输出内容**:
- 根因分析
- 涉及文件定位
- 修复建议
- 预防措施

---

## CI 检查与命令映射

当 CI 检查失败时，可使用对应命令进行诊断和修复：

| CI 检查 | 对应命令 | 修复操作 |
|---------|----------|----------|
| `Code Quality (pre-commit)` | `/review` | `.venv/bin/ruff format && .venv/bin/ruff check --fix` |
| `Unit Tests` | `/test` | `.venv/bin/pytest` 修复测试用例 |
| `Security Scan` | `/diagnose` | 修复安全问题 |
| `Build Docker Image` | `/diagnose` | 检查 Dockerfile |

---

## 关联知识库

命令执行时会参考以下知识库：

| 知识库 | 用途 | 关联命令 |
|--------|------|----------|
| [architecture.md](../knowledge/architecture.md) | 系统架构 | `/analyze-issue`, `/design` |
| [patterns.md](../knowledge/patterns.md) | 代码模式 | `/design`, `/test`, `/review` |
| [conventions.md](../knowledge/conventions.md) | 项目约定 | 全部命令 |
| [troubleshooting.md](../knowledge/troubleshooting.md) | 故障排除 | `/diagnose` |

---

## 快速参考卡片

### 新功能开发
```bash
# 1. 分析需求
/analyze-issue 添加 Kafka 消费者服务

# 2. 生成设计（中/高复杂度）
/design 添加 Kafka 消费者服务

# 3. 生成测试骨架
/test src/oceanus_agent/services/kafka_service.py

# 4. TDD 循环：完善测试 → 实现代码 → 重构

# 5. 代码审查
/review --staged

# 6. 提交并创建 PR
git commit -m "feat(services): add Kafka consumer service"
```

### Bug 修复
```bash
# 1. 分析问题
/analyze-issue fix: MySQL 连接超时 #123

# 2. 生成回归测试
/test fix: MySQL 连接超时 --type=bug

# 3. TDD 循环

# 4. 审查并提交
/review --staged
git commit -m "fix(services): resolve MySQL connection timeout"
```

### CI 失败修复
```bash
# 诊断问题
/diagnose "TypeError: unsupported operand type(s)..."

# 根据建议修复
# ...

# 重新审查
/review --staged
```

---

## 相关文档

- [AI Code 研发全流程指南](../../docs/guides/ai-code-workflow.md)
- [TDD 测试驱动开发指南](../../docs/guides/tdd.md)
- [开发指南](../../docs/guides/development.md)
- [知识库说明](../knowledge/README.md)
