from urllib.parse import urlparse

import httpx


class RepositoryError(RuntimeError):
    pass


def parse_repository_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url)
    parts = parsed.path.strip("/").removesuffix(".git").split("/")
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com" or len(parts) != 2:
        raise RepositoryError("Only public GitHub HTTPS repositories are supported")
    owner, repo = parts
    if not owner or not repo or owner in {".", ".."} or repo in {".", ".."}:
        raise RepositoryError("Invalid GitHub repository URL")
    return owner, repo


async def read_repository_context(url: str, *, max_files: int = 8) -> str:
    owner, repo = parse_repository_url(url)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "MergeMind/0.1"}
    async with httpx.AsyncClient(timeout=25, headers=headers, follow_redirects=True) as client:
        try:
            metadata_response = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            metadata_response.raise_for_status()
            metadata = metadata_response.json()
            branch = metadata["default_branch"]
            tree_response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
            )
            tree_response.raise_for_status()
            tree = tree_response.json().get("tree", [])
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise RepositoryError(
                "Could not read the public GitHub repository. Verify its URL, visibility, and API rate limit."
            ) from exc

        candidates = [
            item for item in tree
            if item.get("type") == "blob"
            and item.get("size", 0) <= 180_000
            and item.get("path", "").lower().endswith(
                (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".md", ".toml", ".json", ".yml", ".yaml")
            )
        ]
        priority = ("readme", "pyproject", "package.json", "main.", "app.", "index.", "test", "config")
        candidates.sort(
            key=lambda item: (
                next((i for i, token in enumerate(priority) if token in item["path"].lower()), len(priority)),
                item["path"].count("/"),
                item["path"],
            )
        )
        selected = candidates[:max_files]
        chunks = [
            f"Repository: {owner}/{repo}\nDefault branch: {branch}\nDescription: {metadata.get('description') or 'Not provided'}"
        ]
        for item in selected:
            try:
                file_response = await client.get(item["url"])
                file_response.raise_for_status()
                encoded = file_response.json().get("content", "")
                import base64
                content = base64.b64decode(encoded).decode("utf-8", errors="replace")
                chunks.append(f"\n--- FILE: {item['path']} ---\n{content[:12000]}")
            except (httpx.HTTPError, ValueError, KeyError):
                chunks.append(f"\n--- FILE: {item['path']} ---\n[Could not retrieve this file]")
        return "\n".join(chunks)
