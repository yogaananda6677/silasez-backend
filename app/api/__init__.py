from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.peternakan import router as peternakan_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.silo import router as silo_router
from app.api.fermentasi import router as fermentasi_router
from app.api.pakar import router as pakar_router
from app.api.notification import router as notification_router


api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(peternakan_router)
api_router.include_router(admin_router) 
api_router.include_router(chat_router)
api_router.include_router(silo_router)
api_router.include_router(fermentasi_router)
api_router.include_router(pakar_router)
api_router.include_router(notification_router)
