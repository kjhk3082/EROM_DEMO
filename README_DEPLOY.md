# 🚀 춘천시 AI 챗봇 - 빠른 배포 가이드

## 📱 Streamlit Cloud 배포 (가장 쉽고 빠름!)

### 1단계: GitHub 저장소 Fork 또는 Clone
```bash
# 이 저장소를 Fork하거나 Clone하세요
git clone https://github.com/prompton-EROM/EROM_DEMO.git
cd EROM_DEMO
```

### 2단계: Streamlit Cloud 배포
1. **Streamlit Cloud 접속**: https://share.streamlit.io/
2. **GitHub 로그인**: GitHub 계정으로 로그인
3. **"New app" 클릭**
4. 설정:
   - Repository: `prompton-EROM/EROM_DEMO` (또는 본인의 Fork)
   - Branch: `main`
   - Main file path: `streamlit_app.py`
5. **"Deploy!" 클릭**

### 3단계: API 키 설정 (중요!)

#### Streamlit Cloud Secrets 설정:
1. 배포된 앱의 Settings (⚙️) 클릭
2. "Secrets" 섹션으로 이동
3. 아래 내용 입력:

```toml
# OpenAI API 키 (필수)
OPENAI_API_KEY = "sk-..."

# Tavily API 키 (선택, 웹 검색용)
TAVILY_API_KEY = "tvly-..."
```

### 🔑 API 키 무료 발급 방법

#### OpenAI API 키:
1. https://platform.openai.com/signup 가입
2. https://platform.openai.com/api-keys 접속
3. "Create new secret key" 클릭
4. 키 복사 (sk-로 시작)

#### Tavily API 키 (선택):
1. https://tavily.com 가입
2. Dashboard에서 API Key 복사
3. 무료: 1,000 검색/월

---

## ⚡ 로컬 테스트 (선택사항)

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
echo "OPENAI_API_KEY=sk-your-key" > .env
echo "TAVILY_API_KEY=tvly-your-key" >> .env

# 실행
streamlit run streamlit_app.py
```

---

## 🌐 배포된 앱 URL

배포 완료 후:
```
https://[your-app-name].streamlit.app
```

---

## ❓ 문제 해결

### API 키 오류:
- Settings > Secrets에서 키가 올바르게 입력되었는지 확인
- OpenAI 계정에 크레딧이 있는지 확인

### 앱이 느린 경우:
- 첫 실행시 데이터 로딩에 시간이 걸릴 수 있음
- 무료 티어는 리소스 제한이 있음

---

## 📞 지원

문제가 있으면 Issues에 남겨주세요:
https://github.com/prompton-EROM/EROM_DEMO/issues

---

**🎉 5분 안에 배포 완료!**