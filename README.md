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

