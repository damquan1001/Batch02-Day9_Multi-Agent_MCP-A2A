from langgraph.graph import StateGraph, START, END

from lab9_multi_agent.state import AgentState
from lab9_multi_agent.agents import (
    supervisor_node,
    legal_rag_worker,
    web_search_worker,
    synthesizer_worker
)

def build_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Thêm các nodes
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("LegalRAG", legal_rag_worker)
    workflow.add_node("WebSearch", web_search_worker)
    workflow.add_node("Synthesizer", synthesizer_worker)

    # Định nghĩa edges
    workflow.add_edge(START, "Supervisor")

    # Conditional routing từ Supervisor
    def route_from_supervisor(state: AgentState):
        return state["next"]
        
    workflow.add_conditional_edges(
        "Supervisor",
        route_from_supervisor,
        {
            "LegalRAG": "LegalRAG",
            "WebSearch": "WebSearch",
            "Synthesizer": "Synthesizer"
        }
    )

    # Sau khi LegalRAG hoặc WebSearch làm xong, chuyển tới Synthesizer
    workflow.add_edge("LegalRAG", "Synthesizer")
    workflow.add_edge("WebSearch", "Synthesizer")
    
    # Synthesizer kết thúc
    workflow.add_edge("Synthesizer", END)

    app = workflow.compile()
    return app
