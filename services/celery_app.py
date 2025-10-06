from celery import Celery
from config.settings import settings
import os

# Build Redis URL with optional auth
redis_password = getattr(settings, 'REDIS_PASSWORD', None)
if redis_password:
    redis_url = f"redis://:{redis_password}@{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
else:
    redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"

# Create Celery app
celery_app = Celery(
    "noteai",
    broker=redis_url,
    backend=redis_url,
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
    result_backend_transport_options={
        'master_name': 'mymaster',
    } if os.getenv('REDIS_SENTINEL') else {},

    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,  # Restart workers periodically
    worker_disable_rate_limits=False,

    # Routing
    task_routes={
        "services.workers.prompt_worker.generate_prompt_task": {"queue": "prompt_generation"}
    },

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Production settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
)
