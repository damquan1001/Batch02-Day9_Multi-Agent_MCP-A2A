Trần Hoàng Nam - 2A202600870

# Lab Solutions - Day 09

Tài liệu này tổng hợp giải pháp chi tiết cho TOÀN BỘ các bài Lab trong `CODELAB.md`.

---

## Phần 1: Direct LLM Calling

### Bài Tập 1.1: Thay đổi câu hỏi
**Yêu cầu:** Sửa biến `QUESTION` thành câu hỏi pháp lý khác.
**Giải pháp:** Mở file `stages/stage_1_direct_llm/main.py` và sửa:
```python
QUESTION = "Theo pháp luật Việt Nam, hành vi tổ chức sử dụng trái phép chất ma túy bị xử lý như thế nào?"
```

### Bài Tập 1.2: Thêm temperature control
**Yêu cầu:** Thêm parameter `temperature=0.3` vào hàm `get_llm()`.
**Giải pháp:** Mở `common/llm.py` và điều chỉnh:
```python
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4-5"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.3, # Đã thêm parameter này
        max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "200")),
    )
```

---

## Phần 2: LLM + RAG & Tools

### Bài Tập 2.1: Thêm knowledge base entry
**Giải pháp:** Thêm vào list `LEGAL_KNOWLEDGE` trong `stages/stage_2_rag_tools/main.py`:
```python
{
    "id": "labor_law",
    "keywords": ["lao động", "sa thải", "hợp đồng lao động", "labor", "termination"],
    "text": (
        "Theo Bộ luật Lao động Việt Nam 2019, người sử dụng lao động có thể "
        "đơn phương chấm dứt hợp đồng trong các trường hợp: (1) người lao động "
        "thường xuyên không hoàn thành công việc; (2) bị ốm đau, tai nạn đã điều trị "
        "12 tháng chưa khỏi; (3) thiên tai, hỏa hoạn; (4) người lao động đủ tuổi nghỉ hưu."
    ),
}
```

### Bài Tập 2.2: Tạo tool mới
**Giải pháp:** Khai báo hàm `@tool` bên dưới hàm `search_legal_knowledge`:
```python
@tool
def check_statute_of_limitations(case_type: str) -> str:
    """Kiểm tra thời hiệu khởi kiện theo loại vụ án.
    
    Args:
        case_type: Loại vụ án (contract, tort, property)
    """
    limits = {
        "contract": "4 năm (UCC § 2-725)",
        "tort": "2-3 năm tùy bang",
        "property": "5 năm",
    }
    return limits.get(case_type.lower(), "Không xác định")
```
Và thêm vào danh sách: `tools = [search_legal_knowledge, check_statute_of_limitations]`

---

## Phần 3: Single Agent với ReAct

### Bài Tập 3.1: Thêm tool tra cứu án lệ
**Giải pháp:** Mở `stages/stage_3_single_agent/main.py`, định nghĩa tool và thêm vào mảng `tools`:
```python
@tool
def search_case_law(keywords: str) -> str:
    """Tìm kiếm án lệ theo từ khóa."""
    cases = {
        "breach": "Hadley v. Baxendale (1854) - Consequential damages",
        "negligence": "Donoghue v. Stevenson (1932) - Duty of care",
        "contract": "Carlill v. Carbolic Smoke Ball Co (1893) - Unilateral contract",
    }
    for key, case in cases.items():
        if key in keywords.lower():
            return case
    return "Không tìm thấy án lệ phù hợp"
```

### Bài Tập 3.2: Debug agent reasoning
**Giải pháp:** Bật debug mode bằng cách thêm tham số `debug=True` (hoặc cấu hình logging) vào `create_react_agent`:
```python
# Cập nhật khi tạo agent
agent_executor = create_react_agent(llm, tools, debug=True)
```

---

## Phần 4: Multi-Agent In-Process

### Bài Tập 4.1 & 4.2: Thêm agent mới & Conditional Routing
**Giải pháp:** Trong `stages/stage_4_milti_agent/main.py`, bổ sung hàm `privacy_agent`:
```python
def privacy_agent(state: State) -> dict:
    llm = get_llm()
    prompt = f"Bạn là chuyên gia về GDPR... \nCâu hỏi: {state['question']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"privacy_analysis": response.content}
```
Và sửa lại hàm định tuyến `check_routing` để bắt từ khoá `privacy`:
```python
def check_routing(state: State) -> list[Send]:
    # ...
    if any(kw in question_lower for kw in ["data", "privacy", "gdpr", "dữ liệu"]):
        tasks.append(Send("privacy_agent", state))
    return tasks if tasks else [Send("aggregate_results", state)]
```
Cuối cùng kết nối vào graph:
```python
graph.add_node("privacy_agent", privacy_agent)
graph.add_edge("privacy_agent", "aggregate_results")
```

---

## Phần 5: Distributed A2A System

### Bài Tập 5.1: Trace request flow
**Sequence Diagram Flow:**
`Client (test_client.py)` ➡️ `Customer Agent (10100)` ➡️ `Law Agent (10101)` ➡️ `Customer Agent` ➡️ Trả về Client.
*(Mỗi request được sinh ra một chuỗi `trace_id` duy nhất và chuyển tiếp qua headers).*

### Bài Tập 5.2: Test dynamic discovery
**Quan sát:** Khi dừng `Tax Agent` ở port `10102`, Customer Agent hoặc Registry sẽ gặp lỗi `ConnectionError`. Do hệ thống có Registry, Tax Agent sẽ bị coi là Offline và fallback sang các Agent khác hoặc trả về thông báo lỗi thay vì treo toàn bộ hệ thống.

### Bài Tập 5.3: Modify agent behavior
**Giải pháp:** Mở `tax_agent/graph.py`, sửa `system_prompt` và chạy lại service để ghi đè prompt:
```python
system_prompt = "Bạn là chuyên gia thuế. Hãy trả lời cực kỳ CỤT LỦN VÀ NGẮN GỌN (dưới 20 chữ)."
```

---

## Phần 6: Bài Tập Nâng Cao (Optional Challenges)

1. **Thêm Memory:** Bổ sung trường `chat_history: list` vào class `State` và dùng `BaseChatMessageHistory` của LangChain.
2. **Add Authentication:** Tạo Middleware FastAPI hoặc kiểm tra `x-api-key` header ở mỗi request.
3. **Implement retry logic:** Bọc các hàm `requests.post` vào một cơ chế retry sử dụng thư viện `tenacity` (`@retry(stop=stop_after_attempt(3), wait=wait_exponential())`).
4. **Monitoring:** Gắn `langsmith` bằng các biến môi trường `LANGCHAIN_TRACING_V2=true` và `LANGCHAIN_API_KEY`.

---

## Bài Tập Cộng Điểm

### 1. Latency (Tổng thời gian trả lời 1 câu hỏi)
Với một RAG pipeline bình thường gọi 3 Agents tuần tự, tổng thời gian tốn khoảng **10 - 15 giây** (tùy theo load của mô hình Gemini Flash / Claude Haiku). Mạng nội bộ kết nối tốn chưa tới 0.1s, bottleneck 99% nằm ở phía gọi LLM API.

### 2. Đề xuất phương án giảm latency
- **Chạy Song Song (Parallel Execution):** Trong bài A2A, thay vì đợi `Law Agent` trả về rồi mới gọi `Tax Agent`, có thể dùng `asyncio.gather()` bắn requests cùng lúc đến tất cả các worker agents để giảm thời gian chờ xuống chỉ bằng thời gian của agent chạy lâu nhất (giảm từ 10s xuống còn 4s).
- **Streaming (SSE):** Sử dụng Server-Sent Events để trả về từng token cho UI ngay khi LLM sinh ra chữ cái đầu tiên (TTFT - Time To First Token). Tăng trải nghiệm người dùng ngay lập tức.
- **Semantic Caching:** Sử dụng Redis hoặc In-memory Vector Store lưu lại câu hỏi. Nếu câu hỏi tương tự 95% xuất hiện, lấy thẳng kết quả thay vì gọi lại Agents (giảm latency xuống dưới 0.1s).
- **Reranker thu gọn context:** Thay vì nhét 5 tài liệu dài vào LLM (tăng thời gian đọc và sinh câu trả lời), dùng một mô hình cross-encoder nhẹ chạy local để chọn đúng 1 đoạn văn chính xác nhất.
