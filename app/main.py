from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback

from app.schemas import PredictRequest, PredictResponse
from app.service import service

app = FastAPI(
    title="Ops Decision Engine API",
    version="1.0.0",
    description="Hybrid ML + RAG + LLM incident triage backend",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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