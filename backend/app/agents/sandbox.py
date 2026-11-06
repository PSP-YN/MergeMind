import asyncio
import os
import shutil
import tempfile
from pathlib import Path

from backend.app.agents.patch_safety import validate_unified_diff
from backend.app.agents.repository import parse_repository_url


async def _run(args: list[str], *, cwd: str | None = None, env: dict | None = None,
               timeout: int = 90) -> tuple[int, str]:
    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        output, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except TimeoutError:
        process.kill()
        await process.communicate()
        return 124, f"Command timed out after {timeout} seconds: {args[0]}"
    return process.returncode or 0, output.decode("utf-8", errors="replace")[-8000:]


async def verify_patch_in_sandbox(repository_url: str, patch: str) -> str:
    """Apply a model patch to a disposable clone and run syntax-only checks in Docker.

    No repository code, package installation, project test, or shell script is executed.
    """
    try:
        patch = validate_unified_diff(patch)
    except ValueError as exc:
        return f"FAILED — patch validation: {exc}"
    if patch == "NO_PATCH":
        return "SKIPPED — Implementer did not produce a patch."
    if not shutil.which("git"):
        return "PARTIAL — Git is not installed. Patch application and sandbox checks were not run."

    owner, repo = parse_repository_url(repository_url)
    with tempfile.TemporaryDirectory(prefix="mergemind-review-") as temp:
        root = Path(temp)
        checkout = root / "source"
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(root),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
        clone_code, clone_output = await _run(
            ["git", "clone", "--depth", "1", "--no-recurse-submodules",
             f"https://github.com/{owner}/{repo}.git", str(checkout)],
            env=safe_env,
            timeout=120,
        )
        if clone_code != 0:
            return f"FAILED — could not create disposable public repository checkout. {clone_output[-1500:]}"

        patch_file = root / "proposal.patch"
        patch_file.write_text(patch, encoding="utf-8")
        check_code, check_output = await _run(
            ["git", "apply", "--check", str(patch_file)],
            cwd=str(checkout),
            env=safe_env,
            timeout=20,
        )
        if check_code != 0:
            return f"FAILED — proposed diff does not apply cleanly to the repository. {check_output[-1500:]}"
        apply_code, apply_output = await _run(
            ["git", "apply", str(patch_file)],
            cwd=str(checkout),
            env=safe_env,
            timeout=20,
        )
        if apply_code != 0:
            return f"FAILED — could not apply the proposal to the disposable checkout. {apply_output[-1500:]}"
        diff_code, diff_output = await _run(
            ["git", "diff", "--check"],
            cwd=str(checkout),
            env=safe_env,
            timeout=20,
        )
        if diff_code != 0:
            return f"FAILED — git diff --check found whitespace or patch-format problems. {diff_output[-1500:]}"

        result = [
            "Patch application: PASS (disposable clone only)",
            "git diff --check: PASS",
        ]
        docker = shutil.which("docker")
        if not docker:
            result.append("Python syntax check: SKIPPED (Docker is not installed)")
            result.append("Project tests: NOT RUN (untrusted repository code is never executed)")
            return "\n".join(result)

        image_code, image_output = await _run(
            [docker, "image", "inspect", "python:3.12-slim"],
            timeout=10,
        )
        if image_code != 0:
            result.append("Python syntax check: SKIPPED (python:3.12-slim image is not already available locally)")
            result.append("Project tests: NOT RUN (untrusted repository code is never executed)")
            return "\n".join(result)

        docker_code, docker_output = await _run(
            [
                docker, "run", "--rm",
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--pids-limit=64",
                "--memory=384m",
                "--cpus=1",
                "--user=65534:65534",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "-e", "PYTHONPYCACHEPREFIX=/tmp/mergemind-pycache",
                "-v", f"{checkout}:/workspace:ro",
                "-w", "/workspace",
                "python:3.12-slim",
                "python", "-m", "compileall", "-q", ".",
            ],
            timeout=90,
        )
        if docker_code == 0:
            result.append("Python syntax check: PASS (read-only, no-network Docker container)")
        else:
            result.append(f"Python syntax check: FAIL (exit {docker_code}) {docker_output[-1500:]}")
        result.append("Project tests: NOT RUN (no project code or test suite was executed)")
        return "\n".join(result)
