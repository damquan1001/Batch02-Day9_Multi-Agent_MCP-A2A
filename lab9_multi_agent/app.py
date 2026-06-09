import sys
import os
from pathlib import Path
import streamlit as st

# Setup path so it can import lab9_multi_agent
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from langchain_core.messages import HumanMessage
from lab9_multi_agent.graph import build_graph

st.set_page_config(page_title="Multi-Agent Legal Demo", layout="wide")
st.title("Lab 9: Multi-Agent Legal System Demo")
st.markdown("Hệ thống này sử dụng LangGraph để định tuyến câu hỏi tới đúng chuyên gia: **Legal RAG**, **Web Search**, hoặc **Synthesizer**.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Nhập câu hỏi của bạn (VD: Hình phạt tội trộm cắp là gì?)...")

if user_input:
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
        
    # Process with the agent
    with st.chat_message("assistant"):
        status_text = st.empty()
        status_text.markdown("🔄 Đang phân tích và điều hướng...")
        
        try:
            app = build_graph()
            initial_state = {
                "messages": [HumanMessage(content=user_input)],
                "next": "",
                "trace": []
            }
            
            final_state = app.invoke(initial_state)
            
            trace = final_state.get("trace", [])
            final_ans = final_state["messages"][-1].content
            
            trace_md = "**Reasoning Flow (Trace):**\n"
            for i, t in enumerate(trace):
                trace_md += f"{i+1}. {t}\n"
                
            full_response = f"{trace_md}\n\n**Kết quả:**\n{final_ans}"
            status_text.markdown(full_response)
            
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            error_msg = f"Đã xảy ra lỗi trong quá trình xử lý: {e}"
            status_text.error(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
