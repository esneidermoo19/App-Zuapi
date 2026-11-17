from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.jobs import router as jobs_router
from app.modules.audio.router import router as audio_router
from app.modules.documents.router import router as documents_router
from app.modules.images.router import router as images_router

app = FastAPI(title="Conversor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = APIRouter(prefix="/api/v1")


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api.include_router(audio_router)
api.include_router(documents_router)
api.include_router(images_router)
api.include_router(jobs_router)
app.include_router(api)
