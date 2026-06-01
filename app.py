"""
독서로 FAQ 챗봇 — Streamlit 웹 인터페이스
실행: streamlit run app.py
"""

import os
import streamlit as st
from rag_engine import build_vectorstore_in_memory, build_qa_chain, answer

st.set_page_config(
    page_title="독서로 FAQ 챗봇",
    page_icon="📚",
    layout="centered",
)

st.markdown(
    """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1E3A5F, #2980B9);
        color: white; padding: 20px; border-radius: 10px;
        text-align: center; margin-bottom: 20px;
    }
    .source-box {
        background: #F0F4F8; border-left: 4px solid #2980B9;
        padding: 10px; border-radius: 5px;
        font-size: 0.85em; color: #555; margin-top: 10px;
    }
    .tip-box {
        background: #FFF9E6; border-left: 4px solid #F39C12;
        padding: 10px; border-radius: 5px; margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="main-header">
        <h2>📚 독서로 FAQ 챗봇</h2>
        <p>독서로(read365.edunet.net) 관련 궁금한 점을 물어보세요!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ── Groq API 키: Streamlit Secrets → 환경변수 → 사이드바 입력 순으로 확인 ──────
groq_key = (
    st.secrets.get("GROQ_API_KEY", "")
    if hasattr(st, "secrets")
    else ""
) or os.environ.get("GROQ_API_KEY", "")

if not groq_key:
    groq_key = st.sidebar.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="groq.com에서 무료로 발급받으세요",
    )
    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    else:
        st.warning("사이드바에 Groq API 키를 입력하세요. groq.com에서 무료로 발급받을 수 있습니다.")
        st.stop()
else:
    os.environ["GROQ_API_KEY"] = groq_key


@st.cache_resource(show_spinner="독서로 FAQ 문서를 분석하는 중... (최초 1회, 약 30초)")
def init_chain():
    vs = build_vectorstore_in_memory()
    return build_qa_chain(vs)


chain = init_chain()

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 자주 묻는 질문")
    quick_questions = [
        "독서로 회원가입 방법",
        "DLS 인증은 어떻게 하나요?",
        "독후활동 작성 방법",
        "대출불가 오류 해결",
        "독서이음활동이란?",
        "나이스 자동 연동 되나요?",
        "아이디 비밀번호 분실",
        "학교관리자 로그인 방법",
        "독서활동 PDF 출력 방법",
        "손글씨 독후감 업로드 방법",
    ]
    for q in quick_questions:
        if st.button(q, use_container_width=True):
            st.session_state.quick_input = q

    st.markdown("---")
    st.markdown("**독서로 바로가기**")
    st.markdown("- [독서로 사이트](https://read365.edunet.net)")
    st.markdown("- [학교관리자](https://read365-school.edunet.net)")
    st.markdown("- 에듀콜센터: **1544-0079**")

    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── 채팅 히스토리 ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "안녕하세요! 독서로 FAQ 챗봇입니다. 📚\n\n"
                "독서로 회원가입, DLS 인증, 독후활동, 교사 관리 기능 등 "
                "궁금한 점을 무엇이든 물어보세요!\n\n"
                "왼쪽 사이드바의 빠른 질문 버튼을 활용하셔도 됩니다."
            ),
        }
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("참고 문서 보기"):
                for i, src in enumerate(msg["sources"], 1):
                    st.markdown(
                        f'<div class="source-box">{i}. {src}...</div>',
                        unsafe_allow_html=True,
                    )

# ── 입력 처리 ─────────────────────────────────────────────────────────────────
if "quick_input" in st.session_state:
    user_input = st.session_state.pop("quick_input")
else:
    user_input = st.chat_input("질문을 입력하세요... (예: DLS 인증 방법이 뭔가요?)")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("독서로 FAQ에서 답변을 찾는 중..."):
            result = answer(user_input, chain)
            response = result["answer"]
            sources = result["sources"]

        st.markdown(response)

        if sources:
            with st.expander("참고 문서 보기"):
                for i, src in enumerate(sources, 1):
                    st.markdown(
                        f'<div class="source-box">{i}. {src}...</div>',
                        unsafe_allow_html=True,
                    )

    st.session_state.messages.append(
        {"role": "assistant", "content": response, "sources": sources}
    )

st.markdown("---")
st.markdown(
    """
    <div class="tip-box">
    💡 <b>RAG(검색 기반 AI) 챗봇</b> — 독서로 FAQ 문서를 벡터 검색으로 찾아 AI가 답변합니다.<br>
    정확한 최신 정보는 <a href="https://read365.edunet.net" target="_blank">독서로 공식 사이트</a>에서 확인하세요.
    </div>
    """,
    unsafe_allow_html=True,
)
