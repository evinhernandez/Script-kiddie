from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.db.session import init_db
from app.routes.health import router as health_router
from app.routes.jobs import router as jobs_router
from app.routes.snippets import router as snippets_router
from app.routes.stats import router as stats_router
from app.routes.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


api = FastAPI(title="Script-kiddie API", version="0.2.0", lifespan=lifespan)

api.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-API-Key", "Content-Type"],
)

api.include_router(health_router, prefix="/health", tags=["health"])
api.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api.include_router(snippets_router, prefix="/snippets", tags=["snippets"])
api.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
api.include_router(stats_router, prefix="/stats", tags=["stats"])
