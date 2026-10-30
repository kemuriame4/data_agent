from typing import List, Dict, Any
from collections import defaultdict

from app.retrieval.qdrant_client import search_similar
from app.retrieval.embedding import embed_text
from app.retrieval.elasticsearch_client import get_es_client


def rrf_fuse(rank_lists: List[List[str]], k: int = 60) -> List[Dict[str, Any]]:
    scores = defaultdict(float)
    for rank_list in rank_lists:
        for rank, sku in enumerate(rank_list):
            scores[sku] += 1 / (k + rank + 1)
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [{"sku": sku, "rrf_score": score} for sku, score in sorted_scores]


def hybrid_search(
    text: str,
    sql_filters: str = None,
    top_k: int = 10,
) -> List[Dict[str, Any]]:
    vector = embed_text(text)
    vector_results = search_similar(vector, top_k=top_k)
    vector_skus = [r["sku"] for r in vector_results]

    es = get_es_client()
    es_query = {
        "multi_match": {
            "query": text,
            "fields": ["name^2", "category", "description"],
        }
    }
    if sql_filters:
        es_query = {
            "bool": {
                "must": es_query,
                "filter": {"query_string": {"query": sql_filters}},
            }
        }
    es_resp = es.search(index="products", body={"query": es_query, "size": top_k})
    es_skus = [hit["_source"].get("sku") for hit in es_resp["hits"]["hits"]]

    return rrf_fuse([vector_skus, es_skus])[:top_k]
