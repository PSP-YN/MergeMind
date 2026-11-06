from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MergeMind"
    mode: str = "demo"
    switch_base_url: str | None = None
    switch_agent_id: str | None = None
    switch_agent_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
