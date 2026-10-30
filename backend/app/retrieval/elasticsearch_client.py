from typing import List, Dict, Any
from elasticsearch import Elasticsearch

from app.config import get_settings

settings = get_settings()

_client = None


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(
            hosts=[
                f"http://{settings.elasticsearch_host}:{settings.elasticsearch_port}"
            ]
        )
    return _client


def ensure_event_index():
    es = get_es_client()
    index = "event_logs"
    if not es.indices.exists(index=index):
        es.indices.create(
            index=index,
            body={
                "mappings": {
                    "properties": {
                        "session_id": {"type": "keyword"},
                        "user_id": {"type": "integer"},
                        "query_text": {"type": "text"},
                        "generated_sql": {"type": "text"},
                        "execution_status": {"type": "keyword"},
                        "latency_ms": {"type": "integer"},
                        "created_at": {"type": "date"},
                    }
                }
            },
        )


def index_event(doc: Dict[str, Any]):
    es = get_es_client()
    ensure_event_index()
    es.index(index="event_logs", document=doc)


def search_events(query: str, size: int = 20) -> List[Dict[str, Any]]:
    es = get_es_client()
    ensure_event_index()
    resp = es.search(
        index="event_logs",
        body={
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["query_text", "generated_sql"],
                }
            },
            "size": size,
        },
    )
    return [hit["_source"] for hit in resp["hits"]["hits"]]
