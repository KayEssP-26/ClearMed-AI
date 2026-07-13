import time
import asyncio
from contextlib import asynccontextmanager

import textstat
from fastapi import FastAPI, BackgroundTasks, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    SimplifyRequest,
    SimplifyResponse,
)
from app.pipeline.simplifier import simplify_text
from app.pipeline.ocr import extract_text_from_file
from app.db.logger import log_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic can go here (e.g. warm-up calls, DB checks)
    yield
    # Shutdown logic can go here


app = FastAPI(title="ClearMed AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_pipeline(
    text: str,
) -> tuple[str, list[str], float, float, int]:
    """
    Shared pipeline: simplification + readability metrics.

    Returns:
        (simplified, sources, readability_before,
         readability_after, latency_ms)
    """
    start = time.monotonic()

    readability_before: float = textstat.flesch_reading_ease(text)

    simplified, sources = simplify_text(text)

    readability_after: float = textstat.flesch_reading_ease(simplified)
    latency_ms: int = int((time.monotonic() - start) * 1000)

    return simplified, sources, readability_before, readability_after, latency_ms


# ---------------------------------------------------------------------------
# POST /simplify
# ---------------------------------------------------------------------------

@app.post("/simplify", response_model=SimplifyResponse)
async def simplify(request: SimplifyRequest, background_tasks: BackgroundTasks):
    simplified, sources, rb, ra, latency = _run_pipeline(request.text)

    log_data = {
        "mode": "text",
        "prompt_version": "v2",
        "input_text": request.text,
        "input_length": len(request.text),
        "readability_before": rb,
        "readability_after": ra,
        "readability_delta": ra - rb,
        "latency_ms": latency,
    }
    background_tasks.add_task(log_request, log_data)

    return SimplifyResponse(
        simplified=simplified,
        sources=sources,
        readability_before=rb,
        readability_after=ra,
        latency_ms=latency,
    )


# ---------------------------------------------------------------------------
# POST /simplify-report
# ---------------------------------------------------------------------------

@app.post("/simplify-report", response_model=SimplifyResponse)
async def simplify_report(
    background_tasks: BackgroundTasks,
    file: UploadFile,
):
    file_bytes = await file.read()
    ocr_text = extract_text_from_file(file_bytes, file.filename or "upload")

    simplified, sources, rb, ra, latency = _run_pipeline(ocr_text)

    log_data = {
        "mode": "report",
        "prompt_version": "v2",
        "input_text": ocr_text,
        "input_length": len(ocr_text),
        "readability_before": rb,
        "readability_after": ra,
        "readability_delta": ra - rb,
        "latency_ms": latency,
    }
    background_tasks.add_task(log_request, log_data)

    return SimplifyResponse(
        simplified=simplified,
        sources=sources,
        readability_before=rb,
        readability_after=ra,
        latency_ms=latency,
    )
