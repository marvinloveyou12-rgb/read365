---
title: 독서로 FAQ 챗봇 API
emoji: 📚
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 독서로 FAQ 챗봇

| 역할 | 주소 |
|------|------|
| 프론트엔드 (화면) | https://marvinloveyou12-rgb.github.io/read365/ |
| 백엔드 API | https://dongle0516-read365.hf.space |

## 구조

```
GitHub Pages (화면)  →  HuggingFace Space (AI 백엔드)
docs/index.html          main.py (FastAPI)
docs/style.css           rag_engine.py (RAG)
docs/app.js              Dockerfile
```

## HuggingFace Space 설정

Space → Settings → Variables and secrets → New secret

| Name | Value |
|------|-------|
| `GROQ_API_KEY` | groq.com에서 발급한 키 |

## GitHub Pages 설정

repo Settings → Pages → Source: `main` 브랜치 → `/docs` 폴더
