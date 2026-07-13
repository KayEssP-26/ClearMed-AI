from pinecone import Pinecone
from app.config import settings
from app.rag.embedder import embed_text


def retrieve_chunks(query: str, top_k: int = 3) -> list[str]:
    """Return the top-k most relevant text chunks from the Pinecone index."""
    vector = embed_text(query)
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(settings.pinecone_index_name)
    response = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return [match["metadata"]["text"] for match in response["matches"]]
