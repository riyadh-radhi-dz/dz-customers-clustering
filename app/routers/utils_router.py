"""API router for predictions and model management."""
import logging

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.schemas import BatchPredictRequest, HealthResponse, PredictRequest, PredictResponse
from app.services.cache import get_cache
from app.services.model_loader import ModelLoader
from app.services.predictor import PredictorService
from app.validators.data_quality import validate_prediction_input

logger = logging.getLogger("uvicorn.error")

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    loader = ModelLoader.get_instance()
    return HealthResponse(status="ok", model_loaded=(loader.artifacts is not None))


@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    """Predict cluster for a single customer."""
    try:
        # Validate input
        features = validate_prediction_input(req.model_dump())
        
        # Make prediction
        out = PredictorService.predict_single(features)
        return PredictResponse(**out, meta={"source": "predict_single"})
    except ValueError as e:
        logger.warning("Validation error: %s", str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("predict error")
        raise HTTPException(status_code=500, detail="prediction failed")


@router.post("/batch_predict")
async def batch_predict(req: BatchPredictRequest):
    """Predict clusters for multiple customers."""
    try:
        # Validate all inputs
        payload = []
        for customer in req.customers:
            features = validate_prediction_input(customer.model_dump())
            payload.append(features)
        
        # Make predictions
        return PredictorService.predict_batch(payload)
    except ValueError as e:
        logger.warning("Validation error: %s", str(e))
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        logger.exception("batch predict error")
        raise HTTPException(status_code=500, detail="batch prediction failed")


@router.post("/reload_model")
async def reload_model():
    """Reload ML model without restarting the service."""
    try:
        await ModelLoader.get_instance().reload(settings)
        
        # Clear cache after reload
        get_cache().clear()
        logger.info("Model reloaded and cache cleared")
        
        return {"detail": "model reloaded"}
    except Exception:
        logger.exception("reload model failed")
        raise HTTPException(status_code=500, detail="reload failed")


@router.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    cache = get_cache()
    return cache.stats()


@router.post("/cache/clear")
async def clear_cache():
    """Clear prediction cache."""
    cache = get_cache()
    cache.clear()
    return {"detail": "cache cleared"}
