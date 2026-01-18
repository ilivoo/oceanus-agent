# GitHub 集成增强设计文档

| 属性 | 值 |
|------|-----|
| **文档状态** | Draft |
| **作者** | @ilivoo |
| **创建日期** | 2026-01-17 |
| **更新日期** | 2026-01-17 |
| **关联 Issue** | - |
| **审阅者** | - |

---

## 1. 概述 (Overview)

### 1.1 背景

项目已采用 ALL IN AI 开发模式，当前已有以下 GitHub 集成：

**已有配置:**
- CI/CD 工作流 (ci.yml, semantic-release.yml, release.yml)
- CodeQL 安全扫描
- CodeRabbit AI 代码审查
- PR 自动描述生成
- PR 自动标签 (labeler.yml)
- Dependabot 依赖更新

**待完善部分:**
- 仓库级 Branch Protection 规则（需手动配置）
- Environments 环境配置（需手动配置）
- GitHub Copilot 指令文件
- Labels 初始化（自动标签依赖这些标签存在）

### 1.2 目标

- **主要目标**:
  - 配置 Branch Protection 规则，保护主分支
  - 设置 Environments 实现分环境部署
  - 配置 GitHub Copilot 指令文件，统一 AI 编码风格
  - 初始化项目所需的 Labels

- **非目标**:
  - 完全替代人工代码审查
  - 自动合并 PR（始终需要人工确认）

### 1.3 术语定义

| 术语 | 定义 |
|------|------|
| Branch Protection | GitHub 分支保护规则，限制对分支的直接推送 |
| Environments | GitHub 部署环境，可配置审批人和密钥 |
| Copilot Instructions | GitHub Copilot 的项目级指令配置文件 |
| Labels | GitHub Issue/PR 的分类标签 |

---

## 2. 设计方案

### 2.1 Branch Protection 配置

**main 分支保护规则:**

| 规则 | 值 | 说明 |
|------|-----|------|
| Require PR | ✅ | 禁止直接推送 |
| Require status checks | ✅ | 必须通过 CI |
| Required checks | quality, test, security | 必选检查项 |
| Require review | ✅ | 至少 1 人审批 |
| Dismiss stale reviews | ✅ | 新提交后需重新审批 |
| Require CODEOWNERS review | ✅ | CODEOWNERS 必须审批 |
| Restrict push access | ✅ | 仅允许管理员 |
| Allow force push | ❌ | 禁止强制推送 |
| Allow deletions | ❌ | 禁止删除分支 |

**配置步骤:**
1. 进入 Settings → Branches
2. 点击 "Add branch protection rule"
3. Branch name pattern: `main`
4. 勾选上述规则

### 2.2 Environments 配置

```yaml
# 环境定义
environments:
  staging:
    # 自动部署到预发环境
    deployment_branch_policy:
      protected_branches: false
      custom_branches:
        - "main"
        - "develop"
    secrets:
      - OPENAI_API_KEY
      - MYSQL_PASSWORD
      - MILVUS_TOKEN
    variables:
      - ENVIRONMENT: staging

  production:
    # 需要审批才能部署
    reviewers:
      - users: ["ilivoo"]
    wait_timer: 5  # 5 分钟等待期
    deployment_branch_policy:
      protected_branches: true  # 仅从受保护分支部署
    secrets:
      - OPENAI_API_KEY
      - MYSQL_PASSWORD
      - MILVUS_TOKEN
    variables:
      - ENVIRONMENT: production
```

**配置步骤:**
1. 进入 Settings → Environments
2. 创建 `staging` 环境
3. 创建 `production` 环境，添加 Required reviewers

### 2.3 GitHub Copilot 指令

**文件位置:** `.github/copilot-instructions.md`

**作用:**
- 告诉 GitHub Copilot 项目的技术栈和编码规范
- 提供常用代码模式示例
- 定义禁止事项

**已创建:** ✅

### 2.4 Labels 初始化

**为什么需要 Labels:**

项目已有 `.github/labeler.yml` 配置，会根据 PR 改动文件自动添加标签：

```yaml
# 现有的自动标签规则
"area/workflow":
  - changed-files:
      - any-glob-to-any-file: "src/oceanus_agent/workflow/**/*"

"area/services":
  - changed-files:
      - any-glob-to-any-file: "src/oceanus_agent/services/**/*"
```

**但这些标签必须先在仓库中存在**，否则自动打标签会失败（静默失败）。

**初始化脚本:** `scripts/init_github_labels.py`

**使用方式:**

```bash
# 方式一：使用 GitHub API（需要 Token）
export GITHUB_TOKEN="ghp_xxx"
python scripts/init_github_labels.py owner/repo

# 方式二：输出 GitHub CLI 命令
python scripts/init_github_labels.py --gh-cli

# 然后手动执行输出的命令
gh label create "area/workflow" --color "xxx" --description "xxx"
```

**标签清单:**

| 标签 | 颜色 | 用途 |
|------|------|------|
| `area/workflow` | Blue | 工作流相关改动 |
| `area/services` | Blue | 服务层改动 |
| `area/api` | Blue | API 层改动 |
| `area/models` | Blue | 模型层改动 |
| `area/config` | Blue | 配置相关改动 |
| `area/tests` | Blue | 测试相关 |
| `area/ci` | Blue | CI/CD 相关 |
| `area/deployment` | Blue | 部署相关 |
| `type/feature` | Cyan | 新功能 |
| `type/bug` | Red | Bug 修复 |
| `type/documentation` | Blue | 文档 |
| `type/refactor` | Purple | 重构 |
| `type/dependencies` | Yellow | 依赖更新 |
| `complexity/low` | Green | 低复杂度 |
| `complexity/medium` | Yellow | 中等复杂度 |
| `complexity/high` | Red | 高复杂度 |

---

## 3. 文件变更清单

### 3.1 新增文件

| 文件路径 | 说明 | 状态 |
|----------|------|------|
| `.github/copilot-instructions.md` | Copilot 指令文件 | ✅ 已创建 |
| `scripts/init_github_labels.py` | Labels 初始化脚本 | ✅ 已创建 |
| `docs/design/github-ai-integration.md` | 本设计文档 | ✅ 已创建 |

### 3.2 手动配置事项

| 设置项 | 位置 | 状态 |
|--------|------|------|
| Branch Protection | Settings → Branches | ⏳ 待配置 |
| Environments | Settings → Environments | ⏳ 待配置 |
| Labels | 运行初始化脚本 | ⏳ 待执行 |

---

## 4. 参考资料

- [GitHub Branch Protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [GitHub Copilot Instructions](https://docs.github.com/en/copilot/customizing-copilot/adding-repository-custom-instructions-for-github-copilot)
- [GitHub Labels](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/managing-labels)
