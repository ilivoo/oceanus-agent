#!/usr/bin/env python3
"""
Initialize GitHub repository labels for Oceanus Agent project.

This script creates the required labels for Issue classification and triage.
Requires: PyGithub, GITHUB_TOKEN environment variable

Usage:
    $ export GITHUB_TOKEN="ghp_xxx"
    $ python scripts/init_github_labels.py [owner/repo]

Or using GitHub CLI:
    $ gh label create "complexity/low" --color "0E8A16" --description "Low complexity"
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass


@dataclass
class LabelConfig:
    """Label configuration."""

    name: str
    color: str
    description: str


# Label definitions
LABELS: list[LabelConfig] = [
    # Area labels (used by labeler.yml for auto-labeling PRs)
    LabelConfig(
        name="area/workflow",
        color="1D76DB",  # Blue
        description="Changes to LangGraph workflow",
    ),
    LabelConfig(
        name="area/services",
        color="1D76DB",  # Blue
        description="Changes to service layer (LLM, Milvus, MySQL)",
    ),
    LabelConfig(
        name="area/api",
        color="1D76DB",  # Blue
        description="Changes to FastAPI routes",
    ),
    LabelConfig(
        name="area/config",
        color="1D76DB",  # Blue
        description="Changes to configuration or prompts",
    ),
    LabelConfig(
        name="area/models",
        color="1D76DB",  # Blue
        description="Changes to Pydantic data models",
    ),
    LabelConfig(
        name="area/tests",
        color="1D76DB",  # Blue
        description="Changes to test files",
    ),
    LabelConfig(
        name="area/ci",
        color="1D76DB",  # Blue
        description="Changes to CI/CD workflows",
    ),
    LabelConfig(
        name="area/deployment",
        color="1D76DB",  # Blue
        description="Changes to deployment configuration",
    ),
    # Complexity labels
    LabelConfig(
        name="complexity/low",
        color="0E8A16",  # Green
        description="Low complexity - simple change, < 50 lines",
    ),
    LabelConfig(
        name="complexity/medium",
        color="FBCA04",  # Yellow
        description="Medium complexity - moderate change, 50-200 lines",
    ),
    LabelConfig(
        name="complexity/high",
        color="D93F0B",  # Red
        description="High complexity - significant change, > 200 lines",
    ),
    # Type labels
    LabelConfig(
        name="type/feature",
        color="A2EEEF",  # Cyan
        description="New feature or enhancement request",
    ),
    LabelConfig(
        name="type/bug",
        color="D73A4A",  # Red
        description="Something isn't working as expected",
    ),
    LabelConfig(
        name="type/documentation",
        color="0075CA",  # Blue
        description="Documentation improvements or additions",
    ),
    LabelConfig(
        name="type/refactor",
        color="7057FF",  # Purple
        description="Code refactoring without functionality change",
    ),
    LabelConfig(
        name="type/question",
        color="D876E3",  # Pink
        description="Question about the project",
    ),
    LabelConfig(
        name="type/enhancement",
        color="84B6EB",  # Light blue
        description="Enhancement to existing functionality",
    ),
    LabelConfig(
        name="type/dependencies",
        color="EDEDED",  # Light gray
        description="Dependency updates",
    ),
    # Status labels
    LabelConfig(
        name="needs-triage",
        color="5319E7",  # Purple
        description="Needs AI analysis and classification",
    ),
    LabelConfig(
        name="ready-for-pr",
        color="0052CC",  # Blue
        description="Ready for PR creation",
    ),
    LabelConfig(
        name="needs-design-doc",
        color="FEF2C0",  # Light yellow
        description="Requires design document before implementation",
    ),
    LabelConfig(
        name="ai-analyzed",
        color="BFD4F2",  # Light blue
        description="Has been analyzed by AI",
    ),
    # Priority labels
    LabelConfig(
        name="priority/critical",
        color="B60205",  # Dark red
        description="Critical priority - needs immediate attention",
    ),
    LabelConfig(
        name="priority/high",
        color="D93F0B",  # Red
        description="High priority",
    ),
    LabelConfig(
        name="priority/medium",
        color="FBCA04",  # Yellow
        description="Medium priority",
    ),
    LabelConfig(
        name="priority/low",
        color="0E8A16",  # Green
        description="Low priority",
    ),
]


def create_labels_with_api(repo_name: str, token: str) -> None:
    """
    Create labels using GitHub API via PyGithub.

    Args:
        repo_name: Repository name in format 'owner/repo'
        token: GitHub personal access token
    """
    try:
        from github import Github, GithubException
    except ImportError:
        print("Error: PyGithub not installed")
        print("Run: pip install PyGithub")
        sys.exit(1)

    gh = Github(token)
    repo = gh.get_repo(repo_name)

    print(f"Creating labels for repository: {repo_name}")
    print("-" * 50)

    created = 0
    updated = 0
    skipped = 0

    for label in LABELS:
        try:
            # Try to get existing label
            existing = repo.get_label(label.name)

            # Check if update needed
            if (
                existing.color != label.color
                or existing.description != label.description
            ):
                existing.edit(
                    name=label.name,
                    color=label.color,
                    description=label.description,
                )
                print(f"  Updated: {label.name}")
                updated += 1
            else:
                print(f"  Skipped (exists): {label.name}")
                skipped += 1

        except GithubException as e:
            if e.status == 404:
                # Label doesn't exist, create it
                repo.create_label(
                    name=label.name,
                    color=label.color,
                    description=label.description,
                )
                print(f"  Created: {label.name}")
                created += 1
            else:
                print(f"  Error with {label.name}: {e}")

    print("-" * 50)
    print(f"Summary: {created} created, {updated} updated, {skipped} skipped")


def print_gh_cli_commands() -> None:
    """Print GitHub CLI commands to create labels."""
    print("# GitHub CLI commands to create labels")
    print("# Run these commands in your repository directory:\n")

    for label in LABELS:
        # Escape double quotes in description
        desc = label.description.replace('"', '\\"')
        print(
            f'gh label create "{label.name}" --color "{label.color}" --description "{desc}"'
        )

    print("\n# Or delete existing and recreate:")
    for label in LABELS:
        desc = label.description.replace('"', '\\"')
        print(f'gh label delete "{label.name}" --yes 2>/dev/null || true')
        print(
            f'gh label create "{label.name}" --color "{label.color}" --description "{desc}"'
        )


def main() -> None:
    """Main entry point."""
    # Check for --gh-cli flag
    if "--gh-cli" in sys.argv:
        print_gh_cli_commands()
        return

    # Get repository name
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        repo_name = sys.argv[1]
    else:
        repo_name = os.environ.get("GITHUB_REPOSITORY", "")

    if not repo_name:
        print("Usage: python scripts/init_github_labels.py [owner/repo]")
        print("       python scripts/init_github_labels.py --gh-cli")
        print("\nOptions:")
        print("  owner/repo    GitHub repository (e.g., 'ilivoo/oceanus-agent')")
        print("  --gh-cli      Print GitHub CLI commands instead of using API")
        print("\nEnvironment variables:")
        print("  GITHUB_TOKEN      GitHub personal access token (required for API)")
        print("  GITHUB_REPOSITORY Default repository name")
        sys.exit(1)

    # Get token
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("\nTo create a token:")
        print("1. Go to https://github.com/settings/tokens")
        print("2. Generate new token with 'repo' scope")
        print("3. Export: export GITHUB_TOKEN='ghp_xxx'")
        print("\nOr use --gh-cli flag to print GitHub CLI commands")
        sys.exit(1)

    create_labels_with_api(repo_name, token)


if __name__ == "__main__":
    main()
