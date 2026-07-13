# OmniRAG

A multi-strategy retrieval-augmented generation platform: hybrid (dense + sparse) retrieval
with RRF fusion and Cohere reranking, a lightweight query router, an adaptive retrieval loop,
real-time RAGAS evaluation, and a strategy comparison / benchmark UI. Positioned as a clinical
literature assistant for this build; the generation prompt is structured to retarget to other
domains (legal, enterprise, financial).

## Stack

- **Backend**: FastAPI (Python 3.12), FAISS + BM25 hybrid retrieval, Cohere Rerank, Gemini
  (`gemini-flash-lite-latest` for generation, routing fallback, and the sufficiency check),
  RAGAS (evaluated by the same Gemini model, via a small custom `BaseRagasLLM` wrapper —
  see [Known issues](#known-issues))
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

Copy `.env.example` (repo root) to `.env` and fill in `GEMINI_API_KEY` / `COHERE_API_KEY`.

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
| `GEMINI_API_KEY` | backend | Gemini API key (generation, routing fallback, sufficiency check, RAGAS judge) |
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
- **Gemini model availability varies by API key/project, not just by model name.** During
  migration, `gemini-2.5-flash` (Google's currently-listed stable flash model) returned a hard
  404 "no longer available to new users" for this project's key, and dated IDs like
  `gemini-2.0-flash` returned a 429 with an explicit `limit: 0` free-tier quota — not a
  transient rate limit, a permanent zero allocation for that model on this project. The
  `gemini-flash-lite-latest` alias (currently resolving to `gemini-3.1-flash-lite`) was the
  one tier confirmed working. If you swap in your own API key, re-verify model access before
  assuming `gemini-flash-lite-latest` is the right (or only working) choice for your project.
- **No `langchain-google-genai` in requirements.txt.** Every version compatible with the
  pinned pre-1.0 `langchain-core` band (required by `ragas==0.2.15`) depends on the legacy
  `google-ai-generativelanguage` client, which rejected this project's API key outright in
  testing (both gRPC and REST transport). Every version using the modern, working `google-genai`
  SDK requires `langchain-core>=1.0`, which breaks `ragas`'s own imports — the same class of
  conflict documented above for the RAGAS/langchain stack generally. The RAGAS judge instead
  implements `ragas`'s own `BaseRagasLLM` interface directly against `google-genai`
  (`evaluation/ragas_eval.py`), the same pattern already used on the embeddings side to avoid
  an equivalent `langchain_huggingface` conflict.
- **Gemini free-tier rate limits.** Requests can still be throttled or quota-exhausted during
  heavy testing (adaptive retrieval, generation, and RAGAS evaluation all call Gemini) — not a
  bug in this app.

## Deployment

Not yet deployed — this section documents what's needed when you are ready.

### Backend → Railway

1. **New service, root directory = `backend/`.** Railway auto-detects the `Dockerfile` there
   and builds from it — no build/start command overrides needed (the `Dockerfile`'s `CMD`
   already binds to Railway's injected `$PORT` and uses `--loop asyncio`).
2. **Environment variables to set** (Railway → Variables): `GEMINI_API_KEY`, `COHERE_API_KEY`,
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
