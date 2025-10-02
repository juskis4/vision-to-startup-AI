from celery import Celery
from config.settings import settings
import os

# Create Celery app
celery_app = Celery(
    "noteai",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
    include=["services.workers.prompt_worker"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Result backend settings
    result_expires=3600,  # 1 hour

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,

    # Routing
    task_routes={
        "services.workers.prompt_worker.generate_prompt_task": {"queue": "prompt_generation"}
    },

    # Timezone
    timezone="UTC",
    enable_utc=True,
)
