from fastapi import Depends, FastAPI
from app.routers import utils_router

app = FastAPI(
    title="DZ Customers Clustering",
    description="Customer clustering API",
    version="0.1.0"
)

app.include_router(utils_router.router)

@app.get("/")
async def root():
    return {"message": "Hello from dz-customers-clustering App!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)