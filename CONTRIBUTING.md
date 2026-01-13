# 贡献指南

感谢你对 Oceanus Agent 的贡献！请仔细阅读本指南，确保贡献流程顺畅。

## 快速开始

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/oceanus-agent.git
cd oceanus-agent
```

### 2. 环境配置 (必须)

```bash
# 使用 Make 一键配置（推荐）
make setup

# 或手动执行
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pre-commit install --hook-type commit-msg
```

> **重要**: `pre-commit install` 会自动在每次 `git commit` 前运行代码检查。
> 这是强制要求，未安装将导致 CI 失败。

### 3. 验证安装

```bash
# 确认 pre-commit 已安装
pre-commit --version

# 运行一次全量检查
pre-commit run --all-files
```

## 代码提交流程

### 提交前检查清单

1. 运行 `pre-commit run --all-files` 并确保通过
2. 运行 `pytest tests/unit -v` 确保测试通过
3. 如有新功能，添加对应测试
4. 如修改配置，更新 `.env.example`

### Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: 添加新的诊断节点
fix: 修复 checkpoint 超时判断逻辑
docs: 更新 API 文档
refactor: 重构 MySQL 服务层
test: 添加 retriever 单元测试
chore: 更新依赖版本
```

### Pull Request 规范

1. PR 标题遵循 Commit 规范
2. 填写 PR 模板中的所有检查项
3. 确保 CI 全部通过（绿色）
4. 请求至少一位维护者 Review

## 代码风格

本项目使用以下工具强制代码风格：

| 工具 | 用途 | 配置位置 |
|------|------|----------|
| Ruff | Linting + Formatting | `pyproject.toml` |
| MyPy | 类型检查 | `pyproject.toml` |
| EditorConfig | IDE 基础设置 | `.editorconfig` |
| Pre-commit | Git Hooks 集成 | `.pre-commit-config.yaml` |

### 关键规则

- **行长度**: 88 字符 (Ruff/Black 默认)
- **缩进**: 4 空格 (Python)
- **引号**: 双引号优先
- **类型注解**: 所有公开函数必须有类型提示
- **数据模型**: 强制使用 Pydantic v2

## 常见问题

### pre-commit 失败了怎么办？

```bash
# 查看具体错误
pre-commit run --all-files

# Ruff 自动修复
ruff check --fix src/ tests/
ruff format src/ tests/

# 重新提交
git add .
git commit -m "your message"
```

### 如何跳过 pre-commit？(不推荐)

```bash
git commit --no-verify -m "emergency fix"
```

> **警告**: CI 仍会检查，不符合规范的代码无法合并。

## 分支管理

- **main**: 主分支，保持随时可部署状态
- **feat/***: 新功能开发分支
- **fix/***: Bug 修复分支
- **refactor/***: 代码重构分支

## 联系方式

如有问题，请在 GitHub Issues 中提问。
