"""Docs and CI presence tests."""

from pathlib import Path


def test_docs_are_split_user_and_developer() -> None:
    """@brief User docs and developer docs should both exist."""
    assert Path("README.md").exists()
    assert Path("docs/user-guide.md").exists()
    assert Path("docs/developer-guide.md").exists()
    assert Path("docs/deployment.md").exists()


def test_release_workflow_exists() -> None:
    """@brief Tag release workflow should be present and draft enabled."""
    workflow = Path(".github/workflows/release.yml")
    assert workflow.exists()

    content = workflow.read_text(encoding="utf-8")
    assert "tags:" in content
    assert "draft: true" in content
