"""Local embedding via sentence-transformers.

Used ONLY by the one-time corpus ingest (scripts/ingest_corpus.py), so the full
corpus can be embedded on CPU without touching the HF Inference API's daily
request cap. It produces the same 384-dim vectors as the API-based embedder in
embedder.py, so the Pinecone index and query-time retrieval are unaffected.

The deployed backend does NOT import this module — query-time embedding still
goes through embedder.py (one HF API call per request), so torch is not needed
in production.
"""

from functools import lru_cache

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the heavy sentence-transformers/torch import only
    # happens when ingest actually runs, and is loaded once per process.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(_MODEL_NAME)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings locally, returning one 384-dim vector each."""
    model = _get_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=False,
        convert_to_numpy=True,
    )
    return [[float(v) for v in row] for row in vectors]
