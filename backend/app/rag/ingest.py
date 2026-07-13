import uuid
from datasets import load_dataset
from pinecone import Pinecone
from app.config import settings
from app.rag.local_embedder import embed_batch

# How many chunks to embed (locally) and upsert to Pinecone per batch.
_BATCH_SIZE = 100


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


def _flush(index, chunk_texts: list[str], total: int) -> None:
    """Embed a batch of chunk texts locally and upsert them to Pinecone."""
    if not chunk_texts:
        return
    vectors = embed_batch(chunk_texts)
    records = [
        {"id": str(uuid.uuid4()), "values": vec, "metadata": {"text": txt}}
        for txt, vec in zip(chunk_texts, vectors)
    ]
    index.upsert(vectors=records)
    print(f"Embedded + upserted {total} chunks so far …")


def ingest_corpus(num_abstracts: int = 500) -> None:
    """Load PubMedQA, chunk, embed locally, and upsert to Pinecone.

    Embedding runs on the local CPU via sentence-transformers, so there is no
    HF Inference API quota limit on the corpus size — the full 500 abstracts
    (~2000 chunks) can be ingested in a single run.
    """
    dataset = load_dataset("pubmed_qa", "pqa_unlabeled", split="train")
    items = list(dataset.select(range(min(num_abstracts, len(dataset)))))

    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)

    pending: list[str] = []
    total_chunks = 0

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
                _flush(index, pending, total_chunks)
                pending = []

    _flush(index, pending, total_chunks)
    print(f"Ingestion complete. {total_chunks} chunks total.")
