import json
import time
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import get_settings
from evaluation.ragas_eval import evaluate_response
from generation.adaptive import adaptive_retrieve
from generation.generate import build_citations, stream_answer
from models.schemas import RagasScores
from pricing import estimate_cost_usd

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    query: str


def _jsonable(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [_jsonable(item) for item in obj]
    return obj


def _event(event_type: str, data) -> str:
    return json.dumps({"type": event_type, "data": _jsonable(data)}) + "\n"


def _stream_chat(query: str) -> Iterator[str]:
    settings = get_settings()
    start = time.perf_counter()

    result = adaptive_retrieve(query)
    yield _event("routing", result.routing)
    for hop in result.hops:
        yield _event("hop", hop)

    citations = build_citations(result.final_chunks)
    yield _event("citations", citations)

    usage_holder: dict = {}
    full_text = ""
    for delta in stream_answer(query, result.final_chunks, usage_holder=usage_holder):
        full_text += delta
        yield _event("token", delta)

    latency_ms = (time.perf_counter() - start) * 1000
    prompt_tokens = usage_holder.get("prompt_tokens")
    completion_tokens = usage_holder.get("completion_tokens")
    cost = (
        estimate_cost_usd(settings.gemini_model, prompt_tokens, completion_tokens)
        if prompt_tokens is not None and completion_tokens is not None
        else None
    )

    yield _event(
        "done",
        {
            "response": full_text,
            "latency_ms": round(latency_ms, 1),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "estimated_cost_usd": cost,
        },
    )


@router.post("/stream")
def chat_stream(payload: ChatRequest):
    if not payload.query.strip():
        raise HTTPException(400, "query must not be empty")
    return StreamingResponse(_stream_chat(payload.query), media_type="application/x-ndjson")


class EvaluateRequest(BaseModel):
    query: str
    response: str
    contexts: list[str]


@router.post("/evaluate", response_model=RagasScores)
def chat_evaluate(payload: EvaluateRequest):
    return evaluate_response(payload.query, payload.response, payload.contexts)
