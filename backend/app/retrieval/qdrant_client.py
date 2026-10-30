from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.config import get_settings

settings = get_settings()

_client = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def ensure_collection(vector_size: int = 768):
    client = get_qdrant_client()
    if not client.collection_exists(settings.qdrant_collection):
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def upsert_points(points: List[PointStruct]):
    client = get_qdrant_client()
    ensure_collection()
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def search_similar(
    vector: List[float],
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    client = get_qdrant_client()
    ensure_collection()
    result = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=vector,
        query_filter=filters,
        limit=top_k,
        with_payload=True,
    )
    return [
        {
            "sku": r.payload.get("sku"),
            "score": r.score,
            "payload": r.payload,
        }
        for r in result
    ]
