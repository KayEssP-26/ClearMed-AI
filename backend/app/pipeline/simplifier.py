from pathlib import Path
from huggingface_hub import InferenceClient
from app.config import settings
from app.rag.retriever import retrieve_chunks

_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "simplify_v2.txt"


def _load_prompt() -> str:
    if not _PROMPT_PATH.exists():
        raise FileNotFoundError(f"Prompt template not found: {_PROMPT_PATH}")
    return _PROMPT_PATH.read_text(encoding="utf-8")


def simplify_text(text: str) -> tuple[str, list[str]]:
    """
    Simplify clinical *text* using a RAG-augmented HF Inference API call.

    Returns:
        (simplified_text, source_chunks)
    """
    source_chunks = retrieve_chunks(text, top_k=3)
    retrieved_context = "\n---\n".join(source_chunks)

    template = _load_prompt()
    prompt = template.format(
        retrieved_context=retrieved_context,
        input_text=text,
    )

    client = InferenceClient(token=settings.hf_token)
    # The HF serverless providers serve this instruct model as a conversational
    # ("chat") model, so we use chat_completion rather than raw text_generation.
    # The whole RAG prompt is passed as a single user message.
    completion = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        model=_MODEL,
        max_tokens=512,
        temperature=0.3,
    )

    simplified = completion.choices[0].message.content.strip()
    return simplified, source_chunks
