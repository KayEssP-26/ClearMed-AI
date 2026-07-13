from pydantic import BaseModel


class SimplifyRequest(BaseModel):
    text: str


class SimplifyResponse(BaseModel):
    simplified: str
    sources: list[str]
    readability_before: float
    readability_after: float
    latency_ms: int
