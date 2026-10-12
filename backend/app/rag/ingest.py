import hashlib
import time
from datasets import load_dataset
from pinecone import Pinecone
from app.config import settings
from app.rag.embedder import PINECONE_NAMESPACE, embed_batch

# How many chunks to embed and upsert to Pinecone per batch.
_BATCH_SIZE = 100
_EMBEDDING_WINDOW_SECONDS = 60
_MAX_EMBEDDING_ATTEMPTS = 3


def _chunk_text(text: str, chunk_size: int = 200, overlap: int = 20) -> list[str]:
    """Split *text* into word-based chunks of ~chunk_size tokens with overlap."""
    words = text.split()
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def _flush(
    index,
    chunk_texts: list[str],
    total: int,
    last_embedding_request_at: float | None,
) -> float | None:
    """Embed a batch of chunk texts with Gemini and upsert them to Pinecone."""
    if not chunk_texts:
        return last_embedding_request_at

    if last_embedding_request_at is not None:
        wait_seconds = _EMBEDDING_WINDOW_SECONDS - (time.monotonic() - last_embedding_request_at)
        if wait_seconds > 0:
            print(f"Waiting {wait_seconds:.0f}s for the Gemini embedding quota window …")
            time.sleep(wait_seconds)

    for attempt in range(1, _MAX_EMBEDDING_ATTEMPTS + 1):
        try:
            vectors = embed_batch(chunk_texts)
            last_embedding_request_at = time.monotonic()
            break
        except Exception as exc:
            is_rate_limit = "429" in str(exc) or "quota" in str(exc).lower()
            if not is_rate_limit or attempt == _MAX_EMBEDDING_ATTEMPTS:
                raise
            print("Gemini embedding quota reached; retrying after 60 seconds …")
            time.sleep(_EMBEDDING_WINDOW_SECONDS)

    records = [
        {
            "id": hashlib.sha256(txt.encode("utf-8")).hexdigest(),
            "values": vec,
            "metadata": {"text": txt},
        }
        for txt, vec in zip(chunk_texts, vectors)
    ]
    index.upsert(vectors=records, namespace=PINECONE_NAMESPACE)
    print(f"Embedded + upserted {total} chunks so far …")
    return last_embedding_request_at


def ingest_corpus(num_abstracts: int = 500) -> None:
    """Load PubMedQA, chunk, embed with Gemini, and upsert to Pinecone."""
    dataset = load_dataset("pubmed_qa", "pqa_unlabeled", split="train")
    items = list(dataset.select(range(min(num_abstracts, len(dataset)))))

    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)

    pending: list[str] = []
    total_chunks = 0
    last_embedding_request_at: float | None = None

    for item in items:
        context_parts = item.get("context", [])
        if isinstance(context_parts, dict):
            # pubmed_qa stores context as {"contexts": [...], "labels": [...], ...}
            context_parts = context_parts.get("contexts", [])
        full_text = " ".join(context_parts)

        for chunk in _chunk_text(full_text):
            pending.append(chunk)
            total_chunks += 1

            if len(pending) >= _BATCH_SIZE:
                last_embedding_request_at = _flush(
                    index,
                    pending,
                    total_chunks,
                    last_embedding_request_at,
                )
                pending = []

    _flush(index, pending, total_chunks, last_embedding_request_at)
    print(f"Ingestion complete. {total_chunks} chunks total.")
