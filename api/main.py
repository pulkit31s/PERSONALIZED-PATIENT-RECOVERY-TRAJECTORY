"""
FastAPI application for ICU Recovery Trajectory predictions.
All predictions use mock/synthetic data — NOT clinical.
"""
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse

from api.schemas import PredictionRequest, PredictionResponse
from src.serving.prediction_pipeline import PredictionPipeline
from src.serving.validation import (
    StayNotFoundError, InvalidPredictionTimeError, ArtifactLoadError
)
from src.serving.artifacts import ArtifactLoader

logger = logging.getLogger(__name__)

pipeline = PredictionPipeline()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load artifacts during startup
    try:
        pipeline.artifact_loader.load_model_manifest()
        logger.info("Successfully loaded artifacts during startup.")
    except Exception as e:
        logger.error(f"Failed to load artifacts during startup: {e}")
    yield
    # Cleanup if needed

app = FastAPI(
    title="ICU Recovery Trajectory API",
    description="Mock prediction service for ICU patient recovery. All data is synthetic.",
    version="0.1.0",
    lifespan=lifespan
)


@app.exception_handler(StayNotFoundError)
async def stay_not_found_handler(request: Request, exc: StayNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "stay_not_found", "detail": str(exc)}
    )

@app.exception_handler(InvalidPredictionTimeError)
async def invalid_prediction_time_handler(request: Request, exc: InvalidPredictionTimeError):
    return JSONResponse(
        status_code=422,
        content={"error": "invalid_prediction_time", "detail": str(exc)}
    )

@app.exception_handler(ArtifactLoadError)
async def artifact_load_error_handler(request: Request, exc: ArtifactLoadError):
    return JSONResponse(
        status_code=503,
        content={"error": "artifact_load_error", "detail": str(exc)}
    )

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    return JSONResponse(
        status_code=503,
        content={"error": "artifact_not_found", "detail": str(exc)}
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("An unexpected error occurred.")
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."}
    )

@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "icu-recovery-trajectory",
        "version": "0.1.0",
        "mock_mode": True
    }

@app.get("/model-metadata")
async def model_metadata() -> Dict[str, Any]:
    try:
        return pipeline.artifact_loader.load_model_manifest()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest = Body(
        openapi_examples={
            "basic": {
                "summary": "Basic prediction request",
                "value": {
                    "stay_id": "mock_stay_001",
                    "prediction_time": "2026-01-01T18:00:00Z",
                    "include_explanations": True
                }
            }
        }
    )
) -> PredictionResponse:
    """Make predictions using mock/synthetic data."""
    return pipeline.predict(
        stay_id=request.stay_id,
        prediction_time=request.prediction_time,
        include_explanations=request.include_explanations
    )
