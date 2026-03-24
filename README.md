# Ops Decision Engine

Ops Decision Engine is now organized as a clean full-stack workspace:

- **Backend:** FastAPI + ML/RAG decision engine
- **Frontend:** isolated Next.js demo dashboard UI

---

## Project Overview

- `app/` + `src/` power the backend decision services and pipelines.
- `frontend/` contains the UI app (dark operations dashboard, mocked simulation flow, analysis workspace).
- Backend and frontend are intentionally separated so they can evolve independently.

---

## Dataset Source

This project uses the Kaggle dataset:

- [Multilingual Customer Support Tickets](https://www.kaggle.com/datasets/tobiasbueck/multilingual-customer-support-tickets)

Expected source CSV location:

- `data/raw/aa_dataset-tickets-multi-lang-5-2-50-version.csv`

If your file name differs, update notebook/script paths accordingly.

---

## Folder Structure

```text
Ops Decision Engine/
├── app/                    # FastAPI backend entrypoints and schemas
├── src/                    # ML, RAG, and decision pipeline logic
├── artifacts/              # model/index/evaluation artifacts
├── data/                   # backend data assets
├── notebooks/              # analysis notebooks
├── outputs/                # generated backend outputs
├── scripts/                # helper scripts
├── tests/                  # backend/pipeline tests
├── frontend/               # isolated Next.js frontend app
│   ├── app/
│   ├── components/
│   ├── data/
│   ├── lib/
│   ├── types/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── postcss.config.mjs
├── requirements.txt
└── README.md
```

---

## Backend Setup and Run (FastAPI)

From repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Run API:

```powershell
uvicorn app.main:app --reload
```

Backend URLs:

- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

If using LLM generation endpoints:

```powershell
$env:OPENAI_API_KEY = "your-key-here"
```

---

## Frontend Setup and Run (Next.js)

From repo root:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

- Dashboard app: `http://localhost:3000`
- Dashboard route: `http://localhost:3000/dashboard`

---

## How to Test the UI

1. Start backend first:
  ```powershell
   uvicorn app.main:app --reload
  ```
2. In a second terminal, start frontend:
  ```powershell
   cd frontend
   npm run dev
  ```
3. 
  Open `http://localhost:3000/dashboard`.
4. Validate core flows:
  - **Simulation mode:** click **Start Simulation**, observe tickets entering stream over time.
  - **Speed control:** switch Slow/Normal/Fast and verify arrival cadence changes.
  - **Pause/Clear:** pause should stop arrivals; clear should reset stream and analysis.
  - **Ticket selection:** selecting a ticket shows loading, then analysis panels.
  - **Manual ticket mode:** open **Manual Ticket**, submit issue, verify it appears and runs analysis.
  - **Debug mode:** toggle debug to show/hide trace tabs.
5. API integration path (next phase):
  - Replace mocked analysis calls with backend requests to:
    - `POST /predict`
    - `POST /predict/debug`

---

## Current Status

- **Backend:** complete v1 (FastAPI decision engine + ML/RAG pipeline)
- **Frontend:** working demo UI in isolated `frontend/` app
- **Data mode:** currently mocked in UI; API integration mode is planned

---

## Model and LLM Scores

### Priority Model Training Scores

| Stage | Training script | Outputs folder | Approach (high level) | Accuracy | Macro F1 | Weighted F1 |
|---|---|---|---|---:|---:|---:|
| `baseline` | `src/ml/train_baseline.py` | `outputs/ml/baseline/` | TF-IDF (text-only) + Logistic Regression | 0.5471 | 0.5029 | 0.5336 |
| `stage2` | `src/ml/train_stage2.py` | `outputs/ml/stage2/` | TF-IDF (text-only, 1-2 grams) + Logistic Regression | 0.6196 | 0.6122 | 0.6211 |
| `stage3` | `src/ml/train_stage3.py` | `outputs/ml/stage3/` | TF-IDF (text) + OneHot(type, queue) + Logistic Regression | 0.6368 | 0.6301 | 0.6379 |
| `stage4` | `src/ml/train_stage4.py` | `outputs/ml/stage4/` | TF-IDF + OneHot(type, queue) + scaled engineered keyword features + Logistic Regression | 0.6334 | 0.6271 | 0.6342 |
| `stage5_svm` | `src/ml/train_stage5_svm.py` | `outputs/ml/stage5_svm/` | TF-IDF + OneHot(type, queue) + LinearSVC | 0.7111 | 0.7018 | 0.7110 |

### LLM and Pipeline Evaluation Outputs

Run:

```powershell
python -m tests.evaluate_pipeline
```

Evaluation output file:

- `artifacts/evaluation/pipeline_evaluation_results.csv`

This report includes per-case outputs such as:

- ML priority prediction
- Rule-based recommended priority
- LLM priority extracted from generated output
- Confidence score / confidence level
- Escalation recommendation and evidence metrics

---

## Troubleshooting

- **Frontend dependencies missing**
  - Run:
    ```powershell
    cd frontend
    npm install
    ```
- **Backend not running**
  - Ensure venv is active and run:
    ```powershell
    uvicorn app.main:app --reload
    ```
- **CORS errors (when UI calls API)**
  - Configure FastAPI CORS middleware to allow `http://localhost:3000`.
- **Bad API URL in frontend**
  - Verify frontend base URL points to `http://127.0.0.1:8000`.
- **Import/path errors in frontend**
  - Confirm you run commands inside `frontend/`.
  - Ensure alias imports use `@/` and `frontend/tsconfig.json` is present.

