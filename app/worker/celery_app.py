"""
Celery application factory.

Celery is configured here as a separate process from the FastAPI ASGI server.
Using Redis as both the task broker and result backend keeps the infrastructure
footprint minimal while providing reliable at-least-once delivery semantics.

The worker is launched via: celery -A app.worker.celery_app worker --loglevel=info
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "task_management",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

# Serialise task arguments as JSON rather than the default pickle format.
# JSON is safer (no arbitrary code execution on deserialization) and
# produces human-readable task arguments in the Redis backend.
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Retry a failed task up to 3 times with exponential backoff.
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
