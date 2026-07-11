import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api import api_router
from app.core.database import SessionLocal
from app.websocket.routes import router as websocket_router

from app.db.seed import seed_admin
from app.mqtt.client import start


os.makedirs("uploads/photos", exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)

app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.include_router(api_router)
app.include_router(websocket_router)



@app.get("/")
def root():
    return {
        "message": "SilaseZ API Running"
    }

@app.on_event("startup")
def startup():

    db = SessionLocal()

    try:
        seed_admin(db)

    finally:
        db.close()
        
    start()