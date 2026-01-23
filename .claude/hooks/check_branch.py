#!/usr/bin/env python3
"""SessionStart hook: 检查当前分支状态并在会话开始时提醒。

输入 (stdin): JSON 格式，包含 session_id, cwd 等
输出: stdout 内容会添加到 Claude 的上下文中
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


def has_uncommitted_changes(cwd: str) -> bool:
    """检查是否有未提交的更改。"""
    try:
        result = subprocess.run(  # nosec B603 B607
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main() -> None:
    """主函数。"""
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    cwd = hook_input.get("cwd", ".")
    branch = get_current_branch(cwd)

    if branch is None:
        sys.exit(0)

    if branch in {"main", "master"}:
        has_changes = has_uncommitted_changes(cwd)

        message = f"""
[Git 分支状态]
当前分支: {branch} (受保护分支)
"""
        if has_changes:
            message += """
警告: 检测到未提交的更改！
建议: 在开始新任务前，请先创建功能分支。

快速创建分支:
  git checkout -b feat/issue-<NUMBER>
  git checkout -b fix/issue-<NUMBER>
"""
        else:
            message += """
提示: 如需修改代码，请先创建功能分支。
"""
        print(message)
    else:
        print(f"[Git] 当前分支: {branch}")

    sys.exit(0)


if __name__ == "__main__":
    main()
