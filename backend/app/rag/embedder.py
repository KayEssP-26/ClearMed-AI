from math import sqrt

from google.genai import types

from app.gemini import get_gemini_client

_MODEL = "gemini-embedding-001"
_OUTPUT_DIMENSIONALITY = 384
PINECONE_NAMESPACE = "gemini-embedding-001-v1"


def _embedding_config() -> types.EmbedContentConfig:
    return types.EmbedContentConfig(
        output_dimensionality=_OUTPUT_DIMENSIONALITY,
        task_type="RETRIEVAL_QUERY",
    )


def _normalize(values: list[float]) -> list[float]:
    vector = [float(value) for value in values]
    magnitude = sqrt(sum(value * value for value in vector))
    return [value / magnitude for value in vector] if magnitude else vector


def embed_text(text: str) -> list[float]:
    """Embed a retrieval query using the shared 384-dimensional Gemini space."""
    response = get_gemini_client().models.embed_content(
        model=_MODEL,
        contents=f"task: search result | query: {text}",
        config=_embedding_config(),
    )
    if not response.embeddings:
        raise ValueError("Gemini returned no query embedding.")
    return _normalize(response.embeddings[0].values)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed corpus documents with the same model and dimensionality as queries."""
    if not texts:
        return []

    response = get_gemini_client().models.embed_content(
        model=_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            output_dimensionality=_OUTPUT_DIMENSIONALITY,
            task_type="RETRIEVAL_DOCUMENT",
        ),
    )
    embeddings = response.embeddings or []
    if len(embeddings) != len(texts):
        raise ValueError("Gemini returned an incomplete document embedding batch.")
    return [_normalize(embedding.values) for embedding in embeddings]
