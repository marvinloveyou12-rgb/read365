"""
독서로 RAG 엔진 — 완전 무료 스택
- 임베딩: HuggingFace sentence-transformers (로컬, 무료)
- LLM:    HuggingFace Inference API text_generation (무료 티어)
- 벡터DB: FAISS (인메모리)
"""

import os
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from huggingface_hub import InferenceClient

DATA_DIR = Path(__file__).parent / "data"

SYSTEM_MESSAGE = (
    "당신은 한국 교육 독서 플랫폼 '독서로'(read365.edunet.net)의 FAQ 도우미입니다. "
    "아래 FAQ 문서만을 바탕으로 선생님의 질문에 한국어로 답하세요. "
    "문서에 없는 내용은 '해당 내용은 독서로 FAQ에서 찾을 수 없습니다. "
    "에듀콜센터(1544-0079)에 문의해 주세요.'라고 답하세요. "
    "절차 설명 시 번호를 붙여 단계별로 안내하세요. "
    "답변 마지막에 반드시 문서의 [출처: ...] 정보를 그대로 포함하세요."
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
    docs = load_documents()
    if not docs:
        raise FileNotFoundError(f"data 폴더에 문서가 없습니다: {DATA_DIR}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n"],
    )
    chunks = splitter.split_documents(docs)

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return FAISS.from_documents(chunks, embeddings)


def build_qa_chain(vectorstore: FAISS) -> dict:
    hf_token = os.environ.get("HF_TOKEN", "")

    client = None
    if hf_token:
        try:
            client = InferenceClient(
                model="mistralai/Mistral-7B-Instruct-v0.3",
                token=hf_token,
            )
        except Exception as e:
            print(f"InferenceClient 초기화 실패, 검색 전용 모드로 실행: {e}")

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )

    return {"client": client, "retriever": retriever}


def _extract_source_tag(text: str) -> str:
    """텍스트에서 [출처: ...] 태그를 추출"""
    import re
    match = re.search(r'\[출처:[^\]]+\]', text)
    return match.group(0) if match else ""


def _fallback_answer(source_docs: list) -> str:
    """LLM 없이 검색된 FAQ 원문을 직접 반환 (출처 포함)"""
    if not source_docs:
        return (
            "해당 내용은 독서로 FAQ에서 찾을 수 없습니다.\n"
            "독서로 사이트 내 1:1 문의 또는 에듀콜센터(1544-0079)에 문의해 주세요."
        )
    parts = []
    for doc in source_docs[:2]:
        parts.append(doc.page_content.strip())
    return "\n\n─────────────────\n\n".join(parts)


def answer(question: str, chain: dict) -> dict:
    client = chain.get("client")
    retriever = chain["retriever"]

    source_docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in source_docs)

    # 출처 태그 수집
    source_tags = []
    for doc in source_docs:
        tag = _extract_source_tag(doc.page_content)
        if tag and tag not in source_tags:
            source_tags.append(tag)

    if client:
        try:
            prompt = (
                f"<s>[INST] {SYSTEM_MESSAGE}\n\n"
                f"[FAQ 문서]\n{context}\n\n"
                f"[질문]\n{question} [/INST]"
            )
            result = client.text_generation(
                prompt=prompt,
                max_new_tokens=512,
                temperature=0.1,
                return_full_text=False,
            )
            answer_text = result.strip()
        except Exception as e:
            print(f"LLM 오류, FAQ 원문 반환: {e}")
            answer_text = _fallback_answer(source_docs)
    else:
        answer_text = _fallback_answer(source_docs)

    return {
        "answer": answer_text,
        "sources": [doc.page_content[:200] for doc in source_docs],
        "source_tags": source_tags,
    }
