from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes import (
    intent_routing_node,
    schema_linking_node,
    text_to_sql_node,
    security_injection_node,
    execution_node,
    self_correction_node,
    finalize_node,
)


workflow = StateGraph(AgentState)

workflow.add_node("intent_routing", intent_routing_node)
workflow.add_node("schema_linking", schema_linking_node)
workflow.add_node("text_to_sql", text_to_sql_node)
workflow.add_node("security_injection", security_injection_node)
workflow.add_node("execution", execution_node)
workflow.add_node("finalize", finalize_node)

workflow.set_entry_point("intent_routing")
workflow.add_edge("intent_routing", "schema_linking")
workflow.add_edge("schema_linking", "text_to_sql")
workflow.add_edge("text_to_sql", "security_injection")
workflow.add_edge("security_injection", "execution")
workflow.add_conditional_edges(
    "execution",
    self_correction_node,
    {
        "generate_sql": "text_to_sql",
        "finalize": "finalize",
    },
)
workflow.add_edge("finalize", END)

agent = workflow.compile()


def run_agent(question: str, role: str = "operator", warehouse_id: int = None) -> dict:
    initial_state = AgentState(
        question=question,
        role=role,
        warehouse_id=warehouse_id,
        intent="",
        selected_tables=[],
        generated_sql="",
        validated_sql="",
        execution_result=None,
        error_message=None,
        correction_count=0,
        final_answer="",
        reasoning=[],
        chart_config=None,
    )
    return agent.invoke(initial_state)
