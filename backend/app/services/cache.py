import json
import hashlib
from typing import Optional
import redis

from app.config import get_settings

settings = get_settings()

_client = None


def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.Redis(host=settings.redis_host, port=settings.redis_port, decode_responses=True)
    return _client


def _key(prefix: str, text: str) -> str:
    return f"{prefix}:{hashlib.md5(text.encode()).hexdigest()}"


def get_cached_query(question: str, role: str) -> Optional[dict]:
    try:
        val = get_redis_client().get(_key("query", f"{question}:{role}"))
        if val:
            return json.loads(val)
    except Exception:
        pass
    return None


def set_cached_query(question: str, role: str, result: dict, ttl: int = 300):
    try:
        get_redis_client().setex(
            _key("query", f"{question}:{role}"),
            ttl,
            json.dumps(result, ensure_ascii=False, default=str),
        )
    except Exception:
        pass
