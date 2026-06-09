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
    tool_result = mcp_web_search.invoke({"query": request.query})
    return {
        "answer": (
            f"{tool_result}\n\n"
            "Ghi chú: đây là kết quả demo từ MCP mock, chưa phải tìm kiếm web thời gian thực."
        ),
        "sources": [],
        "trace": ["WebSearch ➡️ Lấy thông tin từ Web (via MCP Mock)"]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10102)
