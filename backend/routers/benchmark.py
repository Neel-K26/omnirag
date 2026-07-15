import time
from statistics import mean

from fastapi import APIRouter

from benchmark import BENCHMARK_QUERIES
from generation.adaptive import adaptive_retrieve
from generation.generate import stream_answer
from models.schemas import BenchmarkQueryResult, BenchmarkRunResponse, RagasScores

router = APIRouter(prefix="/benchmark", tags=["benchmark"])


def _run_benchmark_query(query: str) -> BenchmarkQueryResult:
    start = time.perf_counter()
    result = adaptive_retrieve(query)
    answer = "".join(stream_answer(query, result.final_chunks))
    latency_ms = (time.perf_counter() - start) * 1000

    if result.final_chunks:
        # Imported lazily — see routers/chat.py's chat_evaluate for why (ragas costs ~300MB
        # at import time, the dominant memory cost in this app).
        from evaluation.ragas_eval import evaluate_response

        ragas = evaluate_response(query, answer, [c.text for c in result.final_chunks])
    else:
        ragas = RagasScores(faithfulness=0.0, answer_relevancy=0.0, context_precision=0.0)

    return BenchmarkQueryResult(
        query=query,
        answer=answer,
        routing=result.routing,
        num_hops=len(result.hops),
        latency_ms=round(latency_ms, 1),
        ragas=ragas,
    )


@router.get("/queries", response_model=list[str])
def get_benchmark_queries():
    return BENCHMARK_QUERIES


@router.post("/run", response_model=BenchmarkRunResponse)
def run_benchmark():
    results = [_run_benchmark_query(q) for q in BENCHMARK_QUERIES]
    aggregate = RagasScores(
        faithfulness=round(mean(r.ragas.faithfulness for r in results), 4),
        answer_relevancy=round(mean(r.ragas.answer_relevancy for r in results), 4),
        context_precision=round(mean(r.ragas.context_precision for r in results), 4),
    )
    aggregate_latency_ms = round(mean(r.latency_ms for r in results), 1)
    return BenchmarkRunResponse(results=results, aggregate=aggregate, aggregate_latency_ms=aggregate_latency_ms)
