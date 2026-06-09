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
DAY08_ROOT = Path(__file__).resolve().parents[1]
if str(DAY08_ROOT) not in sys.path:
    sys.path.insert(0, str(DAY08_ROOT))
GROUP_PROJECT = DAY08_ROOT / "group_project"
if str(GROUP_PROJECT) not in sys.path:
    sys.path.insert(0, str(GROUP_PROJECT))

from src.module_rag_core.rag_engine import RAGCoreEngine
from system_contracts import ChatMessage

app = FastAPI(title="A2A Legal RAG Agent")
engine = RAGCoreEngine()

class ChatRequest(BaseModel):
    query: str
    history: list = []

@app.post("/generate")
def generate(request: ChatRequest):
    try:
        hist = [ChatMessage(**m) for m in request.history]
        ans = engine.generate_answer("default", request.query, hist)
        return {
            "answer": f"Thông tin từ cơ sở dữ liệu luật:\n{ans.answer}",
            "sources": [s.model_dump() for s in ans.sources],
            "trace": ["LegalRAG ➡️ Truy vấn Weaviate DB thành công"]
        }
    except Exception as e:
        return {
            "answer": f"Lỗi RAG: {e}",
            "sources": [],
            "trace": [f"LegalRAG ❌ Lỗi tra cứu ({e})"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10101)