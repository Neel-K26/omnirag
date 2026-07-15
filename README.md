# OmniRAG

A multi-strategy retrieval-augmented generation platform: hybrid (dense + sparse) retrieval
with RRF fusion and Cohere reranking, a lightweight query router, an adaptive retrieval loop,
real-time RAGAS evaluation, and a strategy comparison / benchmark UI. Positioned as a clinical
literature assistant for this build; the generation prompt is structured to retarget to other
domains (legal, enterprise, financial).

## Stack

- **Backend**: FastAPI (Python 3.12), FAISS + BM25 hybrid retrieval, Cohere (reranking +
  `embed-english-light-v3.0` for embeddings — no local ML model, see
  [Known issues](#known-issues)), Gemini (`gemini-flash-lite-latest` for generation, routing
  fallback, and the sufficiency check), RAGAS (evaluated by the same Gemini model, via a small
  custom `BaseRagasLLM` wrapper)
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
`http://localhost:8000`) — note, however, that `NEXT_PUBLIC_API_URL` is currently
hardcoded in `frontend/next.config.ts` and will ignore this file; see that file's comment.

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | backend | Gemini API key (generation, routing fallback, sufficiency check, RAGAS judge) |
| `COHERE_API_KEY` | backend | Cohere API key (reranking + embeddings) |
| `FRONTEND_URL` | backend | Comma-separated list of allowed CORS origins. Default `http://localhost:3000` |
| `DATA_DIR` | backend | Where the FAISS index / BM25 corpus / document registry persist. Default `backend/data/index` (self-contained, container-safe) |
| `NEXT_PUBLIC_API_URL` | frontend | URL of the backend API. **Currently hardcoded as a build-time constant in `frontend/next.config.ts`** — editing this file, `.env.local`, or Vercel's dashboard has no effect until that hardcode is changed or removed. See that file's comment for why. |

No API keys are hardcoded anywhere in source — everything above is read via
`pydantic-settings` (backend) / `process.env` (frontend) with local-dev fallback defaults,
except `NEXT_PUBLIC_API_URL` as noted.

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
- **Render free tier spins the backend down after ~15 minutes of inactivity.** The first
  request after that hits a cold start; Render's proxy returns 502 before the app is even up
  to attach CORS headers, which browsers report as a CORS error rather than a 502 — confusing,
  but not actually a CORS misconfiguration. Two mitigations: `frontend/lib/api.ts`'s
  `fetchWithRetry` retries once after a 3s wait on a 502; `.github/workflows/keep-alive.yml`
  pings `/health` every 10 minutes to keep the instance from spinning down at all — **this is
  the part that actually prevents spin-down**; Render's own dashboard "Health Check Path"
  setting (see below) affects deploy-readiness and auto-restart-on-failure, not free-tier
  inactivity spin-down.
- **Render free tier's 512MB RAM limit ruled out local embeddings entirely.** This app
  originally used a local sentence-transformers model for embeddings. Measured RSS once that
  model was actually used (import + weights + one `encode()` call): ~630MB — over the limit
  regardless of lazy-loading, since chat always needs at least a query embedding, so the
  process would get OOM-killed (not a graceful per-request failure — Render kills the whole
  container, taking down every in-flight request) the moment anyone sent a real chat message.
  Switched to Cohere's `embed-english-light-v3.0` API instead (see `ingestion/embeddings.py`)
  — zero local model, at the cost of a network call on every embed (ingestion and every
  query's retrieval step). Measured post-migration: ~196MB at boot, ~199MB after a chat query,
  ~362MB even in the worst case (a RAGAS evaluation call, which also imports `ragas` — see
  next point). Also worth knowing if you profile this yourself: `ragas` (+ its
  `langchain_openai` transitive dependency, which our code never calls directly — `ragas`
  imports it internally) costs ~300MB at import time, more than the entire former local
  embedding stack combined. `routers/chat.py`, `routers/retrieval.py`, and
  `routers/benchmark.py` import `evaluate_response` lazily inside their handler functions
  rather than at module level for exactly this reason — otherwise that cost would be paid at
  every process boot regardless of whether evaluation is ever used, the same class of problem
  local embeddings had.

## Deployment

Backend on Render, frontend on Vercel.

### Backend → Render

1. **Web service, root directory = `backend/`.** Render auto-detects the `Dockerfile` there.
2. **Environment variables to set** (Render dashboard → Environment): `GEMINI_API_KEY`,
   `COHERE_API_KEY`, `FRONTEND_URL` (your Vercel production URL).
3. **Health check**: in the Render dashboard, set **Health Check Path** to `/health` (Settings →
   Health & Alerts, or wherever your Render UI surfaces it). This affects deploy-readiness and
   auto-restart-on-failure — it does **not** prevent free-tier spin-down from inactivity, which
   is what `.github/workflows/keep-alive.yml` is for instead (see Known Issues above).
4. **Persistent storage — read this before relying on ingested documents.** Render's container
   filesystem is ephemeral: every redeploy or restart wipes `backend/data/index` (the FAISS
   index, BM25 corpus, and document registry), silently losing every ingested document. Before
   going live, either attach a [Render Disk](https://render.com/docs/disks) mounted at a fixed
   path and set `DATA_DIR` to that mount path, or treat the deployment as stateless/demo-only
   and re-ingest documents after each deploy/spin-down cycle.
5. **Memory**: see the 512MB RAM note under Known Issues above — this matters more than image
   size on Render's free tier. `MALLOC_ARENA_MAX=2` is set in the Dockerfile to reduce glibc
   heap fragmentation overhead on top of the embeddings-provider fix.

### Frontend → Vercel

1. **New project, root directory = `frontend/`.** Vercel auto-detects Next.js.
2. **`NEXT_PUBLIC_API_URL`** is currently hardcoded as a build-time constant in
   `frontend/next.config.ts` (see that file's comment for why) — setting it in Vercel's
   dashboard, `.env.local`, or anywhere else has no effect until that hardcode is changed.
3. **CORS**: after deploying the frontend, set the backend's `FRONTEND_URL` (Render dashboard)
   to the resulting Vercel URL so CORS allows it. Accepts a comma-separated list if you add a
   custom domain later.
4. `npm run build` currently passes clean (TypeScript, ESLint, and the production build all
   succeed with no errors or warnings) — verified locally before this section was written.

### Not covered above

- No CI pipeline configured yet (tests currently run manually).
- No rate limiting / auth on the backend API — anyone with the Render URL can call it.
