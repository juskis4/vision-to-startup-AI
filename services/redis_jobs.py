import redis
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from config.settings import settings


class RedisJobManager:

    def __init__(self):
        redis_url = getattr(settings, 'REDIS_URL', None)
        if redis_url and redis_url.strip():
            self.redis_client = redis.from_url(
                redis_url, decode_responses=True)
        else:
            redis_password = getattr(settings, 'REDIS_PASSWORD', None)
            if redis_password:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=redis_password,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
            else:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True
                )
        self.job_ttl = 48 * 3600

    def create_job(
        self,
        idea_id: str,
        service_type: str,
        idempotency_key: str
    ) -> str:
        """Create a new job and return job_id"""
        job_id = str(uuid.uuid4())

        # Check for existing job with same idempotency key
        dedupe_key = f"prompt_job_dedupe:{idea_id}:{service_type}:{idempotency_key}"
        existing_job_id = self.redis_client.get(dedupe_key)

        if existing_job_id:
            return existing_job_id

        # Create job hash
        job_key = f"prompt_job:{job_id}"
        job_data = {
            "status": "queued",
            "progress": "0.0",
            "error": "",
            "idea_id": idea_id,
            "service_type": service_type,
            "idempotency_key": idempotency_key,
            "prompt_id": "",
            "created_at": datetime.utcnow().isoformat()
        }

        # Set job data with TTL
        self.redis_client.hset(job_key, mapping=job_data)
        self.redis_client.expire(job_key, self.job_ttl)

        # Set dedupe key with same TTL
        self.redis_client.setex(dedupe_key, self.job_ttl, job_id)

        return job_id

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job data by job_id"""
        job_key = f"prompt_job:{job_id}"
        job_data = self.redis_client.hgetall(job_key)

        if not job_data:
            return None

        # Convert progress to float
        if "progress" in job_data:
            try:
                job_data["progress"] = float(job_data["progress"])
            except (ValueError, TypeError):
                job_data["progress"] = 0.0

        return job_data

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        error: Optional[str] = None,
        prompt_id: Optional[str] = None
    ) -> bool:
        """Update job fields"""
        job_key = f"prompt_job:{job_id}"

        # Check if job exists
        if not self.redis_client.exists(job_key):
            return False

        updates = {}
        if status is not None:
            updates["status"] = status
        if progress is not None:
            updates["progress"] = str(progress)
        if error is not None:
            updates["error"] = error
        if prompt_id is not None:
            updates["prompt_id"] = prompt_id

        if updates:
            self.redis_client.hset(job_key, mapping=updates)
            # Refresh TTL on update
            self.redis_client.expire(job_key, self.job_ttl)

        return True

    def job_exists(self, job_id: str) -> bool:
        """Check if job exists"""
        job_key = f"prompt_job:{job_id}"
        return self.redis_client.exists(job_key) > 0

    def get_dedupe_job_id(self, idea_id: str, service_type: str, idempotency_key: str) -> Optional[str]:
        """Get existing job ID for idempotency check"""
        dedupe_key = f"prompt_job_dedupe:{idea_id}:{service_type}:{idempotency_key}"
        return self.redis_client.get(dedupe_key)


# Global instance
redis_job_manager = RedisJobManager()
