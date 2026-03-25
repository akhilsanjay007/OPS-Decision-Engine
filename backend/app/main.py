import os
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import PredictRequest, PredictResponse, PredictDebugResponse
from app.service import service

def _parse_allowed_origins() -> list[str]:
    """
    Parse ALLOWED_ORIGINS.

    - `*` enables all origins
    - comma-separated list enables only those origins
    """
    raw = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if raw == "*" or raw == "":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Load model, embedding model, and initialize Chroma before serving requests.
    service.startup()
    yield


app = FastAPI(
    title="Ops Decision Engine API",
    version="1.0.0",
    description="Hybrid ML + RAG + LLM incident triage backend",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    # Browsers disallow `Access-Control-Allow-Credentials: true` with `*` origins.
    allow_credentials=False if os.getenv("ALLOWED_ORIGINS", "*").strip() == "*" else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Ops Decision Engine API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return service.health()


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    try:
        return service.predict(
            issue=payload.issue,
            ticket_type=payload.type,
            queue=payload.queue,
        )
    except Exception as e:
        print(f"[ERROR] /predict failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/debug", response_model=PredictDebugResponse)
def predict_debug(payload: PredictRequest):
    try:
        return service.predict_debug(
            issue=payload.issue,
            ticket_type=payload.type,
            queue=payload.queue,
        )
    except Exception as e:
        print(f"[ERROR] /predict/debug failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))