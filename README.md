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
copy .env.example .env.local
npm run dev
```

Configure the dashboard API target in `frontend/.env.local`:

- **`NEXT_PUBLIC_API_URL`** — Base URL of the FastAPI app (e.g. `http://localhost:8000`). If unset, the UI defaults to `http://localhost:8000`.

The analysis workspace calls:

- **`POST /predict`** when debug mode is off
- **`POST /predict/debug`** when debug mode is on

**Important:** Start the backend before selecting a ticket or submitting a manual ticket; analysis requests are sent to the live API. The decision pipeline uses the LLM layer: set **`OPENAI_API_KEY`** in the backend environment (see above) or `/predict` may return an error; the dashboard will show the API error message.

Frontend URL:

- Dashboard app: `http://localhost:3000`
- Dashboard route: `http://localhost:3000/dashboard`

---

## How to Test the UI

1. Start backend first:
  ```powershell
   uvicorn app.main:app --reload
  ```
2. In a second terminal, start frontend (with `NEXT_PUBLIC_API_URL` pointing at that API if it is not on `http://localhost:8000`):
  ```powershell
   cd frontend
   npm run dev
  ```
3. Open `http://localhost:3000/dashboard`.
4. Validate core flows:
  - **Simulation mode:** click **Start Simulation**, observe tickets entering stream over time (stream remains mocked/local).
  - **Speed control:** switch Slow/Normal/Fast and verify arrival cadence changes.
  - **Pause/Clear:** pause should stop arrivals; clear should reset stream and analysis.
  - **Ticket selection:** selecting a ticket shows loading, then live analysis from the backend.
  - **Manual ticket mode:** open **Manual Ticket**, submit an issue (at least 5 characters, per API validation), verify it appears and runs analysis.
  - **Debug mode:** toggle debug so requests use `/predict/debug` and the **Debug Trace** tabs show retrieval and prompt data from the backend.

---

## Current Status

- **Backend:** complete v1 (FastAPI decision engine + ML/RAG pipeline)
- **Frontend:** Next.js dashboard with live analysis integration; incident simulation stream remains mock-driven

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
  - The bundled backend uses permissive CORS (`allow_origins=["*"]`). If you tighten CORS in `app/main.py`, add your frontend origin (e.g. `http://localhost:3000`) to the allowed list.
- **Bad API URL in frontend**
  - Verify frontend base URL points to `http://127.0.0.1:8000`.
- **Import/path errors in frontend**
  - Confirm you run commands inside `frontend/`.
  - Ensure alias imports use `@/` and `frontend/tsconfig.json` is present.

