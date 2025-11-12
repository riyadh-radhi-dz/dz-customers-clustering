from fastapi import FastAPI

from app.config import settings
from app.routers import utils_router
from app.services.model_loader import ModelLoader

app = FastAPI(
    title="DZ Customers Clustering",
    description="Customer clustering API",
    version="0.1.0"
)

app.include_router(utils_router.router)


@app.on_event("startup")
async def load_artifacts() -> None:
    await ModelLoader.get_instance().load(settings)


@app.on_event("shutdown")
async def cleanup_artifacts() -> None:
    await ModelLoader.get_instance().cleanup()


@app.get("/")
async def root():
    return {"message": "Hello from dz-customers-clustering App!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)