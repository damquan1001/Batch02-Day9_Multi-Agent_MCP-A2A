import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from common.llm import get_llm

from lab9_multi_agent.state import AgentState
from lab9_multi_agent.tools import legal_rag_search, mcp_web_search

load_dotenv()
llm = get_llm()

# --- 1. SUPERVISOR ---
def supervisor_node(state: AgentState) -> AgentState:
    messages = state["messages"]
    
    # Prompt the LLM to decide the next route
    prompt = """Bạn là Supervisor của hệ thống tư vấn pháp lý. Bạn có 3 lựa chọn:
1. 'LegalRAG': Nếu câu hỏi liên quan đến pháp luật Việt Nam, cần tra cứu luật.
2. 'WebSearch': Nếu câu hỏi cần thông tin thực tế, tin tức mới nhất ngoài phạm vi văn bản luật tĩnh.
3. 'Synthesizer': Nếu bạn cho rằng thông tin đã đủ để trả lời, hoặc câu hỏi chỉ mang tính giao tiếp thông thường.

Hãy CHỈ trả về đúng 1 từ: 'LegalRAG', 'WebSearch', hoặc 'Synthesizer'."""

    sys_msg = SystemMessage(content=prompt)
    response = llm.invoke([sys_msg] + list(messages))
    
    next_node = response.content.strip()
    if "LegalRAG" in next_node:
        next_route = "LegalRAG"
    elif "WebSearch" in next_node:
        next_route = "WebSearch"
    else:
        next_route = "Synthesizer"
        
    return {
        "next": next_route,
        "trace": [f"Supervisor quyết định chuyển cho: {next_route}"]
    }

# --- 2. WORKERS ---
def legal_rag_worker(state: AgentState) -> AgentState:
    messages = state["messages"]
    # Agent sử dụng RAG tool
    rag_llm = llm.bind_tools([legal_rag_search])
    
    sys_msg = SystemMessage(content="Bạn là chuyên gia pháp lý (Legal RAG Worker). Hãy dùng legal_rag_search tool để trả lời câu hỏi.")
    response = rag_llm.invoke([sys_msg] + list(messages))
    
    return {
        "messages": [response],
        "trace": ["Legal RAG Worker đã xử lý thông tin nội bộ."]
    }

def web_search_worker(state: AgentState) -> AgentState:
    messages = state["messages"]
    web_llm = llm.bind_tools([mcp_web_search])
    
    sys_msg = SystemMessage(content="Bạn là chuyên viên nghiên cứu (Web Search Worker). Hãy dùng mcp_web_search tool để tìm kiếm cập nhật.")
    response = web_llm.invoke([sys_msg] + list(messages))
    
    return {
        "messages": [response],
        "trace": ["Web Search Worker (MCP) đã tìm kiếm bên ngoài."]
    }

def synthesizer_worker(state: AgentState) -> AgentState:
    messages = state["messages"]
    
    sys_msg = SystemMessage(content="Bạn là Synthesizer. Dựa vào toàn bộ lịch sử (bao gồm cả các tool calls và answers), hãy tổng hợp một câu trả lời cuối cùng cho người dùng.")
    response = llm.invoke([sys_msg] + list(messages))
    
    return {
        "messages": [response],
        "next": END,
        "trace": ["Synthesizer Worker đã tổng hợp kết quả."]
    }
