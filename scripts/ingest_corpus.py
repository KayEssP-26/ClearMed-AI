# Run from project root:
#   python scripts/ingest_corpus.py [num_abstracts]
#
# Examples:
#   python scripts/ingest_corpus.py 10     # small validation run
#   python scripts/ingest_corpus.py        # default (500 abstracts)

import sys
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent

# Load environment variables from .env at the project root.
load_dotenv(dotenv_path=_ROOT / ".env")

# The backend package is rooted at backend/ (its modules import `app.*`),
# so put backend/ on the path before importing the ingest routine.
sys.path.insert(0, str(_ROOT / "backend"))

from app.rag.ingest import ingest_corpus  # noqa: E402


if __name__ == "__main__":
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    print(f"Ingesting {num} abstracts …")
    ingest_corpus(num_abstracts=num)
    print("Ingestion complete")
