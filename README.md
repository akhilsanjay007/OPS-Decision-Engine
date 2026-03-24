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

### Runtime paths (environment variables)

All paths are resolved relative to the **`backend/`** directory unless set to an absolute path.

| Variable        | Default (under `backend/`)                         | Purpose                          |
|----------------|-----------------------------------------------------|----------------------------------|
| `MODEL_PATH`   | `models/priority_stage5_svm_pipeline.joblib`       | ML priority pipeline             |
| `CHROMA_DB_DIR`| `data/chroma`                                      | Persisted Chroma vector store    |
| `KB_PATH`      | `data/processed/rag_knowledge_base.jsonl`          | RAG knowledge base (JSONL)       |

Optional: copy `backend/.env.example` to `backend/.env` and set values. For LLM generation, set **`OPENAI_API_KEY`**.

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
```

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

In `frontend/.env.local`:

- **`NEXT_PUBLIC_API_URL`** — Base URL of the FastAPI app (e.g. `http://localhost:8000`). If unset, the UI defaults to `http://localhost:8000`.

The dashboard calls **`POST /predict`** or **`POST /predict/debug`** (when debug mode is on). Start the **backend** first; set **`OPENAI_API_KEY`** on the backend for successful analysis responses.

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
- **Frontend cannot reach API** — Confirm `NEXT_PUBLIC_API_URL` and that the backend is listening. If you restrict CORS in `backend/app/main.py`, allow the frontend origin (e.g. `http://localhost:3000`).
- **Large Chroma files** — Vector DB under `backend/data/chroma/` may use **Git LFS** (see `.gitattributes`). Install [Git LFS](https://git-lfs.com/) and run `git lfs install` before clone/pull.
