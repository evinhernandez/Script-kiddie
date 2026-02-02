from fastapi import FastAPI
from app.routes.health import router as health_router
from app.routes.jobs import router as jobs_router
from app.routes.snippets import router as snippets_router
from app.db.session import init_db

api = FastAPI(title="Script-kiddie API", version="0.1.0")

@api.on_event("startup")
def _startup():
    init_db()

api.include_router(health_router, prefix="/health", tags=["health"])
api.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api.include_router(snippets_router, prefix="/snippets", tags=["snippets"])
