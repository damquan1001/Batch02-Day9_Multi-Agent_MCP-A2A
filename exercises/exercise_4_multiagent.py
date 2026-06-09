"""Bài Tập 4: Thêm Privacy Agent vào Multi-Agent System."""

import asyncio
import os
import sys
from typing import Annotated, TypedDict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from common.llm import get_llm


def _last_wins(left: str | None, right: str | None) -> str:
    """Reducer: giá trị mới ghi đè giá trị cũ."""
    return right if right is not None else (left or "")


def _invoke_llm_or_fallback(prompt: str, fallback: str) -> str:
    """Call the LLM, but keep the exercise runnable when the provider is rate-limited."""
    try:
        llm = get_llm()
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as exc:
        return f"{fallback}\n\n[Lưu ý: dùng fallback do LLM/API tạm thời lỗi: {exc}]"


class State(TypedDict):
    question: str
    law_analysis: Annotated[str, _last_wins]
    tax_analysis: Annotated[str, _last_wins]
    compliance_analysis: Annotated[str, _last_wins]
    privacy_analysis: Annotated[str, _last_wins]
    final_response: str


def law_agent(state: State) -> dict:
    """Agent phân tích pháp lý tổng quát."""
    prompt = f"""Bạn là chuyên gia pháp lý. Phân tích câu hỏi sau:

{state['question']}

Tập trung vào: hợp đồng, trách nhiệm dân sự, quyền và nghĩa vụ pháp lý."""
    
    fallback = (
        "Có thể phát sinh trách nhiệm dân sự, nghĩa vụ thông báo/khắc phục sự cố, "
        "bồi thường thiệt hại cho khách hàng và rủi ro xử phạt hành chính tùy luật áp dụng."
    )
    return {"law_analysis": _invoke_llm_or_fallback(prompt, fallback)}


def check_routing(state: State) -> list[Send]:
    """Quyết định gọi agents nào dựa trên nội dung câu hỏi."""
    question_lower = state["question"].lower()
    tasks = []
    
    if any(kw in question_lower for kw in ["data", "privacy", "gdpr", "dữ liệu"]):
        tasks.append(Send("privacy_agent", state))
        
    if any(kw in question_lower for kw in ["tax", "irs", "thuế"]):
        tasks.append(Send("tax_agent", state))
    
    if any(kw in question_lower for kw in ["compliance", "sec", "regulation"]):
        tasks.append(Send("compliance_agent", state))
    
    return tasks if tasks else [Send("aggregate_results", state)]


def tax_agent(state: State) -> dict:
    """Agent chuyên về thuế."""
    prompt = f"""Bạn là chuyên gia thuế. Phân tích khía cạnh thuế trong câu hỏi:

Câu hỏi: {state['question']}
Phân tích pháp lý: {state.get('law_analysis', 'N/A')}

Tập trung: IRS, tax evasion, penalties, FBAR, FATCA."""
    
    fallback = (
        "Chi phí khắc phục sự cố có thể được xem xét là chi phí kinh doanh nếu đáp ứng điều kiện khấu trừ. "
        "Tiền phạt hành chính thường không được khấu trừ thuế; cần lưu chứng từ và phân loại chi phí rõ ràng."
    )
    return {"tax_analysis": _invoke_llm_or_fallback(prompt, fallback)}


def compliance_agent(state: State) -> dict:
    """Agent chuyên về compliance."""
    prompt = f"""Bạn là chuyên gia compliance. Phân tích khía cạnh tuân thủ:

Câu hỏi: {state['question']}
Phân tích pháp lý: {state.get('law_analysis', 'N/A')}

Tập trung: SEC, SOX, FCPA, AML, regulatory violations."""
    
    fallback = (
        "Cần đánh giá nghĩa vụ thông báo sự cố, lưu hồ sơ xử lý, rà soát kiểm soát nội bộ "
        "và chuẩn bị báo cáo cho cơ quan quản lý nếu thuộc ngành chịu điều tiết."
    )
    return {"compliance_analysis": _invoke_llm_or_fallback(prompt, fallback)}


def privacy_agent(state: State) -> dict:
    """Agent chuyên về bảo vệ dữ liệu cá nhân và GDPR."""
    prompt = f"""Bạn là chuyên gia về GDPR và luật bảo vệ dữ liệu cá nhân. Phân tích khía cạnh bảo mật dữ liệu trong câu hỏi:
    
Câu hỏi: {state['question']}
Phân tích pháp lý: {state.get('law_analysis', 'N/A')}

Tập trung: GDPR, CCPA, rò rỉ dữ liệu (data breach), quyền riêng tư của khách hàng."""
    
    fallback = (
        "Sự cố rò rỉ dữ liệu có thể kích hoạt nghĩa vụ thông báo cho chủ thể dữ liệu và cơ quan quản lý, "
        "đánh giá tác động bảo vệ dữ liệu, khắc phục lỗ hổng, và rủi ro phạt theo GDPR/CCPA hoặc Nghị định 13/2023/NĐ-CP."
    )
    return {"privacy_analysis": _invoke_llm_or_fallback(prompt, fallback)}


def aggregate_results(state: State) -> dict:
    """Tổng hợp kết quả từ tất cả agents."""
    sections = []
    if state.get("law_analysis"):
        sections.append(f"📋 PHÂN TÍCH PHÁP LÝ:\n{state['law_analysis']}")
    if state.get("tax_analysis"):
        sections.append(f"💰 PHÂN TÍCH THUẾ:\n{state['tax_analysis']}")
    if state.get("compliance_analysis"):
        sections.append(f"✅ PHÂN TÍCH TUÂN THỦ:\n{state['compliance_analysis']}")
    if state.get("privacy_analysis"):
        sections.append(f"🔒 PHÂN TÍCH BẢO MẬT/PRIVACY:\n{state['privacy_analysis']}")
    
    combined = "\n\n".join(sections)
    final_response = (
        f"Câu hỏi gốc: {state['question']}\n\n"
        f"{combined}\n\n"
        "Kết luận: Công ty cần ưu tiên cô lập sự cố, thông báo theo luật áp dụng, "
        "lưu bằng chứng chi phí và tham vấn luật sư/đơn vị thuế để xử lý nghĩa vụ cụ thể."
    )
    return {"final_response": final_response}


def build_graph() -> StateGraph:
    """Xây dựng multi-agent graph."""
    graph = StateGraph(State)
    
    # Add nodes
    graph.add_node("law_agent", law_agent)
    graph.add_node("tax_agent", tax_agent)
    graph.add_node("compliance_agent", compliance_agent)
    graph.add_node("privacy_agent", privacy_agent)
    graph.add_node("aggregate_results", aggregate_results)
    
    # Define edges
    graph.add_edge(START, "law_agent")
    graph.add_conditional_edges(
        "law_agent",
        check_routing,
        ["tax_agent", "compliance_agent", "privacy_agent", "aggregate_results"]
    )
    graph.add_edge("tax_agent", "aggregate_results")
    graph.add_edge("compliance_agent", "aggregate_results")
    graph.add_edge("privacy_agent", "aggregate_results")
    graph.add_edge("aggregate_results", END)
    
    return graph.compile()


async def main():
    load_dotenv()
    
    # Test với câu hỏi có liên quan đến privacy
    question = "Nếu công ty bị rò rỉ dữ liệu khách hàng, hậu quả pháp lý và thuế là gì?"
    
    print("=" * 70)
    print("MULTI-AGENT SYSTEM với Privacy Agent")
    print("=" * 70)
    print(f"\nCâu hỏi: {question}\n")
    print("Đang xử lý qua các agents...\n")
    
    graph = build_graph()
    
    result = await graph.ainvoke({
        "question": question,
        "law_analysis": "",
        "tax_analysis": "",
        "compliance_analysis": "",
        "privacy_analysis": "",
        "final_response": "",
    })
    
    print("\n" + "=" * 70)
    print("KẾT QUẢ CUỐI CÙNG")
    print("=" * 70)
    print(result["final_response"])
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
