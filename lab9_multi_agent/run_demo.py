import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from lab9_multi_agent.graph import build_graph

def run_query(query: str):
    print(f"==============================================")
    print(f"QUERY: {query}")
    print(f"==============================================\n")
    
    app = build_graph()
    
    initial_state = {
        "messages": [HumanMessage(content=query)],
        "next": "",
        "trace": []
    }
    
    # Run the graph
    final_state = app.invoke(initial_state)
    
    print("--- REASONING FLOW (TRACE) ---")
    for idx, step in enumerate(final_state["trace"]):
        print(f"{idx + 1}. {step}")
        
    print("\n--- FINAL RESULT ---")
    print(final_state["messages"][-1].content)
    print("\n")

if __name__ == "__main__":
    # Test 1: Legal question (Should route to LegalRAG)
    run_query("Hình phạt cho tội trộm cắp tài sản là gì?")
    
    # Test 2: Web Search question (Should route to WebSearch)
    run_query("Tình hình giao thông hiện tại ở Hà Nội ra sao?")
    
    # Test 3: General conversation (Should route to Synthesizer directly)
    run_query("Xin chào, bạn có thể giúp gì cho tôi?")
