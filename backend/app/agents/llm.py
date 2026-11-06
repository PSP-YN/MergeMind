import httpx

from backend.app.core.config import settings


class LLMError(RuntimeError):
    pass


class LLMClient:
    """OpenAI-compatible chat completions client; works with local Ollama or hosted providers."""

    async def complete(self, system: str, user: str, *, temperature: float = 0.2) -> str:
        base = settings.llm_base_url.rstrip("/")
        headers = {"Content-Type": "application/json"}
        if settings.llm_api_key:
            headers["Authorization"] = f"Bearer {settings.llm_api_key}"
        payload = {
            "model": settings.llm_model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
                response = await client.post(f"{base}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise LLMError("The model returned an empty response")
                return content.strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMError(
                "LLM request failed. Check the configured OpenAI-compatible endpoint, model, and credentials."
            ) from exc
