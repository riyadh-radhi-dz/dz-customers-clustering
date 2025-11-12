from fastapi import APIRouter, HTTPException
from app.schemas import PredictRequest, PredictResponse, HealthResponse, BatchPredictRequest
from app.services.predictor import PredictorService
from app.services.model_loader import ModelLoader
from app.config import settings
import logging

logger = logging.getLogger("uvicorn.error")

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def health():
    loader = ModelLoader.get_instance()
    return HealthResponse(status="ok", model_loaded=(loader.artifacts is not None))

@router.post("/predict", response_model=PredictResponse)
async def predict(req: PredictRequest):
    try:
        out = PredictorService.predict_single(req.model_dump())
        return PredictResponse(**out, meta={"source": "predict_single"})
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("predict error")
        raise HTTPException(status_code=500, detail="prediction failed")

@router.post("/batch_predict")
async def batch_predict(req: BatchPredictRequest):
    try:
        payload = [customer.model_dump() for customer in req.customers]
        return PredictorService.predict_batch(payload)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception:
        logger.exception("batch predict error")
        raise HTTPException(status_code=500, detail="batch prediction failed")

@router.post("/reload_model")
async def reload_model():
    try:
        await ModelLoader.get_instance().reload(settings)
        return {"detail": "model reloaded"}
    except Exception:
        logger.exception("reload model failed")
        raise HTTPException(status_code=500, detail="reload failed")
