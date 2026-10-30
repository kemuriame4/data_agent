from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, require_role
from app.database.seed_data import seed_all
from app.retrieval.indexer import index_products
from app.services.benchmark_service import run_benchmark

router = APIRouter()


@router.post("/seed")
def seed(user=Depends(require_role("admin"))):
    seed_all()
    return {"message": "Seed completed"}


@router.post("/index-products")
def index(user=Depends(require_role("admin"))):
    index_products()
    return {"message": "Indexing completed"}


@router.post("/benchmark")
def benchmark(user=Depends(require_role("admin", "finance"))):
    return {"results": run_benchmark(role=user["role"])}
