# OmniRAG

A multi-strategy retrieval-augmented generation platform: hybrid (dense + sparse) retrieval
with RRF fusion and Cohere reranking, a lightweight query router, an adaptive retrieval loop,
real-time RAGAS evaluation, and a strategy comparison / benchmark UI. Positioned as a clinical
literature assistant for this build; the generation prompt is structured to retarget to other
domains (legal, enterprise, financial).

## Stack

- **Backend**: FastAPI (Python 3.12), FAISS + BM25 hybrid retrieval, Cohere Rerank, Groq
  (`llama-3.3-70b-versatile` for generation/routing-fallback, `llama-3.1-8b-instant` for the
  sufficiency check), RAGAS (evaluated by the same Groq model)
- **Frontend**: Next.js 16 (App Router), Tailwind CSS v4, shadcn/ui

## Local development

### Backend

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --loop asyncio
```

`--loop asyncio` is required — see [Known issues](#known-issues) below.

Copy `.env.example` (repo root) to `.env` and fill in `GROQ_API_KEY` / `COHERE_API_KEY`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Copy `frontend/.env.example` to `frontend/.env.local` (defaults already point at
`http://localhost:8000`).

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `GROQ_API_KEY` | backend | Groq API key (generation, routing fallback, sufficiency check, RAGAS judge) |
| `COHERE_API_KEY` | backend | Cohere API key (reranking) |
| `FRONTEND_URL` | backend | Comma-separated list of allowed CORS origins. Default `http://localhost:3000` |
| `DATA_DIR` | backend | Where the FAISS index / BM25 corpus / document registry persist. Default `backend/data/index` (self-contained, container-safe) |
| `NEXT_PUBLIC_API_URL` | frontend | URL of the backend API. Default `http://localhost:8000` |

No API keys are hardcoded anywhere in source — everything above is read via
`pydantic-settings` (backend) / `process.env` (frontend) with local-dev fallback defaults only.

## Known issues

- **`--loop asyncio` is required in every environment.** `ragas` calls `nest_asyncio.apply()`
  at import time, which cannot patch `uvloop`'s event loop — uvicorn's default loop
  implementation. Without this flag the app crashes on boot the moment `/chat/evaluate` (or
  anything importing `evaluation.ragas_eval`) is reached. This is baked into the Dockerfile's
  `CMD` already; if you invoke uvicorn any other way (e.g. a custom start script), keep the flag.
- **Groq free-tier daily token quota.** 100,000 tokens/day on `llama-3.3-70b-versatile` is easy
  to exhaust during heavy testing (adaptive retrieval, generation, and RAGAS evaluation all call
  Groq). Requests fail with a 429 until the daily window rolls over — not a bug in this app.

## Deployment

Not yet deployed — this section documents what's needed when you are ready.

### Backend → Railway

1. **New service, root directory = `backend/`.** Railway auto-detects the `Dockerfile` there
   and builds from it — no build/start command overrides needed (the `Dockerfile`'s `CMD`
   already binds to Railway's injected `$PORT` and uses `--loop asyncio`).
2. **Environment variables to set** (Railway → Variables): `GROQ_API_KEY`, `COHERE_API_KEY`,
   `FRONTEND_URL` (set this to your Vercel production URL once you have it — see the
   chicken-and-egg note below).
3. **Health check**: `/health`, already implemented and exercised by the Dockerfile's
   `HEALTHCHECK` directive; point Railway's own health check at the same path if it asks.
4. **Persistent storage — read this before relying on ingested documents.** Railway's
   container filesystem is ephemeral: every redeploy or restart wipes `backend/data/index`
   (the FAISS index, BM25 corpus, and document registry), silently losing every ingested
   document. Before going live, either:
   - attach a [Railway Volume](https://docs.railway.com/reference/volumes) mounted at a fixed
     path and set `DATA_DIR` to that mount path, or
   - treat the deployment as stateless/demo-only and re-ingest documents after each deploy.
   This wasn't fixed automatically because volume provisioning is a Railway-console action,
   not something expressible in code.
5. **Image size**: the `Dockerfile` explicitly installs the CPU-only PyTorch wheel before
   `requirements.txt` — plain `pip install torch` resolves to the CUDA-enabled build (3GB+
   larger) even with no GPU present, which would otherwise slow every build significantly.

### Frontend → Vercel

1. **New project, root directory = `frontend/`.** Vercel auto-detects Next.js; no config
   overrides needed (`next.config.ts` is already Vercel-ready — static output, no custom
   server, `poweredByHeader: false`).
2. **Environment variable**: `NEXT_PUBLIC_API_URL` = your Railway backend's public URL.
   Set it in Vercel → Settings → Environment Variables (`.env.local` is not deployed).
3. **Deployment order**: deploy the backend first to get its Railway URL for
   `NEXT_PUBLIC_API_URL`, then deploy the frontend to get its Vercel URL, then go back to
   Railway and set `FRONTEND_URL` to that Vercel URL so CORS allows it. `FRONTEND_URL` accepts
   a comma-separated list if you also add a custom domain later.
4. `npm run build` currently passes clean (TypeScript, ESLint, and the production build all
   succeed with no errors or warnings) — verified locally before this section was written.

### Not covered above

- No CI pipeline configured yet (tests currently run manually).
- No rate limiting / auth on the backend API — anyone with the Railway URL can call it.
