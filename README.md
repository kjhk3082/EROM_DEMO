# 춘천시 AI 챗봇 🌸

강원특별자치도 춘천시 전문 AI 가이드 챗봇입니다. LangChain과 RAG(Retrieval-Augmented Generation) 시스템을 기반으로 구축되었습니다.

## 주요 기능

- 🏛️ **행정기관 정보**: 춘천시청, 공공시설 안내
- 🍽️ **맛집 & 특산품**: 닭갈비, 막국수 맛집 추천
- 🎪 **관광명소**: 남이섬, 춘천호 등 관광지 정보
- 🚌 **교통정보**: 춘천역, 버스터미널, 시내버스 안내
- 📞 **연락처 안내**: 각종 시설 전화번호 및 주소 제공

## 시스템 구조

```
춘천시 AI 챗봇
├── data_collector.py    # 춘천시 데이터 수집
├── vector_store.py      # RAG용 벡터 스토어
├── chatbot.py          # 메인 챗봇 클래스
├── streamlit_app.py    # 웹 인터페이스
└── requirements.txt    # 의존성 패키지
```

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
```

### 3. 데이터 수집 및 벡터 스토어 구축

```bash
# 춘천시 데이터 수집
python data_collector.py

# 벡터 스토어 구축
python vector_store.py
```

### 4. 챗봇 실행

#### 터미널에서 실행
```bash
python chatbot.py
```

#### 웹 인터페이스 실행
```bash
streamlit run streamlit_app.py
```

## 사용 예시

### 질문 예시
- "춘천 닭갈비 맛집 추천해줘"
- "남이섬 가는 방법 알려줘"
- "춘천시청 연락처는?"
- "막국수 체험할 수 있는 곳"

### 응답 예시
```
춘천의 대표 닭갈비 맛집을 추천해드릴게요!

1. 춘천닭갈비골목
   📞 033-252-9995
   📍 강원특별자치도 춘천시 조양동
   🍗 춘천의 대표 음식 닭갈비 전문거리

2. 춘천명동닭갈비
   📞 033-253-6600
   📍 강원특별자치도 춘천시 명동길 9
   🍗 50년 전통의 닭갈비 전문점
```

## 기술 스택

- **LLM**: OpenAI GPT-4 (o1-mini 대체)
- **RAG**: LangChain + FAISS 벡터 스토어
- **임베딩**: HuggingFace ko-sroberta-multitask
- **웹 인터페이스**: Streamlit
- **데이터 처리**: pandas, BeautifulSoup

## 데이터 소스

현재 포함된 춘천시 정보:
- 행정기관 (춘천시청, 시립도서관, 시민회관)
- 관광지 (남이섬, 춘천호)
- 맛집 (닭갈비골목, 막국수체험박물관)
- 교통시설 (춘천역, 터미널, 시내버스)
- 전통시장 (춘천중앙시장)

## 확장 가능성

- 실시간 웹 크롤링으로 최신 정보 업데이트
- 공공 API 연동 (관광공사, 지자체 API)
- 다국어 지원 (영어, 중국어, 일본어)
- 음성 인터페이스 추가
- 지도 연동 및 길찾기 기능

## 문제 해결

### API 키 오류
```
ValueError: OPENAI_API_KEY가 설정되지 않았습니다.
```
→ `.env` 파일에 올바른 OpenAI API 키를 설정하세요.

### 벡터 스토어 오류
```
벡터 스토어 로드 실패
```
→ `python vector_store.py`를 실행하여 벡터 스토어를 재구축하세요.

### 의존성 오류
```
ModuleNotFoundError
```
→ `pip install -r requirements.txt`로 모든 패키지를 설치하세요.

## 라이선스

이 프로젝트는 교육 목적으로 제작되었습니다.

## 기여

버그 리포트나 기능 제안은 언제든 환영합니다!

---

**춘천시 AI 챗봇과 함께 춘천의 모든 것을 탐험해보세요! 🌸**
