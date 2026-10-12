from functools import lru_cache

from google import genai
from google.genai import types

from app.config import settings


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    return genai.Client(
        api_key=settings.gemini_key,
        http_options=types.HttpOptions(
            timeout=30_000,
            retry_options=types.HttpRetryOptions(attempts=1),
        ),
    )