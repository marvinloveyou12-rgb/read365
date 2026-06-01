"""
독서로 RAG 엔진 — 완전 무료 스택
- 임베딩: HuggingFace sentence-transformers (로컬, 무료)
- LLM:    HuggingFace Inference API (무료 티어)
- 벡터DB: FAISS (인메모리)
"""

import os
from pathlib import Path

from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpoint
from langchain_community.vectorstores import FAISS

DATA_DIR = Path(__file__).parent / "data"

PROMPT_TEMPLATE = """You are a helpful assistant for the Korean educational reading platform '독서로' (read365.edunet.net).
Answer the teacher's question in Korean based only on the FAQ documents provided below.

Rules:
- Answer only from the provided documents
- If the answer is not in the documents, say: "해당 내용은 독서로 FAQ에서 찾을 수 없습니다. 독서로 사이트 내 1:1 문의 또는 에듀콜센터(1544-0079)에 문의해 주세요."
- Use numbered steps when explaining procedures
- Mention the relevant FAQ number at the end (e.g., 참고: FAQ Q16)
- Always respond in Korean

[FAQ Documents]
{context}

[Question]
{question}

[Answer in Korean]"""


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
    if not hf_token:
        raise ValueError("HF_TOKEN 환경변수가 설정되지 않았습니다.")

    os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_token

    llm = HuggingFaceEndpoint(
        repo_id="mistralai/Mistral-7B-Instruct-v0.3",
        task="text-generation",
        max_new_tokens=512,
        temperature=0.1,
    )

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )

    return {"llm": llm, "retriever": retriever}


def answer(question: str, chain: dict) -> dict:
    llm = chain["llm"]
    retriever = chain["retriever"]

    source_docs = retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in source_docs)

    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    result = llm.invoke(prompt)

    return {
        "answer": result,
        "sources": [doc.page_content[:200] for doc in source_docs],
    }
