FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only torch explicitly first. Plain `pip install torch` on PyPI resolves to the
# CUDA-enabled wheel (~3GB+ larger) even on machines with no GPU — wasted weight for this
# CPU-only embedding workload (all-MiniLM-L6-v2). sentence-transformers (in requirements.txt)
# will then see torch already satisfied and won't pull the CUDA build over it.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download the embedding model at build time so it's baked into the image layer instead
# of being fetched (and potentially slow or flaky) on the first request at runtime.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# --loop asyncio is required: ragas's nest_asyncio.apply() (called at import time) cannot
# patch uvloop's event loop, which is uvicorn's default loop implementation — the app crashes
# on boot without this flag.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT} --loop asyncio"]
