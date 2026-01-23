#!/usr/bin/env python3
"""PreToolUse hook: 阻止在 main 分支上进行代码修改。

输入 (stdin): JSON 格式，包含 tool_name, tool_input, cwd 等
输出:
  - exit 0: 允许操作
  - exit 2: 阻止操作，stderr 内容返回给 Claude
"""

import json
import subprocess  # nosec B404
import sys


def get_current_branch(cwd: str) -> str | None:
    """获取当前 Git 分支名。"""
    try:
        result = subprocess.run(  # nosec B603 B607
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def is_protected_branch(branch: str) -> bool:
    """判断是否为受保护分支。"""
    protected = {"main", "master"}
    return branch in protected


def get_open_issues_hint(cwd: str) -> str:
    """获取开放的 GitHub Issues 提示。"""
    try:
        result = subprocess.run(  # nosec B603 B607
            [
                "gh",
                "issue",
                "list",
                "--state",
                "open",
                "--limit",
                "5",
                "--json",
                "number,title,labels",
            ],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            issues = json.loads(result.stdout)
            if issues:
                lines = ["\n## 可用的 GitHub Issues:"]
                for issue in issues:
                    labels = issue.get("labels", [])
                    label_names = [lbl.get("name", "") for lbl in labels]
                    label_str = f" [{', '.join(label_names)}]" if label_names else ""
                    lines.append(f"  #{issue['number']}: {issue['title']}{label_str}")
                return "\n".join(lines)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass
    return ""


def is_allowed_file(file_path: str) -> bool:
    """检查文件是否允许在 main 分支修改。"""
    allowed_patterns = [
        ".md",
        ".txt",
        ".rst",
        "/docs/",
        "/.github/",
        "/.claude/plans/",
    ]

    file_path_lower = file_path.lower()
    for pattern in allowed_patterns:
        if pattern in file_path_lower or file_path_lower.endswith(pattern):
            return True
    return False


def main() -> None:
    """主函数。"""
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    cwd = hook_input.get("cwd", ".")
    tool_input = hook_input.get("tool_input", {})

    file_path = tool_input.get("file_path") or tool_input.get("path", "")

    if is_allowed_file(str(file_path)):
        sys.exit(0)

    branch = get_current_branch(cwd)
    if branch is None:
        sys.exit(0)

    if not is_protected_branch(branch):
        sys.exit(0)

    issues_hint = get_open_issues_hint(cwd)

    error_message = f"""
[分支保护] 检测到你正在 '{branch}' 分支上尝试修改代码文件: {file_path}

为了保持代码库的整洁和可追溯性，请先创建一个新分支。

## 建议的操作步骤:

1. 选择一个相关的 GitHub Issue（或创建新 Issue）
2. 基于 Issue 创建分支:
   ```bash
   # 功能开发
   git checkout -b feat/issue-<NUMBER>

   # Bug 修复
   git checkout -b fix/issue-<NUMBER>

   # 文档更新
   git checkout -b docs/issue-<NUMBER>
   ```

3. 然后继续你的修改
{issues_hint}

## 分支命名规范:
- feat/issue-42     # 新功能
- fix/issue-123     # Bug 修复
- refactor/xxx      # 重构
- docs/xxx          # 文档

如需帮助创建分支，请告诉我 Issue 编号或功能描述。
"""
    print(error_message, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
