from __future__ import annotations
from celery import Celery
from app.config import REDIS_URL

celery_app = Celery("scriptkiddie", broker=REDIS_URL, backend=REDIS_URL)

@celery_app.task(name="run_scan_job")
def run_scan_job(payload: dict):
    from app.services.pipeline import run_pipeline
    return run_pipeline(payload)
