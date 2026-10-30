from qdrant_client.models import PointStruct

from app.database.mysql_client import get_db_session
from app.database.models import SKU
from app.retrieval.qdrant_client import upsert_points, ensure_collection
from app.retrieval.embedding import embed_texts
from app.retrieval.elasticsearch_client import get_es_client


def index_products():
    with get_db_session() as db:
        skus = db.query(SKU).all()

    texts = [f"{s.name} {s.category} {s.description or ''}" for s in skus]
    embeddings = embed_texts(texts)

    points = []
    for sku, vector in zip(skus, embeddings):
        points.append(
            PointStruct(
                id=sku.id,
                vector=vector,
                payload={
                    "sku": sku.sku,
                    "name": sku.name,
                    "category": sku.category,
                    "description": sku.description,
                    "image_url": sku.image_url,
                    "sale_price": float(sku.sale_price),
                },
            )
        )
    ensure_collection(len(embeddings[0]) if embeddings else 768)
    upsert_points(points)

    es = get_es_client()
    if not es.indices.exists(index="products"):
        es.indices.create(
            index="products",
            body={
                "mappings": {
                    "properties": {
                        "sku": {"type": "keyword"},
                        "name": {"type": "text"},
                        "category": {"type": "keyword"},
                        "description": {"type": "text"},
                        "sale_price": {"type": "float"},
                    }
                }
            },
        )
    for sku in skus:
        es.index(
            index="products",
            id=sku.sku,
            document={
                "sku": sku.sku,
                "name": sku.name,
                "category": sku.category,
                "description": sku.description,
                "sale_price": float(sku.sale_price),
            },
        )
    print(f"Indexed {len(skus)} products to Qdrant & Elasticsearch.")


if __name__ == "__main__":
    index_products()
