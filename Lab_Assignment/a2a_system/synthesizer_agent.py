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

app = FastAPI(title="A2A Synthesizer Agent")

class ChatRequest(BaseModel):
    query: str
    history: list = []
    context: str = ""

@app.post("/generate")
def generate(request: ChatRequest):
    try:
        llm = get_llm()
        sys_msg = SystemMessage(content=f"Bạn là Tổng hợp viên (Synthesizer). Dựa vào nội dung đã thu thập được từ các chuyên gia khác dưới đây, hãy tổng hợp câu trả lời cuối cùng một cách thân thiện, súc tích và dễ hiểu nhất cho người dùng.\n\n[Dữ liệu thu thập]:\n{request.context}")
        response = llm.invoke([sys_msg, HumanMessage(content=request.query)])
        return {
            "answer": response.content,
            "sources": [],
            "trace": ["Synthesizer ➡️ Tổng hợp đáp án cuối cùng"]
        }
    except Exception as e:
        return {
            "answer": f"Lỗi Synthesizer: {e}",
            "sources": [],
            "trace": [f"Synthesizer ❌ Lỗi tổng hợp ({e})"]
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10103)