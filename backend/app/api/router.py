from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.creators import router as creators_router
from app.api.brands import router as brands_router
from app.api.contacts import router as contacts_router
from app.api.emails import router as emails_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(creators_router)
api_router.include_router(brands_router)
api_router.include_router(contacts_router)
api_router.include_router(emails_router)


@api_router.get("/ping")
async def ping():
    return {"message": "pong"}
