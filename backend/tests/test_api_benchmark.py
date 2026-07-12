from fastapi.testclient import TestClient

from main import app
from retrieval import hybrid
import routers.benchmark as benchmark_router
import benchmark as benchmark_module

client = TestClient(app)


def test_get_benchmark_queries_returns_ten_presets():
    resp = client.get("/benchmark/queries")
    assert resp.status_code == 200
    queries = resp.json()
    assert len(queries) == 10
    assert queries == benchmark_module.BENCHMARK_QUERIES


def test_run_benchmark_end_to_end(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)
    # Full pipeline runs Groq calls per query (sufficiency + generation + RAGAS judge) —
    # trim to 2 presets here to prove correctness without burning the full 10-query quota.
    monkeypatch.setattr(benchmark_router, "BENCHMARK_QUERIES", benchmark_module.BENCHMARK_QUERIES[:2])

    resp = client.post("/benchmark/run")
    assert resp.status_code == 200
    body = resp.json()

    assert len(body["results"]) == 2
    for r in body["results"]:
        assert r["query"] in benchmark_module.BENCHMARK_QUERIES[:2]
        assert r["answer"]
        assert r["latency_ms"] > 0
        assert r["num_hops"] >= 1
        assert 0.0 <= r["ragas"]["faithfulness"] <= 1.0

    agg = body["aggregate"]
    expected_faithfulness = (body["results"][0]["ragas"]["faithfulness"] + body["results"][1]["ragas"]["faithfulness"]) / 2
    assert agg["faithfulness"] == round(expected_faithfulness, 4)
    assert body["aggregate_latency_ms"] > 0
