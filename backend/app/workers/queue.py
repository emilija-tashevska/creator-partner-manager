import uuid

from arq import create_pool
from arq.connections import ArqRedis

from app.workers.settings import redis_settings

_pool: ArqRedis | None = None


async def get_pool() -> ArqRedis:
    """Get or create a shared ARQ connection pool for enqueueing jobs."""
    global _pool
    if _pool is None:
        _pool = await create_pool(redis_settings)
    return _pool


async def enqueue(function_name: str, *args, **kwargs) -> str:
    """Enqueue a background job. Returns the job ID.
    
    Uses a unique _job_id per call so retries are never blocked by stale results.
    """
    pool = await get_pool()
    job = await pool.enqueue_job(
        function_name, *args, _job_id=uuid.uuid4().hex, **kwargs
    )
    return job.job_id
