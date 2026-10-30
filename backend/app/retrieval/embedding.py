from typing import List
from sentence_transformers import SentenceTransformer

from app.config import get_settings

settings = get_settings()
_text_model = None


def get_text_embedding_model() -> SentenceTransformer:
    global _text_model
    if _text_model is None:
        _text_model = SentenceTransformer(settings.embedding_model)
    return _text_model


def embed_text(text: str) -> List[float]:
    model = get_text_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_text_embedding_model()
    return model.encode(texts, normalize_embeddings=True).tolist()
