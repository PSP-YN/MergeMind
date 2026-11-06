import re


class UnsafePatch(ValueError):
    pass


def validate_unified_diff(patch: str) -> str:
    patch = patch.strip()
    if patch.startswith("```") and patch.endswith("```"):
        lines = patch.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            patch = "\n".join(lines[1:-1]).strip()
    if patch == "NO_PATCH":
        return patch
    if len(patch.encode("utf-8")) > 500_000:
        raise UnsafePatch("Proposed patch exceeds 500 KB")
    if not (patch.startswith("diff --git ") or patch.startswith("--- a/")):
        raise UnsafePatch("Model output is not a unified diff")
    paths = re.findall(r"^(?:\+\+\+|---) [ab]/([^\s]+)", patch, flags=re.MULTILINE)
    for path in paths:
        if path.startswith("/") or ".." in path.split("/") or "\\" in path:
            raise UnsafePatch("Patch contains an unsafe file path")
    if re.search(r"^(?:\+\+\+|---) /dev/null", patch, flags=re.MULTILINE):
        return patch
    return patch
