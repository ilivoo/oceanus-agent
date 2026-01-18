# AI 编程与 GitHub 集成指南

> 本文档记录了 oceanus-agent 项目的 AI 编程工具链与 GitHub 集成现状，供开发者参考。
>
> 最后更新：2026-01-18

## 总体评估

**当前状态**：项目已经具备了 **非常完善** 的 AI 编程和 GitHub 集成基础设施。

> [!TIP]
> 项目在 AI 辅助开发方面的准备程度已经达到了 **专业级水平**，覆盖了开发、审查、发布全流程。

---

## 已完成部分

### 1. AI 助手配置（Claude & Gemini）

| 配置项 | 状态 | 文件路径 |
|--------|------|----------|
| Claude 全局配置 | ✅ | `CLAUDE.md` |
| Gemini 全局配置 | ✅ | `GEMINI.md` |
| Claude 自定义命令 | ✅ | `.claude/commands/` |
| Claude 知识库 | ✅ | `.claude/knowledge/` |

**亮点**：
- 详尽的开发规范文档，AI 可直接遵循
- 自定义命令（`/design`, `/review`, `/diagnose`）加速开发
- 完整的知识库（架构、模式、约定、故障排除）

---

### 2. GitHub CI/CD 流水线

| 工作流 | 功能 | 状态 |
|--------|------|------|
| `ci.yml` | 代码质量、单元测试、安全扫描、Docker 构建 | ✅ |
| `release.yml` | Release 发布后构建 Docker 镜像 + 更新 K8s 配置 | ✅ |
| `semantic-release.yml` | 基于 Conventional Commits 自动版本发布 | ✅ |
| `codeql.yml` | 代码安全扫描（每周定时） | ✅ |
| `stale.yml` | 自动清理过期 Issue/PR | ✅ |
| `labeler.yml` | 自动标签 PR | ✅ |
| `pr-auto-describe.yml` | PR 创建时自动生成变更统计 | ✅ |

---

### 3. 代码审查与自动化

| 组件 | 功能 | 状态 |
|------|------|------|
| CodeRabbit | AI 代码审查（中文输出、路径级审查规则） | ✅ |
| CODEOWNERS | 代码变更自动指派审查者 | ✅ |
| PR 模板 | 标准化 PR 描述与检查清单 | ✅ |
| labeler.yml | 基于变更文件自动打标签 | ✅ |

**CodeRabbit 配置亮点**：
- 按路径定制审查重点（workflow、services、api、models 等）
- 自动审查、知识库集成
- 使用中文进行审查

---

### 4. Issue 与 PR 管理

| 组件 | 功能 | 状态 |
|------|------|------|
| Bug 报告模板 | 结构化缺陷报告，含 AI 元数据区 | ✅ |
| 功能请求模板 | 详尽的需求模板，含设计文档要求 | ✅ |
| Stale Bot | 自动关闭过期 Issue/PR | ✅ |

**Issue 模板亮点**：
- 包含 AI 处理元数据区（供未来 AI Agent 自动处理）
- 详尽的结构化字段
- 内置验收标准模板（Given-When-Then）

---

### 5. 依赖与安全管理

| 组件 | 功能 | 状态 |
|------|------|------|
| Dependabot | 自动检测依赖更新（pip、GitHub Actions、Docker） | ✅ |
| Bandit | 安全漏洞扫描 | ✅ |
| CodeQL | GitHub 代码扫描 | ✅ |

---

### 6. 代码质量工具链

| 工具 | 功能 | 配置状态 |
|------|------|----------|
| Pre-commit | 提交前自动检查 | ✅ 已配置 |
| Ruff | Python linter + formatter | ✅ 已配置 |
| MyPy | 类型检查 | ✅ 已配置 |
| Conventional Commits | 规范化提交消息 | ✅ 已配置 |
| pytest + coverage | 测试与覆盖率 | ✅ 已配置 |
| Codecov | 覆盖率上报 | ✅ 已配置 |

---

### 7. 文档体系

| 文档类型 | 位置 | 状态 |
|----------|------|------|
| 设计文档 | `docs/design/` | ✅ |
| ADR（架构决策记录） | `docs/design/adr/` | ✅ |
| 开发指南 | `docs/guides/` | ✅ |
| 设计模板 | `docs/templates/` | ✅ |
| 贡献指南 | `CONTRIBUTING.md` | ✅ |
| 安全策略 | `SECURITY.md` | ✅ |
| 行为准则 | `CODE_OF_CONDUCT.md` | ✅ |
| 变更日志 | `CHANGELOG.md` | ✅ |

---

## 可改进 / 缺失部分

### 1. GitHub 仓库设置（需手动配置）

以下需要在 GitHub 仓库 **Settings** 中手动配置：

| 设置项 | 说明 | 状态 |
|--------|------|------|
| Branch Protection Rules | 保护 `main` 分支，强制 PR、CI 通过、Code Review | ✅ [配置指南](./branch-protection.md) |
| Secrets 配置 | `CODECOV_TOKEN` 等密钥 | ⚠️ 需确认 |
| GitHub Pages | 如需发布文档站点 | ❌ 未配置 |
| Environments | 配置 staging/production 环境保护 | ❌ 未配置 |

> [!IMPORTANT]
> 建议在 GitHub 仓库设置中配置 **Branch Protection Rules**，强制 PR 必须通过 CI 并获得 Code Review 后才能合并。

---

### 2. AI Agent 自动化处理 Issue/PR（进阶）

当前的 Issue 模板包含 AI 元数据区，但尚未实现：

| 功能 | 说明 | 状态 |
|------|------|------|
| Issue 自动分析 | AI 自动分析新 Issue 并分类 | ❌ 未实现 |
| 自动生成设计文档 | 根据 Feature Request 自动生成初稿 | ❌ 未实现 |
| PR 自动代码实现 | AI 自动根据 Issue 创建 PR | ❌ 未实现 |

> [!NOTE]
> 这些功能属于"AI Agent 自动化"范畴，可通过 GitHub Actions + OpenAI API 或第三方服务（如 Sweep、Devin）实现。

---

### 3. 缺少的可选配置

| 组件 | 说明 | 优先级 |
|------|------|--------|
| GitHub Projects | 可视化项目管理看板 | 中 |
| Discussions | 开放社区讨论 | 低 |
| Wiki | 项目 Wiki 文档 | 低（已有 docs/） |
| ~~GitHub Copilot 配置~~ | ~~`.github/copilot-instructions.md`~~ | ✅ 已完成 |

---

## AI 编程就绪度评分

| 维度 | 评分 | 满分 |
|------|------|------|
| CI/CD 自动化 | 10 | 10 |
| 代码质量工具 | 10 | 10 |
| AI 助手配置 | 10 | 10 |
| 代码审查自动化 | 10 | 10 |
| Issue/PR 管理 | 9 | 10 |
| 依赖安全管理 | 10 | 10 |
| 文档体系 | 10 | 10 |
| AI Agent 自动化 | 5 | 10 |
| **总分** | **84** | **90** |

---

## 推荐的下一步行动

### 优先级高

1. **确认 GitHub 仓库设置**
   - ~~配置 Branch Protection Rules~~ ✅ 已完成，参见 [配置指南](./branch-protection.md)
   - 验证 Secrets（`CODECOV_TOKEN` 等）

2. ~~**添加 GitHub Copilot 配置**~~ ✅ 已完成
   - 配置文件：`.github/copilot-instructions.md`
   - 包含：项目概览、技术栈、代码风格、命名规范、常用模式等

### 优先级中

3. **启用 GitHub Environments** - [配置指南](#github-environments-配置指南)
   - 配置 `staging` 和 `production` 环境
   - 添加环境保护规则（需审批才能部署）

4. **考虑 AI Agent 自动化**
   - 使用 GitHub Actions + OpenAI API 自动分析 Issue
   - 或集成 Sweep、Devin 等 AI 代码助手

### 优先级低

5. **启用 GitHub Discussions**（如需开放社区交流）
6. **配置 GitHub Pages**（如需发布文档站点）

---

## 总结

项目在 AI 编程集成方面已经做得非常完善，几乎覆盖了专业级开发团队的所有最佳实践。主要的改进空间在于：

1. **GitHub 仓库级别的设置**（Environments、Secrets 验证）
2. **进阶的 AI Agent 自动化**（自动处理 Issue、生成 PR）

当前的配置已经足以支撑高效的 AI 辅助开发流程！

---

## 附录

### GitHub Environments 配置指南

GitHub Environments 允许你为不同的部署目标（如 staging、production）配置保护规则和密钥。

#### 配置步骤

1. **进入仓库设置**
   - 打开 GitHub 仓库页面
   - 点击 **Settings** → **Environments**

2. **创建 Staging 环境**
   ```
   名称: staging
   保护规则:
   - ✅ Required reviewers: 0（可选，staging 通常不需要审批）
   - ✅ Wait timer: 0 分钟
   ```

3. **创建 Production 环境**
   ```
   名称: production
   保护规则:
   - ✅ Required reviewers: 1（至少 1 人审批）
   - ✅ Wait timer: 5 分钟（可选，给予取消时间）
   - ✅ Deployment branches: 仅限 main 分支
   ```

4. **配置环境密钥**（可选）
   每个环境可以有独立的 Secrets：
   ```
   staging:
   - KUBECONFIG_STAGING
   - API_ENDPOINT_STAGING

   production:
   - KUBECONFIG_PRODUCTION
   - API_ENDPOINT_PRODUCTION
   ```

#### 在 Workflow 中使用

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging  # 使用 staging 环境
    steps:
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging..."

  deploy-production:
    runs-on: ubuntu-latest
    environment: production  # 使用 production 环境（需审批）
    needs: deploy-staging
    steps:
      - name: Deploy to Production
        run: |
          echo "Deploying to production..."
```

#### 推荐的环境配置

| 环境 | 审批要求 | 分支限制 | 等待时间 |
|------|----------|----------|----------|
| `staging` | 无 | 无 | 0 分钟 |
| `production` | 1 人 | 仅 `main` | 5 分钟 |

---

### Secrets 配置检查清单

以下是项目可能需要的 GitHub Secrets：

| Secret 名称 | 用途 | 必需 | 配置位置 |
|-------------|------|------|----------|
| `CODECOV_TOKEN` | 代码覆盖率上报 | 推荐 | Repository secrets |
| `DOCKER_USERNAME` | Docker Hub 登录 | 是 | Repository secrets |
| `DOCKER_PASSWORD` | Docker Hub 密码 | 是 | Repository secrets |
| `OPENAI_API_KEY` | LLM API 调用（仅测试） | 可选 | Repository secrets |
| `KUBECONFIG` | K8s 部署配置 | 部署时需要 | Environment secrets |

#### 配置步骤

1. **进入仓库设置**
   - 打开 GitHub 仓库页面
   - 点击 **Settings** → **Secrets and variables** → **Actions**

2. **添加 Repository secrets**
   - 点击 **New repository secret**
   - 输入名称和值

3. **验证 Secrets 是否生效**
   ```yaml
   # 在 workflow 中检查 secret 是否存在
   - name: Check secrets
     run: |
       if [ -z "${{ secrets.CODECOV_TOKEN }}" ]; then
         echo "Warning: CODECOV_TOKEN not configured"
       fi
   ```

> [!CAUTION]
> 永远不要在日志中打印 Secret 的实际值！
