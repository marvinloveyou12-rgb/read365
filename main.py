import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_engine import build_vectorstore_in_memory, build_qa_chain, answer as rag_answer

chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global chain
    print("RAG 엔진 초기화 중...")
    vs = build_vectorstore_in_memory()
    chain = build_qa_chain(vs)
    print("준비 완료!")
    yield


app = FastAPI(title="독서로 FAQ 챗봇 API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://marvinloveyou12-rgb.github.io",
        "http://localhost:3000",
        "http://localhost:5500",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not chain:
        raise HTTPException(status_code=503, detail="준비 중입니다. 잠시 후 다시 시도해 주세요.")
    result = rag_answer(req.message, chain)
    return ChatResponse(answer=result["answer"], sources=result["sources"])


@app.get("/health")
async def health():
    return {"status": "ok", "ready": chain is not None}
