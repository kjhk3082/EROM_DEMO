# 🚀 춘천시 AI 챗봇 배포 가이드

## 📋 배포 옵션 요약

| 플랫폼 | 난이도 | 무료 티어 | 장점 | 단점 |
|--------|--------|-----------|------|------|
| **Streamlit Cloud** | ⭐ 쉬움 | ✅ 무제한 | 배포 간단, 자동 업데이트 | Streamlit 앱만 가능 |
| **Render** | ⭐⭐ 보통 | ✅ 750시간/월 | Flask 직접 실행, 안정적 | 무료 티어 제한 |
| **Railway** | ⭐⭐ 보통 | ✅ $5 크레딧 | 빠른 배포, 좋은 성능 | 크레딧 소진시 유료 |
| **Vercel** | ⭐⭐⭐ 어려움 | ✅ 무제한 | 무료 호스팅, 빠른 속도 | 서버리스 제약 |

---

## 🎯 Option 1: Streamlit Cloud (가장 쉬움) 

### 1. GitHub 저장소 준비
```bash
# 로컬에서
cd /home/user/webapp
git init
git add .
git commit -m "Initial commit for Streamlit deployment"
git remote add origin https://github.com/YOUR_USERNAME/chuncheon-chatbot.git
git push -u origin main
```

### 2. Streamlit Cloud 배포
1. https://streamlit.io/cloud 접속
2. GitHub 계정으로 로그인
3. "New app" 클릭
4. Repository: `YOUR_USERNAME/chuncheon-chatbot`
5. Branch: `main`
6. Main file path: `streamlit_app.py`
7. "Deploy" 클릭

### 3. 환경변수 설정 (Streamlit Cloud)
1. 앱 대시보드에서 "Settings" 클릭
2. "Secrets" 섹션에서 다음 추가:
```toml
OPENAI_API_KEY = "your-openai-api-key"
TAVILY_API_KEY = "your-tavily-api-key"
```

### 배포 URL
```
https://YOUR_APP_NAME.streamlit.app
```

---

## 🔧 Option 2: Render.com (Flask 앱)

### 1. GitHub 저장소 준비 (위와 동일)

### 2. Render 배포
1. https://render.com 접속 및 가입
2. Dashboard에서 "New +" → "Web Service"
3. GitHub 저장소 연결
4. 설정:
   - Name: `chuncheon-chatbot`
   - Environment: `Python`
   - Build Command: `pip install -r requirements_enhanced.txt`
   - Start Command: `python enhanced_web_chatbot.py`

### 3. 환경변수 설정 (Render)
Dashboard → Environment에서:
- `OPENAI_API_KEY`: your-key
- `TAVILY_API_KEY`: your-key
- `PORT`: 8080

### 배포 URL
```
https://chuncheon-chatbot.onrender.com
```

---

## 🚄 Option 3: Railway.app

### 1. Railway CLI 설치
```bash
# macOS/Linux
curl -fsSL https://railway.app/install.sh | sh

# Windows
scoop install railway
```

### 2. 배포
```bash
cd /home/user/webapp
railway login
railway init
railway up
```

### 3. 환경변수 설정 (Railway)
```bash
railway variables set OPENAI_API_KEY="your-key"
railway variables set TAVILY_API_KEY="your-key"
```

### 배포 URL
```
https://chuncheon-chatbot.up.railway.app
```

---

## ⚡ Option 4: Vercel (서버리스)

### 1. Vercel CLI 설치
```bash
npm install -g vercel
```

### 2. 배포
```bash
cd /home/user/webapp
vercel
```

### 3. 환경변수 설정
```bash
vercel env add OPENAI_API_KEY
vercel env add TAVILY_API_KEY
```

### 배포 URL
```
https://chuncheon-chatbot.vercel.app
```

---

## 🔐 환경변수 보안 가이드

### 필수 환경변수
```env
# OpenAI API (필수)
OPENAI_API_KEY=sk-...

# Tavily Search API (선택사항, 웹 검색용)
TAVILY_API_KEY=tvly-...

# Flask 보안 키 (자동 생성 가능)
FLASK_SECRET_KEY=your-secret-key-here

# 포트 설정 (플랫폼별 자동 설정)
PORT=8080
```

### API 키 획득 방법

#### OpenAI API Key
1. https://platform.openai.com 접속
2. 계정 생성/로그인
3. API Keys 섹션에서 새 키 생성
4. 사용량 제한 설정 권장 ($10-20/월)

#### Tavily API Key
1. https://tavily.com 접속
2. 무료 계정 생성
3. Dashboard에서 API Key 복사
4. 무료 티어: 1,000 검색/월

---

## 🛠️ 로컬 테스트

### 1. 환경 설정
```bash
cd /home/user/webapp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements_enhanced.txt
```

### 2. 환경변수 파일 생성
```bash
cat > .env << EOF
OPENAI_API_KEY=your-key
TAVILY_API_KEY=your-key
FLASK_SECRET_KEY=your-secret
EOF
```

### 3. 실행
```bash
# Flask 앱
python enhanced_web_chatbot.py

# Streamlit 앱
streamlit run streamlit_app.py
```

---

## 📊 데이터 관리

### ChromaDB 초기화
배포 후 첫 실행시 자동으로 벡터 DB가 생성됩니다.
데이터는 `./chroma_db` 디렉토리에 저장됩니다.

### CSV 데이터 업데이트
1. `dataSet/`, `dataset2/`, `민원 관련/` 폴더에 CSV 파일 추가
2. 서버 재시작 또는 `/initialize` 엔드포인트 호출
3. 자동으로 벡터 DB 업데이트

---

## 🚨 문제 해결

### 1. 메모리 부족 오류
```python
# enhanced_web_chatbot.py에서 chunk_size 조정
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # 1000에서 줄임
    chunk_overlap=100  # 200에서 줄임
)
```

### 2. API 호출 제한
```python
# 응답 캐싱 추가
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_response(question):
    return chatbot.chat(question, [])
```

### 3. 느린 초기 로딩
- 벡터 DB를 미리 생성하여 배포
- 작은 데이터셋으로 시작

---

## 📈 성능 최적화

### 1. 프로덕션 설정
```python
# Flask 프로덕션 모드
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8080)
```

### 2. 데이터베이스 최적화
```python
# 벡터 스토어 최적화
vectorstore = Chroma(
    embedding_function=embeddings,
    persist_directory="./chroma_db",
    collection_metadata={"hnsw:space": "cosine"}
)
```

### 3. 캐싱 전략
- Redis 캐싱 추가 (선택사항)
- 정적 파일 CDN 사용
- 응답 캐싱

---

## 🎯 추천 배포 전략

### 개발/테스트용
→ **Streamlit Cloud** (무료, 간단)

### 프로덕션용
→ **Render.com** (안정적, Flask 지원)

### 대규모 트래픽
→ **AWS/GCP/Azure** (확장 가능)

---

## 📞 지원

배포 관련 문의사항이 있으시면 GitHub Issues에 남겨주세요.
https://github.com/YOUR_USERNAME/chuncheon-chatbot/issues

---

*마지막 업데이트: 2025년 1월*