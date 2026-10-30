import json
from typing import List

from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.semantic.data_dictionary import get_all_tables, get_schema_prompt

settings = get_settings()

llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=settings.llm_temperature,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

SCHEMA_LINK_PROMPT = """You are an expert e-commerce data architect. Given the user question, select the minimal set of tables needed to answer it.
Available tables and their descriptions:
{schema}

Respond ONLY with a JSON array of table names, e.g. ["orders", "skus"].
User question: {question}
"""


def select_tables(question: str) -> List[str]:
    schema_prompt = get_schema_prompt(get_all_tables())
    prompt = SCHEMA_LINK_PROMPT.format(schema=schema_prompt, question=question)
    resp = llm.invoke(prompt).content.strip()
    try:
        if "```" in resp:
            resp = (
                resp.split("```")[-2] if "```json" in resp else resp.replace("```", "")
            )
        tables = json.loads(resp)
        if isinstance(tables, list):
            return [t for t in tables if t in get_all_tables()]
    except Exception:
        pass
    return ["orders"]
