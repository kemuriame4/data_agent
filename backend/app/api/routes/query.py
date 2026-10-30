from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_current_user
from app.services.query_service import (
    answer_question,
    attribution_report,
    hybrid_product_search,
)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str


class SearchRequest(BaseModel):
    text: str
    sql_filters: str = None
    top_k: int = 10


@router.post("/ask")
def ask(req: QueryRequest, user=Depends(get_current_user)):
    return answer_question(req.question, user)


@router.post("/attribution")
def attribution(
    model: str = "last_touch",
    days: int = 30,
    top_n: int = 10,
    user=Depends(get_current_user),
):
    return {"model": model, "data": attribution_report(model, days, top_n)}


@router.post("/hybrid-search")
def hybrid_search(req: SearchRequest, user=Depends(get_current_user)):
    return {"results": hybrid_product_search(req.text, req.sql_filters, req.top_k)}
