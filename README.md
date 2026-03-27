# Ops Decision Engine

Monorepo for the Ops Decision Engine: a **FastAPI** backend (ML + RAG + LLM) and a **Next.js** operations dashboard.

---

## Repository layout

```text
Ops Decision Engine/
├── backend/                 # Python API, pipelines, tests, runtime assets
│   ├── app/                 # FastAPI (routes, schemas, service)
│   ├── src/                 # ML, RAG, decision pipeline
│   ├── tests/               # Backend tests
│   ├── models/              # Deployed priority model (joblib)
│   ├── data/                # Chroma vector DB + processed RAG JSONL (see .gitignore)
│   ├── artifacts/           # Training outputs, evaluation CSVs (typically gitignored)
│   ├── notebooks/         # Analysis notebooks (gitignored by default)
│   ├── outputs/             # Generated outputs (gitignored)
│   ├── scripts/             # Helper scripts
│   ├── requirements.txt
│   └── .env.example         # Env var template (copy to `.env` in backend/)
├── frontend/                # Next.js UI
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   └── ...
├── .env.example             # Template for root `.env` (Docker Compose, shared secrets)
├── docker-compose.yml       # Run backend + frontend in Docker with env from root `.env`
├── .gitignore
└── README.md
```

---

## Dataset

Training and RAG preparation use the **Multilingual Customer Support Tickets** dataset. The canonical raw export used in this project is **`aa_dataset-tickets-multi-lang-5-2-50-version.csv`**.

- **Kaggle (source):** [Multilingual Customer Support Tickets](https://www.kaggle.com/datasets/tobiasbueck/multilingual-customer-support-tickets?select=aa_dataset-tickets-multi-lang-5-2-50-version.csv)
- **Hugging Face (mirror):** [Tobi-Bueck/customer-support-tickets](https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets)

After download, place the CSV under **`backend/data/raw/`** for the notebooks and training scripts (that folder stays out of git for size).

---

## Model performance (priority classifier)

All rows use the **same held-out test set** (**n = 3,268**), three-class priority (**HIGH / MEDIUM / LOW**). Metrics come from `backend/outputs/ml/<run>/metrics.json`; per-class precision/recall/F1 are in the matching `classification_report.json`.

### Comparison across training stages

| Approach | Accuracy | Macro F1 | Weighted F1 |
|----------|----------|----------|-------------|
| Baseline | 54.7% | 0.503 | 0.534 |
| Stage 2 | 62.0% | 0.612 | 0.621 |
| Stage 3 | 63.7% | 0.630 | 0.638 |
| Stage 4 | 63.3% | 0.627 | 0.634 |
| **Stage 5 (LinearSVC)** — **deployed** | **71.1%** | **0.702** | **0.711** |

Stage 5 improves over the baseline by **~16.4 points** accuracy and **~0.20** macro F1 on this split. The API loads **`models/priority_stage5_svm_pipeline.joblib`** by default (`MODEL_PATH`).

---

## End-to-end pipeline evaluation

This runs **predict → retrieve → rerank → LLM decision** on fixed **test scenarios** (not the REST API). Requires **`OPENAI_API_KEY`**.

From **`backend/`**:

```powershell
python -m tests.evaluate_pipeline
```

Writes **`backend/artifacts/evaluation/pipeline_evaluation_results.csv`** and prints per-case fields (ML priority, rule-based recommendation, LLM priority, confidence, escalation, etc.) plus a short summary.

**Retrieval-only** (embedding + Chroma, no LLM):

```powershell
cd backend
python -m tests.test_retrieval
```

VS Code tasks **Tests: evaluate pipeline** and **Tests: retrieval** use **`backend/`** as the working directory.

---

## Backend (FastAPI)

### Environment variables

| Variable | Required for startup | Purpose |
|----------|----------------------|---------|
| `OPENAI_API_KEY` | No | Full LLM-generated triage (`/predict`). If unset, the API still runs; ML + RAG run, and LLM-shaped fields use a safe fallback message. |
| `OPENAI_MODEL` | No | OpenAI chat model (default `gpt-4o-mini`). |
| `MODEL_PATH` | No | Joblib priority pipeline (see paths table below). |
| `CHROMA_DIR` or `CHROMA_DB_DIR` | No | Chroma persistence directory. |
| `KB_PATH` | No | JSONL knowledge base for index rebuild scripts. |
| `ALLOWED_ORIGINS` | No | CORS allowlist (`*` or comma-separated origins). Used by `backend/app/main.py`. |

At startup the backend logs whether `OPENAI_API_KEY` is set, the resolved `MODEL_PATH`, `CHROMA_DIR`, and `KB_PATH`. `GET /health` includes `openai_configured` and `openai_model`.

### Runtime paths (environment variables)

With **`APP_HOME=/app`** (Docker), paths default under `/app/`. For **local** runs, `src/core/config.py` defaults `APP_HOME` to `/app` unless you set **`APP_HOME`** to the absolute path of your `backend` directory (or use absolute `MODEL_PATH` / `CHROMA_DIR` / `KB_PATH`).

| Variable | Default (container / typical) | Purpose |
|----------|-------------------------------|---------|
| `MODEL_PATH` | `models/priority_stage5_svm_pipeline.joblib` | ML priority pipeline |
| `CHROMA_DIR` or `CHROMA_DB_DIR` | `data/chroma` | Persisted Chroma vector store |
| `KB_PATH` | `data/processed/rag_knowledge_base.jsonl` | RAG knowledge base (JSONL) |

**Local uvicorn:** copy `backend/.env.example` to `backend/.env` and adjust values.

**Docker Compose:** copy **root** `.env.example` to `.env` at the repository root (same folder as `docker-compose.yml`), set `OPENAI_API_KEY` when you want LLM output, optionally set `NEXT_PUBLIC_API_BASE_URL` if the API is not on `http://localhost:8000`, then run compose (see below).

### Install and run

From the **repository root**:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Run the API **from `backend/`** so imports resolve correctly:

```powershell
cd backend
uvicorn app.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

```powershell
$env:OPENAI_API_KEY = "your-key-here"
# optional:
$env:OPENAI_MODEL = "gpt-4o-mini"
```

### Run with Docker Compose (full stack)

From the **repository root**:

1. Create `.env` from the template and set variables as needed:

   ```powershell
   copy .env.example .env
   ```

   Edit `.env`:

   - **`OPENAI_API_KEY`** — set when you want full LLM-generated triage (leave empty for ML+RAG-only fallback on `/predict`).
   - **`OPENAI_MODEL`** — optional; defaults to `gpt-4o-mini` in Compose if unset.
   - **`NEXT_PUBLIC_API_BASE_URL`** — optional; defaults to `http://localhost:8000`. The browser uses this URL to call the API (appropriate when the stack is published on `localhost` with port mapping).

2. Build and start **backend** and **frontend**:

   ```powershell
   docker compose up --build
   ```

3. Open the apps:

   - **Frontend:** [http://localhost:3000](http://localhost:3000) — dashboard at [http://localhost:3000/dashboard](http://localhost:3000/dashboard).
   - **Backend:** [http://localhost:8000/docs](http://localhost:8000/docs), [http://localhost:8000/health](http://localhost:8000/health).

Compose reads the root `.env` for variable substitution. The backend service sets `APP_HOME`, `MODEL_PATH`, `CHROMA_DIR`, `KB_PATH`, `ALLOWED_ORIGINS=http://localhost:3000`, and OpenAI-related variables. The frontend image is built with `NEXT_PUBLIC_API_BASE_URL` so client-side requests target the API. The `backend/data/chroma` folder is mounted at `/app/data/chroma` for persistence. Both services use `restart: unless-stopped`.

### Deploy backend on Render

The repo now includes `render.yaml` for a one-click backend deployment blueprint.

1. Push this repository to GitHub.
2. In Render, create a new **Blueprint** service and point it at the repo.
3. Render reads `render.yaml` and creates `ops-decision-engine-backend` from `backend/Dockerfile`.
4. In the Render dashboard, set:
   - `OPENAI_API_KEY` (required for full LLM-generated triage; optional for ML + RAG fallback mode)
   - `ALLOWED_ORIGINS` (set this to your frontend URL instead of `*` in production)
5. Deploy and verify:
   - `GET /health` returns `status: "ok"` once startup completes.
   - Use the Render service URL with `/docs` to test the API.

Notes:
- The container startup command now respects Render's dynamic `PORT` environment variable.
- Chroma data is stored in `/app/data/chroma` inside the container. On Render, attach a persistent disk if you need index persistence across deploys/restarts.

### Tests

```powershell
cd backend
python -m pip install pytest
python -m pytest
```

---

## Frontend (Next.js)

From **repository root**:

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

In `frontend/.env.local` (or root `.env` when using Compose for the frontend build):

- **`NEXT_PUBLIC_API_BASE_URL`** — Base URL of the FastAPI app (e.g. `http://localhost:8000`). If unset, the UI defaults to `http://localhost:8000`. All API calls go through `getApiBaseUrl()` in `frontend/lib/config.ts` (no hardcoded backend URLs in components).

The dashboard calls **`POST /predict`** or **`POST /predict/debug`** (when debug mode is on). Start the **backend** first. Set **`OPENAI_API_KEY`** (and optionally **`OPENAI_MODEL`**) for full LLM-written analysis; without a key, the API still returns ML priority, evidence, and fallback text for LLM-shaped fields.

- App: `http://localhost:3000`
- Dashboard: `http://localhost:3000/dashboard`

---

## Local dev: backend + frontend

1. Terminal A — backend:
   ```powershell
   cd backend
   uvicorn app.main:app --reload
   ```
2. Terminal B — frontend:
   ```powershell
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:3000/dashboard`.

---

## Troubleshooting

- **Imports fail when running uvicorn** — Run commands with **`backend/`** as the current working directory.
- **Frontend cannot reach API** — Confirm `NEXT_PUBLIC_API_BASE_URL` (build-time for Docker images) and that the backend is listening. Docker Compose sets `ALLOWED_ORIGINS=http://localhost:3000` on the backend for the default layout.
- **Large Chroma files** — Vector DB under `backend/data/chroma/` may use **Git LFS** (see `.gitattributes`). Install [Git LFS](https://git-lfs.com/) and run `git lfs install` before clone/pull.
