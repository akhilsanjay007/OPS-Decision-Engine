import os
import time
import traceback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import PredictRequest, PredictResponse, PredictDebugResponse
from app.service import OpsDecisionService, ResourcesNotReadyError

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


app = FastAPI(
    title="Ops Decision Engine API",
    version="1.0.0",
    description="Hybrid ML + RAG + LLM incident triage backend",
)
app.state.resource_manager = OpsDecisionService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=_parse_allowed_origins(),
    # Browsers disallow `Access-Control-Allow-Credentials: true` with `*` origins.
    allow_credentials=False if os.getenv("ALLOWED_ORIGINS", "*").strip() == "*" else True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def start_background_init() -> None:
    # Launch warmup asynchronously so the server can bind the port immediately.
    app.state.resource_manager.start_background_initialization()


@app.get("/")
def root():
    return {
        "message": "Ops Decision Engine API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return app.state.resource_manager.health()


@app.post("/predict", response_model=PredictResponse)
def predict(payload: PredictRequest):
    request_start = time.perf_counter()
    print(
        "[INFO] /predict request started "
        f"(type={payload.type!r}, queue={payload.queue!r}, issue_chars={len(payload.issue)})"
    )
    try:
        result = app.state.resource_manager.predict(
            issue=payload.issue,
            ticket_type=payload.type,
            queue=payload.queue,
        )
        return result
    except ResourcesNotReadyError as e:
        print(f"[WARN] /predict requested before resources ready: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[ERROR] /predict failed: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        total_ms = (time.perf_counter() - request_start) * 1000
        print(f"[TIMING] endpoint=/predict total_request_ms={total_ms:.2f}")


@app.post("/predict/debug", response_model=PredictDebugResponse)
def predict_debug(payload: PredictRequest):
    try:
        return app.state.resource_manager.predict_debug(
            issue=payload.issue,
            ticket_type=payload.type,
            queue=payload.queue,
        )
    except ResourcesNotReadyError as e:
        print(f"[WARN] /predict/debug requested before resources ready: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        print(f"[ERROR] /predict/debug failed: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))