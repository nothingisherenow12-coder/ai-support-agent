from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str
    gemini_api_key:str
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"
    groq_timeout_seconds: float = 30.0
    auth_username: str = ""
    auth_password: str = ""
    auth_secret_key: str = ""
    auth_token_ttl_minutes: int = 480
    auth_cookie_secure: bool = True
    max_upload_bytes: int = 20 * 1024 * 1024
    rag_max_distance:float=0.35
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,https://ai-support-agent-seven.vercel.app"

    model_config=SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

settings = Settings()
