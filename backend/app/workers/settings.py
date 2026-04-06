from arq.connections import RedisSettings

from app.config import settings
from app.workers.enrichment_jobs import run_enrichment
from app.workers.brand_discovery_jobs import run_brand_discovery
from app.workers.apollo_jobs import run_scout_contacts
from app.workers.email_jobs import run_draft_emails


def parse_redis_url(url: str) -> RedisSettings:
    """Convert a redis:// URL into ARQ RedisSettings."""
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "localhost",
        port=parsed.port or 6379,
        password=parsed.password,
        database=int(parsed.path.lstrip("/") or 0),
    )


redis_settings = parse_redis_url(settings.redis_url)


class WorkerSettings:
    redis_settings = parse_redis_url(settings.redis_url)
    max_jobs = 10
    job_timeout = 300
    functions = [
        run_enrichment,
        run_brand_discovery,
        run_scout_contacts,
        run_draft_emails,
    ]
