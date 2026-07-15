from fastapi.testclient import TestClient

from ingestion.embeddings import get_embedding_model
from main import app
from warmup import warmup


def test_warmup_loads_the_embedding_model():
    get_embedding_model.cache_clear()
    assert get_embedding_model.cache_info().currsize == 0

    warmup()

    assert get_embedding_model.cache_info().currsize == 1


def test_warmup_is_idempotent():
    warmup()
    warmup()  # should not raise or reload anything


def test_app_lifespan_runs_warmup_on_startup():
    # Only entering TestClient as a context manager actually triggers FastAPI's lifespan
    # (startup/shutdown) — plain TestClient(app) used elsewhere in this suite does not.
    get_embedding_model.cache_clear()
    with TestClient(app) as client:
        assert get_embedding_model.cache_info().currsize == 1
        resp = client.get("/health")
        assert resp.status_code == 200


def test_warmup_endpoint():
    with TestClient(app) as client:
        resp = client.get("/warmup")
        assert resp.status_code == 200
        assert resp.json() == {"status": "warm"}
