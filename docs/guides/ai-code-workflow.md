# AI Code 研发全流程指南

本文档定义了使用 AI 辅助工具（Claude Code / Gemini CLI）进行完整研发的标准流程。

## 流程概览

```text
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  1. 需求    │ → │  2. 设计    │ → │  3. TDD     │ → │  4. 质量    │ → │  5. 发布    │
│    分析     │   │    评审     │   │    开发     │   │    保障     │   │    上线     │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
```

> **重要**: 本项目采用 TDD（测试驱动开发）流程。所有新功能必须**先写测试，后写代码**。

---

## 阶段 1：需求分析

### 输入
- GitHub Issue 或口头需求

### 动作
```bash
# 使用 AI 分析需求
/analyze-issue [Issue 链接或描述]
```

### 输出
- 需求分析报告（功能边界、验收标准、复杂度评估）

### 检查点
- [ ] 需求边界清晰
- [ ] 验收标准可验证
- [ ] 复杂度已评估

---

## 阶段 2：设计评审

### 输入
- 需求分析报告

### 动作

**所有需求都需要设计说明**：

| 复杂度 | 设计要求 |
|--------|----------|
| 低     | 简化设计（在 PR 描述中说明方案） |
| 中     | 标准设计文档（`/design` 命令） |
| 高     | 完整设计文档 + ADR（如涉及架构变更） |

```bash
# 复杂度 >= 中：生成设计文档
/design [功能描述]

# 涉及架构变更：创建 ADR
# 手动创建 docs/design/adr/NNN-title.md
```

### 输出
- 低复杂度：PR 描述中的设计说明
- 中/高复杂度：`docs/design/[feature-name].md`
- 架构变更：`docs/design/adr/NNN-title.md`

### 检查点
- [ ] 设计方案合理
- [ ] 符合现有架构
- [ ] 人工确认设计

---

## 阶段 3：TDD 驱动的代码开发

### 输入
- 设计方案

### TDD 核心流程

```text
┌─────────────────────────────────────────────────────────────┐
│                    TDD 开发循环                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ 1. Red  │ -> │  测试   │ -> │ 2.Green │ -> │3.Refactor│  │
│  │ 写测试  │    │  失败   │    │  写代码  │    │  重构    │  │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘  │
│       ^                                              |       │
│       └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 动作

```bash
# 1. 创建分支
git checkout -b feat/xxx  # 或 fix/xxx

# 2. 生成测试骨架 (TDD 第一步)
/test [模块路径或功能描述]
# 示例: /test src/oceanus_agent/services/kafka_service.py
# 示例: /test 添加 Kafka 消费者健康检查

# 3. 完善测试用例
# 编写具体的测试断言，确保覆盖：
# - 正常路径 (happy path)
# - 边界条件 (edge cases)
# - 错误处理 (error handling)

# 4. 运行测试确认失败 (Red)
./.venv/bin/pytest tests/unit/xxx/test_xxx.py -v
# 预期: FAILED (因为功能尚未实现)

# 5. AI 辅助实现功能代码
# Claude Code 会自动遵循 CLAUDE.md 中的格式规范

# 6. 运行测试确认通过 (Green)
./.venv/bin/pytest tests/unit/xxx/test_xxx.py -v
# 预期: PASSED

# 7. 重构优化 (Refactor)
# 在测试保护下优化代码质量

# 8. 最终验证
./.venv/bin/pre-commit run --all-files
./.venv/bin/pytest tests/unit -v --cov=oceanus_agent --cov-fail-under=70
```

### AI 编码规范
- **测试先行**：必须先创建测试文件，再实现功能代码
- **必须先阅读**：修改前阅读目标文件和相关代码
- **遵循格式**：严格遵循 CLAUDE.md 中的格式规范
- **增量修改**：优先使用 Edit 而非 Write 重写

### 输出
- 测试文件（先于实现代码创建）
- 符合规范的实现代码
- 通过的测试套件

### TDD 检查点
- [ ] **测试先行**: 测试文件早于实现代码创建
- [ ] **测试命名**: 遵循 `test_<method>_<scenario>_<expected>()` 规范
- [ ] **测试覆盖**: 包含正常路径、边界条件、错误处理
- [ ] **Red 确认**: 测试在实现前确实失败
- [ ] **Green 确认**: 实现后所有测试通过
- [ ] **覆盖率达标**: 整体覆盖率 >= 70%（CI 强制），新代码推荐 >= 80%
- [ ] pre-commit 检查通过

---

## 阶段 4：质量保障

### 输入
- 完成的代码

### 动作

```bash
# 1. 创建 PR
git push -u origin feat/xxx
gh pr create --title "feat: xxx" --body "..."

# 2. 自检（可选）
/review --staged

# 3. 等待自动检查
# - CodeRabbit AI 审查
# - CI 流水线

# 4. 人工 Code Review
# - 响应审查意见
# - 修改代码
```

### 输出
- Approved PR
- CI 全部通过

### 检查点
- [ ] CI 流水线绿灯
- [ ] CodeRabbit 无严重问题
- [ ] 人工 Review 通过
- [ ] PR 描述清晰

---

## 阶段 5：发布上线

### 输入
- Approved PR

### 动作

```bash
# 1. 合并 PR
gh pr merge --squash

# 2. 自动触发
# - semantic-release 版本发布
# - Docker 镜像构建
# - K8s 部署（如配置）
```

### 输出
- 新版本发布
- 代码上线

### 检查点
- [ ] Release 成功
- [ ] 镜像构建成功
- [ ] 部署成功（如适用）
- [ ] 监控无异常

---

## 快速参考

### 常用命令

| 命令 | 用途 | 详细文档 |
|------|------|----------|
| `/analyze-issue` | 分析需求 | [命令说明](../../.claude/commands/analyze-issue.md) |
| `/design` | 生成设计文档 | [命令说明](../../.claude/commands/design.md) |
| `/test` | 生成测试骨架 (TDD) | [命令说明](../../.claude/commands/test.md) |
| `/review` | 代码审查 | [命令说明](../../.claude/commands/review.md) |
| `/diagnose` | 问题诊断 | [命令说明](../../.claude/commands/diagnose.md) |

> 命令完整索引和流程图请参考 [命令总览](../../.claude/commands/README.md)

### 分支命名

| 类型 | 前缀 | 示例 |
|------|------|------|
| 新功能 | `feat/` | `feat/add-kafka-consumer` |
| Bug 修复 | `fix/` | `fix/connection-timeout` |
| 重构 | `refactor/` | `refactor/llm-service` |
| 文档 | `docs/` | `docs/api-guide` |

### Commit 规范

```text
<type>(<scope>): <description>

feat(workflow): add retry mechanism for LLM calls
fix(services): handle connection timeout in MySQL
docs(api): update endpoint documentation
```

---

## 流程检查清单

完整开发一个功能时，确保完成以下步骤：

### 需求阶段
- [ ] 运行 `/analyze-issue` 分析需求
- [ ] 确认功能边界和验收标准
- [ ] 评估复杂度

### 设计阶段
- [ ] 低复杂度：准备 PR 描述中的设计说明
- [ ] 中/高复杂度：运行 `/design` 生成设计文档
- [ ] 架构变更：创建 ADR

### 开发阶段 (TDD)
- [ ] 创建 feature 分支
- [ ] 使用 `/test` 生成测试骨架
- [ ] 完善测试用例
- [ ] 运行测试确认失败 (Red)
- [ ] AI 辅助实现功能代码
- [ ] 运行测试确认通过 (Green)
- [ ] 重构优化 (Refactor)
- [ ] 运行 pre-commit 检查
- [ ] 运行完整测试套件

### 质量阶段
- [ ] 创建 PR
- [ ] 等待 CI 通过
- [ ] 响应 CodeRabbit 审查意见
- [ ] 获得人工 Review 批准

### 发布阶段
- [ ] 合并 PR
- [ ] 确认 Release 成功
- [ ] 验证部署（如适用）

---

## 相关文档

- [命令总览](../../.claude/commands/README.md) - 所有命令的详细说明和流程图
- [知识库说明](../../.claude/knowledge/README.md) - 项目知识库索引
- [TDD 开发指南](tdd.md) - 测试驱动开发详细指南
- [端到端示例](workflow-example.md) - 完整开发流程示例
- [分支保护规则](branch-protection.md) - GitHub 分支保护配置
