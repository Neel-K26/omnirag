from fastapi.testclient import TestClient

from main import app
from retrieval import hybrid

client = TestClient(app)


def test_compare_strategies_end_to_end(monkeypatch, populated_store):
    monkeypatch.setattr(hybrid, "get_vector_store", lambda: populated_store)

    resp = client.post("/retrieval/compare", json={"query": "What treats high blood pressure?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "What treats high blood pressure?"
    assert len(body["results"]) == 4

    strategies = {r["strategy"] for r in body["results"]}
    assert strategies == {"dense", "sparse", "hybrid", "hybrid_rerank"}

    for r in body["results"]:
        assert r["latency_ms"] > 0
        assert r["answer"]
        assert len(r["chunks"]) > 0
        assert 0.0 <= r["ragas"]["faithfulness"] <= 1.0
        assert 0.0 <= r["ragas"]["answer_relevancy"] <= 1.0
        assert 0.0 <= r["ragas"]["context_precision"] <= 1.0


def test_compare_strategies_rejects_empty_query():
    resp = client.post("/retrieval/compare", json={"query": "   "})
    assert resp.status_code == 400
