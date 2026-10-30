from langchain_openai import ChatOpenAI

from app.config import get_settings
from app.semantic.data_dictionary import get_schema_prompt, METRICS

settings = get_settings()

llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=settings.llm_temperature,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)

TEXT_TO_SQL_PROMPT = """You are an expert Text-to-SQL assistant for cross-border e-commerce analytics.
Generate a READ-ONLY MySQL SQL query for the user question. Do NOT use DDL/DML. Always use table aliases.

Selected tables and columns:
{schema}

Standard metric formulas:
{metrics}

Additional rules:
- Use DATE(created_at) or appropriate date filters when time ranges are mentioned.
- "美西仓" means warehouse_id = 1; "美东仓" means warehouse_id = 2.
- "Facebook" means source = 'Facebook' or platform = 'Facebook'.
- "爆款" means high sales volume; sort by SUM(quantity) or COUNT(*) DESC.
- "退货率" = SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) / COUNT(*).
- Return SQL only, no markdown, no explanation.

User question: {question}
SQL:
"""

FEW_SHOT_EXAMPLES = """
Q: 近 30 天各仓库的 GMV 是多少？
SQL: SELECT warehouse_id, SUM(gmv) AS gmv FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) GROUP BY warehouse_id;

Q: 上个月退货率最高的 5 个 SKU
SQL: SELECT sku, SUM(CASE WHEN is_returned THEN 1 ELSE 0 END)/COUNT(*) AS return_rate FROM orders WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 MONTH) GROUP BY sku ORDER BY return_rate DESC LIMIT 5;
"""


def generate_sql(question: str, selected_tables: list, previous_error: str = "") -> str:
    schema = get_schema_prompt(selected_tables)
    metrics = "\n".join([f"{k}: {v}" for k, v in METRICS.items()])
    prompt = TEXT_TO_SQL_PROMPT.format(
        schema=schema, metrics=metrics, question=question
    )
    if previous_error:
        prompt += f"\nPrevious attempt failed with error: {previous_error}\nPlease correct the SQL."
    prompt += FEW_SHOT_EXAMPLES
    resp = llm.invoke(prompt).content.strip()
    resp = resp.replace("```sql", "").replace("```", "").strip()
    return resp
