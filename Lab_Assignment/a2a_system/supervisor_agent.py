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

VALID_ROUTES = {"legal_rag", "web_search", "synthesizer"}
LEGAL_KEYWORDS = {
    "luật", "pháp luật", "ma túy", "ma tuý", "chat ma tuy", "chất ma túy",
    "hình phạt", "hinh phat", "tội", "toi", "điều", "dieu", "nghị định",
    "nghi dinh", "cai nghiện", "cai nghien", "tàng trữ", "tang tru",
    "mua bán", "mua ban", "vận chuyển", "van chuyen",
}
WEB_KEYWORDS = {
    "tin tức", "tin tuc", "hôm nay", "hom nay", "mới nhất", "moi nhat",
    "hiện nay", "hien nay", "cập nhật", "cap nhat", "thời sự", "thoi su",
    "tìm trên mạng", "tim tren mang", "web", "internet",
}


def _heuristic_route(query: str) -> str:
    lowered = query.lower()
    if any(keyword in lowered for keyword in WEB_KEYWORDS):
        return "web_search"
    if any(keyword in lowered for keyword in LEGAL_KEYWORDS):
        return "legal_rag"
    return "synthesizer"


def _normalize_route(raw_route: str, query: str) -> str:
    route = raw_route.strip().lower().strip("`'\" ")
    if route in VALID_ROUTES:
        return route

    matches = [candidate for candidate in VALID_ROUTES if candidate in route]
    if len(matches) == 1:
        return matches[0]

    return _heuristic_route(query)

class ChatRequest(BaseModel):
    query: str
    history: list = []

@app.post("/generate")
def generate(request: ChatRequest):
    prompt = """Bạn là Supervisor của hệ thống tư vấn pháp lý. Bạn có 3 lựa chọn:
1. 'legal_rag': Nếu câu hỏi liên quan đến pháp luật Việt Nam, luật phòng chống ma túy.
2. 'web_search': Nếu câu hỏi cần thông tin thực tế, tin tức đời sống, tình hình xã hội bên ngoài.
3. 'synthesizer': Nếu câu hỏi chỉ mang tính giao tiếp chào hỏi thông thường.
Hãy CHỈ trả về đúng 1 từ: 'legal_rag', 'web_search', hoặc 'synthesizer'."""

    try:
        if os.getenv("RAG_FORCE_OFFLINE", "").strip() in {"1", "true", "yes", "on"}:
            raise RuntimeError("RAG_FORCE_OFFLINE is enabled")
        if not os.getenv("OPENROUTER_API_KEY", "").strip():
            raise RuntimeError("OPENROUTER_API_KEY is not configured")
        llm = get_llm()
        sys_msg = SystemMessage(content=prompt)
        response = llm.invoke([sys_msg, HumanMessage(content=request.query)])
        route = response.content
    except Exception:
        route = ""

    next_route = _normalize_route(route, request.query)
    
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
        
        # Bổ sung: Đi qua Synthesizer (LLM synthesis cuối) để tổng hợp lại câu trả lời
        if next_route in ["legal_rag", "web_search"]:
            trace.append(f"{next_route} ➡️ Chuyển dữ liệu cho Synthesizer tổng hợp")
            synth_payload = request.model_dump()
            synth_payload["context"] = data.get("answer", "")
            
            synth_url = f"http://localhost:{ports['synthesizer']}/generate"
            synth_resp = requests.post(synth_url, json=synth_payload, timeout=60)
            synth_resp.raise_for_status()
            synth_data = synth_resp.json()
            
            return {
                "answer": synth_data.get("answer", ""),
                "sources": data.get("sources", []),
                "trace": trace + data.get("trace", []) + synth_data.get("trace", [])
            }
        
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
