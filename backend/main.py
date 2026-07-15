from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from routers import benchmark, chat, documents, retrieval
from warmup import warmup

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Blocking on purpose: the app won't start accepting connections — and Render's health
    # check at /health won't succeed — until this finishes. That's the point: it means a
    # cold-started instance only starts receiving real traffic once the slow part (loading
    # the local embedding model) is already done, instead of also making the first real
    # request pay for it.
    warmup()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(retrieval.router)
app.include_router(benchmark.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


@app.get("/warmup")
def warmup_endpoint():
    # Idempotent after the first call in a process's lifetime — the underlying singletons
    # are @lru_cache'd, so this is nearly instant unless something evicted them. Exists for
    # an external pinger to hit explicitly; the lifespan startup hook above already runs
    # this automatically on every cold start, so calling it isn't required for correctness.
    warmup()
    return {"status": "warm"}
