from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    cohere_api_key: str = ""
    next_public_api_url: str = "http://localhost:8000"

    # llama-3.1-70b-versatile (named in the original spec) was deprecated by Groq;
    # llama-3.3-70b-versatile is its direct successor.
    groq_model: str = "llama-3.3-70b-versatile"

    app_name: str = "OmniRAG"
    environment: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
