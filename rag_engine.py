"""
독서로 RAG 엔진 — 무료 스택
- 임베딩: HuggingFace sentence-transformers (로컬, 무료)
- LLM:    Groq API (무료 티어)
- 벡터DB: FAISS (인메모리)
"""

import os
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

DATA_DIR = Path(__file__).parent / "data"

SYSTEM_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""당신은 독서로(read365.edunet.net) 활용을 돕는 전문 안내 챗봇입니다.
아래 제공된 독서로 FAQ 문서를 바탕으로 선생님의 질문에 친절하고 정확하게 답변해 주세요.

규칙:
- 문서에 있는 내용만 답변하세요
- 문서에 없는 내용은 "해당 내용은 독서로 FAQ에서 찾을 수 없습니다. 독서로 사이트 내 1:1 문의 또는 에듀콜센터(1544-0079)에 문의해 주세요."라고 안내하세요
- 단계별 안내가 필요한 경우 번호를 사용하세요
- 답변 마지막에 관련 FAQ 번호를 표시하세요 (예: 참고: FAQ Q16)

[참고 문서]
{context}

[질문]
{question}

[답변]""",
)


def load_documents() -> list:
    docs = []
    for txt_file in DATA_DIR.glob("*.txt"):
        loader = TextLoader(str(txt_file), encoding="utf-8")
        docs.extend(loader.load())
    for pdf_file in DATA_DIR.glob("*.pdf"):
        loader = PyPDFLoader(str(pdf_file))
        docs.extend(loader.load())
    return docs


def build_vectorstore_in_memory() -> FAISS:
    """문서를 로드해 인메모리 FAISS 벡터 DB를 생성합니다."""
    docs = load_documents()
    if not docs:
        raise FileNotFoundError(f"data 폴더에 문서가 없습니다: {DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n"],
    )
    chunks = splitter.split_documents(docs)

    # 다국어(한국어 포함) 무료 임베딩 모델
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return FAISS.from_documents(chunks, embeddings)


def build_qa_chain(vectorstore: FAISS) -> RetrievalQA:
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        raise ValueError("GROQ_API_KEY 환경변수가 설정되지 않았습니다.")

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=groq_key,
    )
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": SYSTEM_PROMPT},
        return_source_documents=True,
    )


def answer(question: str, chain: RetrievalQA) -> dict:
    result = chain.invoke({"query": question})
    return {
        "answer": result["result"],
        "sources": [doc.page_content[:200] for doc in result["source_documents"]],
    }
