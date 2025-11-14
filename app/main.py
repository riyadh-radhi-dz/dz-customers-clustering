"""Main FastAPI application with full MLOps features."""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.config import settings
from app.middleware.auth import APIKeyAuth
from app.middleware.logging import LoggingMiddleware, setup_logging
from app.middleware.metrics import MetricsMiddleware, metrics_endpoint, set_model_load_time
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import utils_router
from app.services.model_loader import ModelLoader


# Setup structured logging
setup_logging(log_level=settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    start_time = time.time()
    await ModelLoader.get_instance().load(settings)
    load_duration = time.time() - start_time
    set_model_load_time(load_duration)
    
    yield
    
    # Shutdown
    await ModelLoader.get_instance().cleanup()


app = FastAPI(
    title="DZ Customers Clustering API",
    description="""
    Production-ready ML API for customer clustering using K-Prototypes algorithm.
    
    ## Features
    - Real-time customer cluster prediction
    - Batch prediction support
    - Model hot-reloading
    - Prometheus metrics
    - Structured logging
    - Rate limiting
    - API key authentication
    
    ## Authentication
    Include your API key in the request header:
    - `Authorization: Bearer YOUR_API_KEY` or
    - `X-API-Key: YOUR_API_KEY`
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add custom middlewares
app.add_middleware(LoggingMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    requests_per_hour=settings.RATE_LIMIT_PER_HOUR,
)
app.add_middleware(
    APIKeyAuth,
    api_keys=settings.API_KEYS,
    enabled=settings.AUTH_ENABLED,
)

# Add routers
app.include_router(utils_router.router, tags=["predictions"])

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint)


@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "DZ Customers Clustering API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )