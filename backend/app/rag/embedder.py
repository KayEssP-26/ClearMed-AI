from huggingface_hub import InferenceClient
from app.config import settings

_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def embed_text(text: str) -> list[float]:
    """Return a flat list of floats representing the embedding of *text*."""
    client = InferenceClient(token=settings.hf_token)
    result = client.feature_extraction(text, model=_MODEL)
    # result may be a nested list (1 x D) or already flat; normalise to 1-D
    if isinstance(result[0], (list, tuple)):
        embedding = result[0]
    else:
        embedding = result
    return [float(v) for v in embedding]
