from pathlib import Path

from app.gemini import get_gemini_client
from app.rag.retriever import retrieve_chunks

_MODEL = "gemini-3.5-flash-lite"
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "simplify_v2.txt"


def _load_prompt() -> str:
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt template not found: {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _provider_unavailable_message(error: Exception) -> str:
    error_text = str(error).lower()
    if "429" in error_text or "quota" in error_text or "rate limit" in error_text:
        return (
            "ClearMed AI is temporarily unavailable because the Gemini API quota or rate "
            "limit was exceeded. Please verify your API configuration and try again."
        )
    if "missing gemini api key" in error_text:
        return "Set GEMINI_API_KEY or GOOGLE_API_KEY to enable Gemini simplification."
    return (
        "ClearMed AI is temporarily unavailable because the Gemini API request failed. "
        "Please verify the API key and model configuration, then try again."
    )


def simplify_text(text: str) -> tuple[str, list[str]]:
    """
    Simplify clinical *text* using a RAG-augmented Gemini API call.

    Returns:
        (simplified_text, source_chunks)
    """
    source_chunks: list[str] = []

    try:
        source_chunks = retrieve_chunks(text, top_k=3)
        retrieved_context = "\n---\n".join(source_chunks)

        template = _load_prompt()
        prompt = template.format(
            retrieved_context=retrieved_context,
            input_text=text,
        )

        response = get_gemini_client().interactions.create(
            model=_MODEL,
            input=prompt,
            store=False,
            generation_config={
                "temperature": 0.3,
                "max_output_tokens": 512,
            },
        )
        simplified = (response.output_text or "").strip()
        if not simplified:
            raise ValueError("Gemini returned an empty response.")
        return simplified, source_chunks
    except Exception as exc:
        raise RuntimeError(_provider_unavailable_message(exc)) from exc
