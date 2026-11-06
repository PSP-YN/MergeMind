from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MergeMind"
    database_path: str = "data/mergemind.sqlite3"
    admin_token: str = ""
    encryption_key: str = ""
    llm_base_url: str = "http://127.0.0.1:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5-coder:3b"
    llm_timeout_seconds: int = 120
    switch_reconnect_seconds: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MERGEMIND_",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
