from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    question: str
    role: str
    warehouse_id: Optional[int]
    intent: str
    selected_tables: List[str]
    generated_sql: str
    validated_sql: str
    execution_result: Any
    error_message: Optional[str]
    correction_count: int
    final_answer: str
    reasoning: List[str]
    chart_config: Optional[Dict[str, Any]]
