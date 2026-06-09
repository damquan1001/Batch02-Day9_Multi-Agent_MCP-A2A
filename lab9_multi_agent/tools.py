import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Thêm Day08 vào sys.path để có thể import
DAY08_PATH = Path(__file__).resolve().parent.parent / "Day08_RAG_pipeline_cohort2"
if str(DAY08_PATH) not in sys.path:
    sys.path.insert(0, str(DAY08_PATH))

from langchain_core.tools import tool

# Cố gắng import retrieve từ Day08 (nếu fail thì tạo mock)
try:
    from src.task9_retrieval_pipeline import retrieve as day08_retrieve
    HAS_DAY08 = True
except ImportError:
    HAS_DAY08 = False

@tool
def legal_rag_search(query: str) -> str:
    """Sử dụng để tìm kiếm các thông tin về luật, nghị định, thông tư trong cơ sở dữ liệu nội bộ (Day 08 RAG)."""
    if HAS_DAY08:
        try:
            results = day08_retrieve(query, top_k=3)
            if not results:
                return "Không tìm thấy tài liệu phù hợp trong nội bộ."
            docs = []
            for i, res in enumerate(results):
                docs.append(f"[{i+1}] Nguồn: {res.get('source', 'unknown')} | Điểm: {res.get('score', 0):.2f}\n{res.get('content', '')}")
            return "\n\n".join(docs)
        except Exception as e:
            return f"Lỗi khi truy vấn RAG nội bộ: {e}"
    else:
        return f"Mock RAG Result: Theo luật xyz, hành vi {query} sẽ bị phạt từ 10-20 triệu."

@tool
def mcp_web_search(query: str) -> str:
    """Sử dụng external capability (thông qua MCP) để tìm kiếm thông tin mới nhất trên web."""
    return f"Mock Web MCP Result: Tìm thấy thông tin trên mạng về '{query}'. Cập nhật mới nhất là chính phủ đang xem xét sửa đổi luật này vào năm 2026."
