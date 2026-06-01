# 독서로 FAQ 챗봇 📚

독서로(read365.edunet.net) FAQ 문서를 기반으로 선생님들의 질문에 AI가 답변하는 챗봇입니다.  
**완전 무료**로 운영 가능합니다.

## 무료 기술 스택

| 역할 | 기술 | 비용 |
|------|------|------|
| 웹 UI | Streamlit | 무료 |
| 호스팅 | Streamlit Cloud | 무료 |
| 임베딩(벡터 변환) | HuggingFace sentence-transformers | 무료 |
| AI 답변 생성 | Groq API (llama-3.3-70b) | 무료 티어 |
| 벡터 검색 | FAISS | 무료 |

## 배포 방법 (무료)

### 1단계: Groq API 키 발급 (무료)
1. [groq.com](https://groq.com) 접속 → 회원가입
2. API Keys → Create API Key
3. 키 복사 (`gsk_...` 형식)

### 2단계: GitHub 저장소 업로드
```bash
git init
git add .
git commit -m "독서로 FAQ 챗봇 초기 배포"
git branch -M main
git remote add origin https://github.com/아이디/저장소명.git
git push -u origin main
```

### 3단계: Streamlit Cloud 배포
1. [share.streamlit.io](https://share.streamlit.io) 접속 → GitHub 로그인
2. **New app** → GitHub 저장소 선택 → `app.py` 선택
3. **Advanced settings → Secrets**에 아래 내용 입력:
   ```
   GROQ_API_KEY = "gsk_여기에_실제_키"
   ```
4. **Deploy** 클릭 → 약 3분 후 배포 완료
5. URL: `https://앱이름.streamlit.app`

## 로컬 실행 방법

```bash
pip install -r requirements.txt

# .streamlit/secrets.toml 파일 생성
mkdir .streamlit
echo 'GROQ_API_KEY = "gsk_실제키"' > .streamlit/secrets.toml

streamlit run app.py
```

## 문서 추가 방법

`data/` 폴더에 PDF 파일을 넣으면 자동으로 학습됩니다:

```bash
cp "독서로 영역 FAQ_V4.pdf" data/
cp "독서로 이용자 매뉴얼_2026.pdf" data/
```

GitHub에 push하면 Streamlit Cloud가 자동으로 재배포합니다.
