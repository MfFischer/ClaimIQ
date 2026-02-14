from fastapi import APIRouter
from app.api.claims import router as claims_router

api_router = APIRouter()
api_router.include_router(claims_router)
