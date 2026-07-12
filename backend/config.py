from functools import lru_cache
from pathlib import Path

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

    # Comma-separated list of allowed CORS origins (exact matches — no wildcards), e.g. the
    # Vercel production domain plus a custom domain: "https://omnirag.vercel.app,https://omnirag.com"
    frontend_url: str = "http://localhost:3000"

    # Self-contained default (backend/data/index) — works regardless of Docker build context,
    # unlike a path climbing to a repo-root sibling. Override to point at a mounted volume
    # in production, since container filesystems are ephemeral by default (see README).
    data_dir: str = str(Path(__file__).resolve().parent / "data" / "index")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_url.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
