import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys, os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Add root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool

app = FastAPI(title="A2A Web Search Agent")

class ChatRequest(BaseModel):
    query: str
    history: list = []

@tool
def mcp_web_search(query: str) -> str:
    """Tìm kiếm thông tin trên mạng."""
    return f"Kết quả từ Web cho '{query}': Tình hình hiện tại đang có nhiều biến động tích cực."

@app.post("/generate")
def generate(request: ChatRequest):
    try:
        llm = get_llm()
        web_llm = llm.bind_tools([mcp_web_search])
        sys_msg = SystemMessage(content="Bạn là Web Search Worker. Hãy dùng tool mcp_web_search để lấy thông tin.")
        response = web_llm.invoke([sys_msg, HumanMessage(content=request.query)])
        return {
            "answer": response.content,
            "sources": [],
            "trace": ["WebSearch ➡️ Lấy thông tin từ Web (via MCP Mock)"]
        }
    except Exception as e:
        return {
            "answer": f"Lỗi WebSearch: {e}",
            "sources": [],
            "trace": [f"WebSearch ❌ Lỗi tra cứu ({e})"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10102)