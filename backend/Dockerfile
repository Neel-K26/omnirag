FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000
# Caps glibc's per-thread malloc arenas to reduce heap fragmentation/overhead — meaningful
# headroom on a memory-constrained instance (Render free tier: 512MB), at the cost of some
# malloc contention under concurrent load, which isn't a concern at this app's traffic level.
ENV MALLOC_ARENA_MAX=2
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# --loop asyncio is required: ragas's nest_asyncio.apply() (called at import time) cannot
# patch uvloop's event loop, which is uvicorn's default loop implementation — the app crashes
# on boot without this flag.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --loop asyncio"]
