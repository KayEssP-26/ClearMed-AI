from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is three levels up from this file:
#   backend/app/config.py -> backend/app -> backend -> <root>
# Resolving the .env path absolutely means the backend loads the same
# credentials whether it's launched from the repo root or from backend/.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    hf_token: str
    pinecone_api_key: str
    pinecone_index_name: str = "clearmed"
    supabase_url: str
    supabase_key: str
    backend_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE))


settings = Settings()
