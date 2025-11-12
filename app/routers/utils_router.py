from fastapi import APIRouter

router = APIRouter()

@router.post("/")
async def post():
    return {"message": "Hello from utils dz-customers-clustering!"}