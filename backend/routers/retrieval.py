import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from generation.generate import stream_answer
from models.schemas import RagasScores, RetrievalStrategy, StrategyResult
from retrieval.hybrid import retrieve

router = APIRouter(prefix="/retrieval", tags=["retrieval"])

TOP_K = 5


class CompareRequest(BaseModel):
    query: str


class CompareResponse(BaseModel):
    query: str
    results: list[StrategyResult]


def _run_strategy(query: str, strategy: RetrievalStrategy) -> StrategyResult:
    start = time.perf_counter()
    retrieved = retrieve(query, strategy=strategy, top_k=TOP_K)
    chunks = [c for c, _ in retrieved]
    answer = "".join(stream_answer(query, chunks))
    latency_ms = (time.perf_counter() - start) * 1000

    if chunks:
        # Imported lazily — see routers/chat.py's chat_evaluate for why (ragas costs ~300MB
        # at import time, the dominant memory cost in this app).
        from evaluation.ragas_eval import evaluate_response

        ragas = evaluate_response(query, answer, [c.text for c in chunks])
    else:
        ragas = RagasScores(faithfulness=0.0, answer_relevancy=0.0, context_precision=0.0)

    return StrategyResult(
        strategy=strategy,
        latency_ms=round(latency_ms, 1),
        answer=answer,
        chunks=chunks,
        ragas=ragas,
    )


@router.post("/compare", response_model=CompareResponse)
def compare_strategies(payload: CompareRequest):
    if not payload.query.strip():
        raise HTTPException(400, "query must not be empty")
    results = [_run_strategy(payload.query, strategy) for strategy in RetrievalStrategy]
    return CompareResponse(query=payload.query, results=results)
