import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import sys, os
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv()

# Add root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

app = FastAPI(title="A2A Supervisor Agent")

class ChatRequest(BaseModel):
    query: str
    history: list = []

@app.post("/generate")
def generate(request: ChatRequest):
    llm = get_llm()
    prompt = """Bạn là Supervisor của hệ thống tư vấn pháp lý. Bạn có 3 lựa chọn:
1. 'legal_rag': Nếu câu hỏi liên quan đến pháp luật Việt Nam, luật phòng chống ma túy.
2. 'web_search': Nếu câu hỏi cần thông tin thực tế, tin tức đời sống, tình hình xã hội bên ngoài.
3. 'synthesizer': Nếu câu hỏi chỉ mang tính giao tiếp chào hỏi thông thường.
Hãy CHỈ trả về đúng 1 từ: 'legal_rag', 'web_search', hoặc 'synthesizer'."""

    sys_msg = SystemMessage(content=prompt)
    response = llm.invoke([sys_msg, HumanMessage(content=request.query)])
    
    route = response.content.strip()
    next_route = "synthesizer"
    if "legal_rag" in route: next_route = "legal_rag"
    elif "web_search" in route: next_route = "web_search"
    
    trace = [f"Supervisor ➡️ Định tuyến tới {next_route}"]
    
    # Map routes to ports
    ports = {
        "legal_rag": 10101,
        "web_search": 10102,
        "synthesizer": 10103
    }
    
    try:
        url = f"http://localhost:{ports[next_route]}/generate"
        resp = requests.post(url, json=request.model_dump(), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return {
            "answer": data.get("answer", ""),
            "sources": data.get("sources", []),
            "trace": trace + data.get("trace", [])
        }
    except Exception as e:
        # Fallback to synthesizer
        trace.append(f"Lỗi gọi {next_route} ({e}) ➡️ Fallback to synthesizer")
        if next_route != "synthesizer":
            try:
                url = "http://localhost:10103/generate"
                resp = requests.post(url, json=request.model_dump(), timeout=60)
                data = resp.json()
                return {
                    "answer": data.get("answer", ""),
                    "sources": data.get("sources", []),
                    "trace": trace + data.get("trace", [])
                }
            except Exception as e2:
                return {"answer": f"Lỗi hệ thống: {e2}", "sources": [], "trace": trace}
        return {"answer": f"Lỗi hệ thống: {e}", "sources": [], "trace": trace}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10100)
