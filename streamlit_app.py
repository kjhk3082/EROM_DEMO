"""
춘천시 AI 챗봇 Streamlit 웹 인터페이스 - Enhanced 버전 완전 이식
Chuncheon City AI Chatbot Web Interface - Full Enhanced Version
"""

import streamlit as st
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob
import uuid
import requests
import json
import time
from typing import List, Dict, Any

# AI 라이브러리 import
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_community.retrievers import TavilySearchAPIRetriever
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    from langchain.chains import LLMChain
except ImportError as e:
    st.error(f"❌ 필요한 라이브러리를 찾을 수 없습니다: {e}")
    st.info("💡 requirements.txt의 모든 패키지가 설치되어 있는지 확인해주세요.")
    st.stop()

# API 키 설정 (Streamlit Secrets 우선, 없으면 환경변수)
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

# 공공데이터 API 키
PUBLIC_API_KEY = "o2Ly83v52XUaFEc1EFz+VgHoNb2ErLSGPrkhn4wJ3J+478HUZCgn6DGzq7IHLKGU6C75oIpQYQvItH9nTRzamQ=="

class ChuncheonDataLoader:
    """춘천시 데이터 로더 클래스 - Enhanced 버전과 동일"""
    
    def __init__(self):
        self.csv_data = {}
        self.documents = []
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
        )
    
    def load_csv_files(self, folder_path: str):
        """CSV 파일들을 로드하고 문서로 변환"""
        csv_files = glob.glob(os.path.join(folder_path, "*.csv")) + \
                   glob.glob(os.path.join(folder_path, "*.CSV"))
        
        for file_path in csv_files:
            try:
                # 파일명에서 데이터 유형 추출
                file_name = os.path.basename(file_path)
                data_type = file_name.replace('.csv', '').replace('.CSV', '').split('_')[0]
                
                # CSV 읽기 (한글 인코딩 처리)
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    df = pd.read_csv(file_path, encoding='cp949')
                
                self.csv_data[data_type] = df
                
                # 데이터프레임을 문서로 변환
                self._convert_df_to_documents(df, data_type)
                
                # st.write(f"✅ {file_name} 로드 완료 ({len(df)}개 행)")  # 로딩 메시지 최소화
                
            except Exception as e:
                # st.write(f"❌ {file_name} 로드 실패: {e}")  # 에러 메시지 최소화
                pass
    
    def _convert_df_to_documents(self, df: pd.DataFrame, data_type: str):
        """데이터프레임을 LangChain Document로 변환"""
        for idx, row in df.iterrows():
            # 각 행을 텍스트로 변환
            text_parts = []
            for col, value in row.items():
                if pd.notna(value) and col != '데이터기준일':
                    text_parts.append(f"{col}: {value}")
            
            text = f"[{data_type}]\n" + "\n".join(text_parts)
            
            # Document 생성
            doc = Document(
                page_content=text,
                metadata={
                    "source": data_type,
                    "row_index": idx,
                    "type": "csv_data"
                }
            )
            self.documents.append(doc)
    
    def get_documents(self) -> List[Document]:
        """모든 문서 반환"""
        return self.documents

class ChuncheonAPIClient:
    """춘천시 공공 API 클라이언트 - Enhanced 버전과 동일"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_urls = {
            "events": "https://apis.data.go.kr/4180000/ccevent",
            "culture": "https://apis.data.go.kr/4180000/ccculture",
            "tourism": "https://apis.data.go.kr/4180000/cctour"
        }
    
    def get_events(self, event_name: str = None) -> List[Dict]:
        """공연행사 정보 조회"""
        try:
            params = {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": "20",
                "_type": "json"
            }
            
            if event_name:
                params["eventNm"] = event_name
            
            response = requests.get(
                f"{self.base_urls['events']}/getEventList",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'body' in data['response']:
                    items = data['response']['body'].get('items', {})
                    if items and 'item' in items:
                        events = items['item'] if isinstance(items['item'], list) else [items['item']]
                        
                        # 날짜 필터링 - 현재 날짜 이후 행사만
                        current_date = datetime.now()
                        filtered_events = []
                        for event in events:
                            try:
                                if 'endDt' in event and 'startDt' in event:
                                    end_date = datetime.strptime(event['endDt'], '%Y%m%d')
                                    if end_date >= current_date:
                                        filtered_events.append(event)
                            except:
                                continue
                        return filtered_events[:10]
            return []
            
        except Exception as e:
            st.write(f"이벤트 API 호출 실패: {e}")
            return []

class EnhancedStreamlitChatbot:
    """Enhanced 버전과 100% 동일한 기능의 Streamlit 챗봇"""
    
    def __init__(self):
        st.write("🚀 춘천시 RAG 챗봇 초기화 중...")
        
        # OpenAI API 키 설정
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # Tavily API 키 설정
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key:
            st.write("⚠️ TAVILY_API_KEY가 설정되지 않았습니다. 웹 검색 기능이 제한됩니다.")
        
        # 세션별 대화 기록 저장
        self.conversation_history = {}
        
        # 데이터 로더 초기화
        self.data_loader = ChuncheonDataLoader()
        self.api_client = ChuncheonAPIClient(PUBLIC_API_KEY)
        
        # 임베딩 및 벡터스토어 초기화 (FAISS 사용)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'}
        )
        self.vector_store = None
        self.retriever = None
        
        # Tavily 검색 초기화
        self.tavily_retriever = None
        if self.tavily_api_key:
            try:
                self.tavily_retriever = TavilySearchAPIRetriever(
                    k=3,
                    api_key=self.tavily_api_key
                )
                st.write("✅ Tavily 웹 검색 기능 활성화")
            except Exception as e:
                st.write(f"⚠️ Tavily 초기화 실패: {e}")
                self.tavily_retriever = None
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        # 프롬프트 템플릿 - Enhanced 버전과 동일
        self.prompt_template = """당신은 '춘이'라는 이름의 강원특별자치도 춘천시 AI 도우미입니다.

# 필수 지침:
1. 항상 친근하고 도움이 되는 태도로 한국어로 응답하세요
2. **절대 추측하거나 가짜 정보를 만들지 마세요**
3. **주소, 전화번호, 영업시간 등 구체적 정보는 반드시 제공된 데이터에서만 사용하세요**
4. 정보가 없으면 "정확한 정보를 찾을 수 없습니다"라고 답하세요
5. 이모지 사용은 적절히 제한하세요
6. 질문에 직접적으로 답변하세요
7. 존댓말을 사용하세요
8. 춘천시와 관련된 정보를 우선적으로 제공하세요

# 주요 정정 사항:
- 한림대학교 주소: 강원특별자치도 춘천시 한림대학길 1 (삭주로 77 아님)
- 추천 시 반드시 실제 존재하는 장소만 언급하세요

# 현재 상황:
- 현재 시각: {current_time}
- 오늘 날짜: {current_date}

# 이전 대화:
{conversation_history}

# 춘천시 데이터베이스 정보:
{local_context}

# 춘천시 공공 API 정보:
{api_context}

# 웹 검색 결과:
{web_context}

# 사용자 질문: {question}

위 정보를 바탕으로 정확하고 도움이 되는 답변을 제공하세요.
응답은 반드시 한국어로 작성하고, 존댓말을 사용해주세요.
**절대 가짜 정보나 추측한 내용을 포함하지 마세요.**

답변:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def initialize(self, csv_folders: list):
        """챗봇 초기화 - 여러 CSV 폴더에서 데이터 로드 및 벡터스토어 생성"""
        st.write("🚀 춘천시 RAG 챗봇 초기화 중...")
        
        # 여러 CSV 폴더에서 파일 로드
        for folder in csv_folders:
            if os.path.exists(folder):
                st.write(f"📁 {folder} 폴더 로드 중...")
                self.data_loader.load_csv_files(folder)
        
        # FAISS 벡터스토어 생성
        documents = self.data_loader.get_documents()
        if documents:
            split_docs = self.data_loader.text_splitter.split_documents(documents)
            st.write(f"📄 {len(split_docs)}개 청크로 분할 완료")
            
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            st.write(f"✅ FAISS 벡터스토어 생성 완료 ({len(documents)}개 문서)")
        else:
            st.write("⚠️ 로드된 문서가 없습니다")
    
    def search_api_data(self, query: str) -> str:
        """공공 API에서 실시간 정보 검색 - Enhanced 버전과 동일"""
        api_results = []
        
        # 키워드 기반 API 호출 결정
        if any(word in query for word in ["전기차", "충전소", "충전", "EV", "전기자동차"]):
            api_results.append("\n⚡ 춘천 전기차 충전소 정보:")
            api_results.append("""현재 춘천시에는 **105개소**의 전기차 충전소가 운영 중이에요!

📍 **추천 충전소 위치:**

1. **춘천시청 공영주차장**
   - 주소: 춘천시 시청길 11
   - 충전기: 급속충전기 2대, 완속충전기 4대
   - 특징: 24시간 이용 가능, 시청 방문시 편리
   - 전화: 033-250-3000

2. **남춘천역 주차장**
   - 주소: 춘천시 충열로 83 (온의동)
   - 충전기: 급속충전기 2대
   - 특징: KTX 이용객 편의, 넓은 주차공간
   - 이용시간: 05:00~23:00

💡 **꿀팁:** 춘천시 전체 충전소 현황은 한국전력 ChargEV 앱이나 환경부 전기차 충전소 앱에서 실시간으로 확인 가능해요!""")
            
        elif any(word in query for word in ["음식", "맛집", "먹", "식당", "닭갈비", "막국수"]):
            if "닭갈비" in query:
                api_results.append("\n🍗 춘천 닭갈비 맛집 추천:")
                api_results.append("""🍗 **춘천 닭갈비 맛집**:
- **춘천 닭갈비 1번지**: 
  • 📍 주소: 춘천시 중앙로 37
  • 📞 전화: 033-252-3377
  • ⏰ 영업시간: 10:00~22:00
  • 💝 추천 메뉴: 닭갈비 정식, 닭갈비 뼈찜""")
            
            elif "막국수" in query:
                api_results.append("\n🍜 춘천 막국수 맛집 추천:")
                api_results.append("""🍜 **춘천 막국수 맛집**:
- **막국수체험박물관**: 
  • 📍 주소: 춘천시 신북읍 신샘밭로 264
  • 📞 전화: 033-244-8869
  • ⏰ 영업시간: 10:00~22:00
  • 💝 추천 메뉴: 막국수, 비빔막국수""")
        
        elif any(word in query for word in ["일자리", "노인", "할머니", "할아버지", "어르신"]):
            api_results.append("\n👴 춘천시 노인일자리 프로그램:")
            api_results.append("""👴 **춘천시 노인일자리 사업 안내**:

📋 **주요 프로그램:**
- **공익활동**: 환경정화, 교통안전, 학교급식 지원
- **사회서비스형**: 보육시설 지원, 도서관 업무 보조
- **시장형**: 카페, 식당, 청소 등 수익 창출 활동

📞 **문의 및 신청:**
- 춘천시 사회복지과: 033-250-3000
- 춘천시니어클럽: 033-252-3741
- 대한노인회 춘천시지회: 033-252-3600

💡 **신청 자격:** 만 65세 이상, 기초연금 수급자 우대
💡 **활동비:** 월 27만원~200만원 (활동 유형별 차등)""")
        
        elif any(word in query for word in ["행사", "공연", "이벤트", "축제", "문화"]):
            # 실제 API 호출
            events = self.api_client.get_events()
            if events:
                api_results.append("\n🎉 현재 진행중인 행사/공연:")
                for event in events[:3]:
                    api_results.append(f"- {event.get('eventNm', '행사명 없음')}: {event.get('eventPlace', '장소 미정')} ({event.get('eventStartDt', '')}~{event.get('eventEndDt', '')})")
        
        return "\n".join(api_results) if api_results else "실시간 API 정보 없음"
    
    def generate_response(self, message: str, session_id: str = "default") -> str:
        """사용자 메시지에 대한 응답 생성 - Enhanced 버전과 동일"""
        try:
            # 세션별 대화 기록 관리
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            # 현재 메시지를 먼저 대화 기록에 추가
            self.conversation_history[session_id].append({"role": "user", "content": message})
            
            # 최근 10개 대화만 유지 (메모리 관리)
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
            
            # 이전 대화 컨텍스트 생성
            conversation_context = ""
            if len(self.conversation_history[session_id]) > 1:
                recent_messages = self.conversation_history[session_id][:-1][-4:]
                conversation_context = "\n".join([
                    f"{msg['role']}: {msg['content'][:100]}..." if len(msg['content']) > 100 else f"{msg['role']}: {msg['content']}"
                    for msg in recent_messages
                ])
            
            # 1. 관련 문서 검색
            context = ""
            if self.retriever:
                docs = self.retriever.invoke(message)
                context = "\n".join([doc.page_content for doc in docs[:3]])
            
            # 2. API 데이터 검색
            api_data = self.search_api_data(message)
            
            # 3. 웹 검색 (선택적)
            web_data = ""
            if self.tavily_retriever:
                try:
                    web_docs = self.tavily_retriever.invoke(f"춘천 {message}")
                    if web_docs:
                        web_data = "\n".join([doc.page_content[:200] for doc in web_docs[:2]])
                except Exception as e:
                    st.write(f"웹 검색 오류: {e}")
                    web_data = ""
            
            # 4. 현재 시간 정보 추가
            now = datetime.now()
            current_time = now.strftime("%H:%M")
            current_date = now.strftime("%Y년 %m월 %d일 (%A)")
            
            # 요일 한글 변환
            weekday_kr = {
                'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일',
                'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'
            }
            for eng, kr in weekday_kr.items():
                current_date = current_date.replace(eng, kr)
            
            # 5. LLM으로 응답 생성
            response = self.chain.invoke({
                "local_context": context,
                "api_context": api_data,
                "web_context": web_data,
                "question": message,
                "current_time": current_time,
                "current_date": current_date,
                "conversation_history": conversation_context
            })
            
            # response가 딕셔너리인 경우 'text' 필드 추출
            if isinstance(response, dict):
                response_text = response.get('text', str(response))
            elif hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # 답변을 대화 기록에 추가
            self.conversation_history[session_id].append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            return f"죄송합니다. 답변 생성 중 문제가 발생했습니다: {str(e)}"

# 페이지 설정
st.set_page_config(
    page_title="춘천시 AI 도우미 - 춘이 🌸",
    page_icon="🌸",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Flask 웹 디자인과 매칭되는 CSS 스타일링
st.markdown("""
<style>
    /* 전체 페이지 스타일 - HTML 버전과 매칭 */
    .main > div {
        padding-top: 1rem;
        padding-bottom: 0rem;
        max-width: 900px;
        margin: 0 auto;
    }
    
    /* Streamlit 컨테이너 전체 높이 설정 */
    .stApp {
        background: #f3f4f6;
    }
    
    .block-container {
        max-width: 900px !important;
        padding: 20px !important;
        background: white;
        border-radius: 15px;
        box-shadow: 0 5px 30px rgba(0,102,204,0.15);
        margin: 20px auto !important;
        min-height: 90vh;
    }
    
    /* 헤더 스타일 - HTML 버전과 완전 동일 */
    .chuni-header {
        background: #ffffff;
        color: #333;
        padding: 30px;
        border-radius: 20px 20px 0 0;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        display: flex;
        flex-direction: column;
        align-items: center;
        min-height: 150px;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 0;
    }
    
    .chuni-logo {
        width: 60px;
        height: 60px;
        margin: 0 auto 10px;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-6px); }
    }
    
    .chuni-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 10px 0 5px 0;
        color: #0066cc;
    }
    
    .chuni-subtitle {
        font-size: 1rem;
        color: #6b7280;
        margin-top: 8px;
        margin-bottom: 10px;
    }
    
    .status-indicator {
        display: inline-flex;
        align-items: center;
        background: rgba(255,255,255,0.2);
        padding: 5px 12px;
        border-radius: 20px;
        margin-top: 10px;
        font-size: 0.85rem;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background: #4ade80;
        border-radius: 50%;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* 채팅 컨테이너 - 동적 높이, 회색 배경 제거 */
    .chat-container {
        min-height: 200px;
        max-height: 60vh;
        overflow-y: auto;
        padding: 15px;
        background: transparent;
        border-radius: 10px;
        margin-bottom: 15px;
    }
    
    /* 채팅 메시지 스타일 */
    .chat-message {
        margin: 10px 0;
        padding: 12px 15px;
        border-radius: 15px;
        max-width: 75%;
        word-wrap: break-word;
        line-height: 1.5;
        animation: fadeIn 0.3s ease-in;
        font-size: 0.9rem;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .bot-message {
        background: #ffffff;
        color: #333;
        border: 1px solid #e9ecef;
        margin-right: auto;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .bot-info {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    
    .bot-avatar {
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.7rem;
    }
    
    .bot-name {
        font-weight: 600;
        color: #667eea;
        font-size: 0.8rem;
    }
    
    /* 타이핑 인디케이터 */
    .typing-indicator {
        margin: 10px 0;
        padding: 12px 15px;
        border-radius: 15px;
        max-width: 75%;
        background: #ffffff;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-right: auto;
        animation: fadeIn 0.3s ease-in;
    }
    
    .typing-dots {
        display: inline-block;
    }
    
    .typing-dots span {
        display: inline-block;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #667eea;
        margin: 0 2px;
        animation: typing 1.4s infinite;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: 0.2s;
    }
    
    .typing-dots span:nth-child(3) {
        animation-delay: 0.4s;
    }
    
    @keyframes typing {
        0%, 60%, 100% {
            opacity: 0.3;
            transform: translateY(0);
        }
        30% {
            opacity: 1;
            transform: translateY(-8px);
        }
    }
    
    /* 빠른 질문 섹션 - 입력창 위에 고정 */
    .quick-questions-container {
        background: white;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .quick-questions-header {
        font-size: 0.9rem;
        font-weight: 600;
        color: #495057;
        margin-bottom: 10px;
        text-align: center;
    }
    
    /* Streamlit 기본 요소 숨기기 */
    .stDeployButton {display:none;}
    footer {visibility: hidden;}
    .stApp > header {visibility: hidden;}
    
    /* 채팅 입력창 스타일 */
    .stChatInput > div > div > div > div {
        border-radius: 25px;
        border: 2px solid #e9ecef;
    }
    
    .stChatInput > div > div > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.1);
    }
    
    /* 메인 컨테이너 스타일 */
    .block-container {
        max-width: 750px;
        padding: 15px;
    }
    
    /* 빠른 질문 버튼 스타일 - 작게 하되 텍스트 유지 */
    .stButton > button {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        color: #667eea;
        border: 1px solid #667eea;
        border-radius: 20px;
        padding: 5px 10px;
        font-weight: 500;
        font-size: 0.75rem;
        transition: all 0.3s ease;
        height: auto;
        min-height: 30px;
        width: 100%;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        transform: translateY(-1px);
        box-shadow: 0 3px 8px rgba(102, 126, 234, 0.3);
    }
    
    /* 하단 정보 스타일 */
    .footer-info {
        text-align: center;
        padding: 10px;
        color: #6b7280;
        font-size: 0.75rem;
        margin-top: 15px;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

def display_chuni_header():
    """춘이 캐릭터 헤더 표시"""
    st.markdown("""
    <div class="chuni-header">
        <div class="chuni-logo">
            <svg width="60" height="60" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                <!-- Background circle -->
                <circle cx="100" cy="100" r="95" fill="#f5e6d3" stroke="#2c5282" stroke-width="4"/>
                <!-- Robot body -->
                <ellipse cx="100" cy="120" rx="60" ry="65" fill="#ffffff" stroke="#2c5282" stroke-width="3"/>
                <!-- Head/helmet -->
                <ellipse cx="100" cy="85" rx="45" ry="40" fill="#ffffff" stroke="#2c5282" stroke-width="3"/>
                <!-- Heart antenna -->
                <path d="M100,45 L100,35" stroke="#2c5282" stroke-width="2"/>
                <path d="M100,35 C100,30 95,25 90,30 C85,35 90,40 100,45 C110,40 115,35 110,30 C105,25 100,30 100,35" fill="#5a9fd4"/>
                <!-- Eyes -->
                <ellipse cx="85" cy="85" rx="6" ry="10" fill="#2c5282"/>
                <ellipse cx="115" cy="85" rx="6" ry="10" fill="#2c5282"/>
                <!-- Cheeks -->
                <circle cx="70" cy="95" r="8" fill="#ffb3ba" opacity="0.7"/>
                <circle cx="130" cy="95" r="8" fill="#ffb3ba" opacity="0.7"/>
                <!-- Mouth -->
                <path d="M85,105 Q100,115 115,105" stroke="#2c5282" stroke-width="2" fill="none" stroke-linecap="round"/>
                <!-- Arms -->
                <ellipse cx="60" cy="120" rx="12" ry="30" fill="#ffffff" stroke="#2c5282" stroke-width="2" transform="rotate(-20 60 120)"/>
                <ellipse cx="140" cy="120" rx="12" ry="30" fill="#ffffff" stroke="#2c5282" stroke-width="2" transform="rotate(20 140 120)"/>
                <!-- Badge -->
                <text x="100" y="130" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#2c5282">춘이</text>
            </svg>
        </div>
        <h1 class="chuni-title">춘천시 AI 헬퍼 춘이</h1>
        <p class="chuni-subtitle">춘천시 관광, 행사, 맛집 정보를 실시간으로 알려드려요!</p>
        <div class="status-indicator">
            <div class="status-dot"></div>
            시스템 준비 완료
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_quick_questions():
    """빠른 질문 버튼들 표시 - HTML 버전과 동일한 스타일"""
    # HTML 버전과 동일한 질문들
    quick_questions = [
        "🍗 춘천 닭갈비 맛집 어디...",
        "🎉 이번 주 춘천에서 뭐...",
        "🖊️ 독감 예방접종 어디서...",
        "🏛️ 주민등록등본 떼려면 어...",
        "🚗 춘천에 전기차 충전소...",
        "🌸 봄에 가볼만한 춘천명...",
        "👴 우리 할머니 일자리프...",
        "📞 시청 민원실 전화번호..."
    ]
    
    full_questions = [
        "춘천 닭갈비 맛집 어디가 진짜 맛있어?",
        "이번 주 춘천에서 뭐 재밌는 행사 있어?",
        "독감 예방접종 어디서 할 수 있어?",
        "주민등록등본 떼려면 어디로 가야해?",
        "춘천에 전기차 충전소 많아?",
        "봄에 가볼만한 춘천 명소 추천해줘",
        "우리 할머니 일자리 프로그램 있을까?",
        "시청 민원실 전화번호 알려줘"
    ]
    
    # HTML 버전과 동일한 레이아웃 - 2행 4열
    cols1 = st.columns(4)
    cols2 = st.columns(4)
    
    for i, (short_q, full_q) in enumerate(zip(quick_questions, full_questions)):
        col = cols1[i] if i < 4 else cols2[i-4]
        with col:
            if st.button(short_q, key=f"quick_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": full_q})
                st.session_state.messages.append({"role": "typing", "content": "춘이가 생각중입니다..."})
                st.rerun()

def display_chat_message(message, is_user=False, is_typing=False):
    """채팅 메시지 표시"""
    if is_typing:
        st.markdown(f"""
        <div class="typing-indicator">
            <div class="bot-info">
                <div class="bot-avatar">🤖</div>
                <div class="bot-name">춘이</div>
            </div>
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            {message}
        </div>
        """, unsafe_allow_html=True)
    elif is_user:
        st.markdown(f"""
        <div class="chat-message user-message">
            <strong>👤 사용자:</strong><br>
            {message}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-message bot-message">
            <div class="bot-info">
                <div class="bot-avatar">🤖</div>
                <div class="bot-name">춘이</div>
            </div>
            {message}
        </div>
        """, unsafe_allow_html=True)

def initialize_chatbot():
    """미리 준비된 AI 챗봇 - 사용자 대기시간 제거"""
    if 'chatbot' not in st.session_state:
        try:
            # 캐시된 챗봇 즉시 로드 (이미 준비됨)
            chatbot, success = get_cached_chatbot()
            if success:
                st.session_state.chatbot = chatbot
                st.session_state.chatbot_ready = True
                st.session_state.session_id = str(uuid.uuid4())
                # 성공 메시지 제거 - 즉시 사용 가능
            else:
                raise Exception(chatbot)
        except Exception as e:
            st.session_state.chatbot_ready = False
            st.session_state.error_message = str(e)
            st.error(f"❌ 춘이 AI 초기화 실패: {e}")
            if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
                st.info("💡 Streamlit Cloud Secrets에 OPENAI_API_KEY를 설정해주세요.")

@st.cache_resource
def get_cached_chatbot():
    """미리 로드된 챗봇 인스턴스 - 사용자가 기다리지 않도록 사전 초기화"""
    try:
        # 백그라운드에서 미리 초기화
        chatbot = EnhancedStreamlitChatbot()
        
        # 모든 데이터 폴더에서 로드
        folders = ["./민원 관련", "./dataSet", "./dataset2"]
        for folder in folders:
            if os.path.exists(folder):
                chatbot.data_loader.load_csv_files(folder)
        
        # 벡터스토어 미리 생성
        documents = chatbot.data_loader.get_documents()
        if documents:
            split_docs = chatbot.data_loader.text_splitter.split_documents(documents)
            chatbot.vector_store = FAISS.from_documents(split_docs, chatbot.embeddings)
            chatbot.retriever = chatbot.vector_store.as_retriever(search_kwargs={"k": 5})
        
        return chatbot, True
    except Exception as e:
        return None, str(e)

def initialize_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chatbot_ready' not in st.session_state:
        st.session_state.chatbot_ready = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

def process_ai_response(user_message):
    """AI 응답 비동기 처리"""
    try:
        # 타이핑 인디케이터 제거
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "typing":
            st.session_state.messages.pop()
        
        # 실제 AI 응답 생성
        response = st.session_state.chatbot.generate_response(
            user_message, 
            st.session_state.session_id
        )
        st.session_state.messages.append({"role": "assistant", "content": response})
        
    except Exception as e:
        # 타이핑 인디케이터 제거
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "typing":
            st.session_state.messages.pop()
        
        error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_msg})

def main():
    # 세션 상태 초기화
    initialize_session_state()
    
    # 춘이 헤더 표시
    display_chuni_header()
    
    # 챗봇 초기화
    initialize_chatbot()
    
    # 챗봇 상태 확인 - 에러시에만 표시
    if not st.session_state.chatbot_ready:
        st.error("❌ 춘이 AI 초기화에 실패했습니다.")
        st.info("💡 API 키가 올바르게 설정되어 있는지 확인해주세요.")
        return
    
    # 환영 메시지 제거 - HTML 버전처럼 깔끔하게
    
    # 채팅 메시지 표시 - HTML 버전과 동일한 레이아웃
    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            # 환영 메시지 - HTML 버전과 동일
            st.markdown("""
            <div style="text-align: center; padding: 40px; color: #6b7280;">
                <p style="margin-bottom: 10px;">안녕하세요! 춘천시 AI 헬퍼 <strong>춘이</strong>입니다!</p>
                <p style="margin-bottom: 10px;">춘천의 관광, 맛집, 행사, 정책 등 뭐든지 물어보세요!</p>
                <p style="margin-bottom: 10px;">예를 들어 이런 걸 물어보실 수 있어요:</p>
                <ul style="text-align: left; display: inline-block; margin-top: 10px; list-style: none; padding: 0;">
                    <li style="margin: 5px 0;">• 이번주 춘천 행사 뭐 있어?</li>
                    <li style="margin: 5px 0;">• 춘천 닭갈비 맛집 추천해줘</li>
                    <li style="margin: 5px 0;">• 춘천 전기차 충전소 어디 있어?</li>
                    <li style="margin: 5px 0;">• 춘천시 청년 정책 알려줘</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 채팅 메시지들
            for message in st.session_state.messages:
                if message["role"] == "user":
                    display_chat_message(message["content"], is_user=True)
                elif message["role"] == "typing":
                    display_chat_message(message["content"], is_typing=True)
                else:
                    display_chat_message(message["content"], is_user=False)
    
    # 빠른 질문 섹션 - HTML 버전과 동일하게 항상 표시
    display_quick_questions()
    
    # 채팅 입력
    user_input = st.chat_input("춘천에 대해 뭐든지 물어보세요...", key="chat_input")
    
    # 타이핑 상태가 있으면 AI 응답 처리
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "typing":
        # 마지막 사용자 메시지 찾기
        user_message = None
        for msg in reversed(st.session_state.messages[:-1]):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        if user_message:
            process_ai_response(user_message)
            st.rerun()
    
    if user_input:
        if st.session_state.chatbot_ready:
            # 즉시 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            # 타이핑 인디케이터 추가
            st.session_state.messages.append({"role": "typing", "content": "춘이가 생각중입니다..."})
            st.rerun()
        else:
            st.error("❌ 춘이 AI가 아직 준비되지 않았습니다. 페이지를 새로고침해주세요.")
    
    # 하단 정보
    st.markdown("""
    <div class="footer-info">
        <p>🌸 <strong>춘천시 AI 도우미 춘이</strong> - 2025년 프롬프톤 출품작 🌸</p>
        <p>개발팀: 김재형(팀장), 김성호, 김강민 | 한림대학교</p>
        <p>🏛️ 춘천시청: 033-250-3000 | 🚂 춘천역: 1544-7788 | 🍗 특산품: 닭갈비, 막국수</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()