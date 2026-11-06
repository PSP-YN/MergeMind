import asyncio

from backend.app.agents.sandbox import verify_patch_in_sandbox


def test_sandbox_skips_when_no_patch_was_produced():
    result = asyncio.run(
        verify_patch_in_sandbox("https://github.com/example/repo", "NO_PATCH")
    )
    assert result.startswith("SKIPPED")


def test_sandbox_reports_missing_git_without_attempting_clone(monkeypatch):
    import backend.app.agents.sandbox as sandbox

    monkeypatch.setattr(sandbox.shutil, "which", lambda _name: None)
    result = asyncio.run(
        sandbox.verify_patch_in_sandbox(
            "https://github.com/example/repo",
            "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-a\n+b",
        )
    )
    assert result.startswith("PARTIAL")
    assert "Git is not installed" in result
