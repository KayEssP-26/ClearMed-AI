from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is three levels up from this file:
#   backend/app/config.py -> backend/app -> backend -> <root>
# Resolving the .env path absolutely means the backend loads the same
# credentials whether it's launched from the repo root or from backend/.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    gemini_api_key: str | None = None
    google_api_key: str | None = None
    pinecone_api_key: str | None = None
    pinecone_index_name: str = "clearmed"
    supabase_url: str | None = None
    supabase_key: str | None = None
    backend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    @property
    def gemini_key(self) -> str:
        key = self.gemini_api_key or self.google_api_key
        if not key:
            raise ValueError("Missing Gemini API key. Set GEMINI_API_KEY or GOOGLE_API_KEY in the environment.")
        return key


settings = Settings()
