# GitHub 分支保护规则配置指南

> 本文档说明如何为 oceanus-agent 项目配置 GitHub Branch Protection Rules，确保代码质量和安全合并流程。

## 1. 概述

Branch Protection Rules 用于保护重要分支（如 `main`），强制执行：

- 必须通过 Pull Request 才能合并代码
- 必须通过 CI 检查
- 必须获得 Code Review 批准
- 禁止强制推送和删除分支

## 2. 必须通过的 CI 检查

根据项目 `.github/workflows/ci.yml` 配置，以下检查必须通过：

| 检查名称 | 说明 | 必选 |
|----------|------|------|
| `quality` | 代码质量检查 (pre-commit, ruff, mypy) | ✅ |
| `test` | 单元测试 (pytest) | ✅ |
| `security` | 安全扫描 (Bandit) | ✅ |
| `build` | Docker 镜像构建 | ✅ |

## 3. 配置步骤

### 3.1 通过 GitHub Web UI 配置

1. 进入仓库页面，点击 **Settings**
2. 左侧菜单选择 **Branches**
3. 在 "Branch protection rules" 区域，点击 **Add rule**
4. 配置规则：

#### 基础设置

| 设置项 | 值 | 说明 |
|--------|-----|------|
| Branch name pattern | `main` | 保护主分支 |

#### 保护规则

勾选以下选项：

- [x] **Require a pull request before merging**
  - [x] Require approvals: `1`
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - 添加必选检查：
    - `quality`
    - `test`
    - `security`
    - `build`

- [x] **Require conversation resolution before merging**

- [x] **Do not allow bypassing the above settings**

- [ ] **Allow force pushes** (不勾选)

- [ ] **Allow deletions** (不勾选)

5. 点击 **Create** 保存规则

### 3.2 通过 GitHub CLI 配置

```bash
# 安装 GitHub CLI (如未安装)
# macOS: brew install gh
# Linux: https://github.com/cli/cli/blob/trunk/docs/install_linux.md

# 登录
gh auth login

# 配置分支保护规则
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --header "Accept: application/vnd.github+json" \
  --field required_status_checks='{"strict":true,"contexts":["quality","test","security","build"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"dismissal_restrictions":{},"dismiss_stale_reviews":true,"require_code_owner_reviews":true,"required_approving_review_count":1}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_conversation_resolution=true
```

> **注意**：将 `{owner}/{repo}` 替换为实际的仓库路径，如 `myorg/oceanus-agent`。

### 3.3 验证配置

配置完成后，可通过以下方式验证：

```bash
# 查看分支保护规则
gh api repos/{owner}/{repo}/branches/main/protection

# 或在 Web UI 查看
# Settings -> Branches -> main 旁边应显示 "protected" 标签
```

## 4. 推荐的额外配置

### 4.1 保护 `develop` 分支（可选）

如果使用 Git Flow 工作流，建议同样保护 `develop` 分支：

```bash
gh api repos/{owner}/{repo}/branches/develop/protection \
  --method PUT \
  --header "Accept: application/vnd.github+json" \
  --field required_status_checks='{"strict":true,"contexts":["quality","test"]}' \
  --field required_pull_request_reviews='{"required_approving_review_count":1}' \
  --field allow_force_pushes=false \
  --field allow_deletions=false
```

### 4.2 配置 CODEOWNERS（已完成）

项目已配置 `.github/CODEOWNERS`，确保关键代码变更需要指定人员审查。

## 5. 常见问题

### Q: CI 检查不显示在状态检查列表中？

**A**: 状态检查只有在至少运行过一次后才会出现在列表中。请先创建一个 PR 触发 CI，然后再配置保护规则。

### Q: 如何在紧急情况下绕过保护规则？

**A**:
1. 仓库管理员可以临时禁用 "Do not allow bypassing the above settings"
2. 紧急修复后立即恢复设置
3. 建议在 PR 描述中说明紧急情况原因

### Q: 如何允许特定用户绕过？

**A**: 在保护规则中配置 "Restrict who can push to matching branches"，添加允许绕过的用户或团队。

---

## 相关文档

- [GitHub 官方文档：About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [项目 CI 配置](.github/workflows/ci.yml)
- [AI 集成指南](./ai-integration.md)
