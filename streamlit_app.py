"""
춘천시 AI 챗봇 Streamlit 앱 - 완전 새로운 디자인
"""

import streamlit as st
import os
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import glob
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import requests
import json
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# Tavily 검색 추가
try:
    from langchain_community.tools.tavily_search import TavilySearchResults
except ImportError:
    TavilySearchResults = None

# AI 라이브러리 import
try:
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnablePassthrough, RunnableLambda
    from langchain.chains import LLMChain
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    import pandas as pd
    import numpy as np
    import glob
    import requests
    import json
except ImportError as e:
    st.error(f"❌ 필요한 라이브러리를 찾을 수 없습니다: {e}")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="춘천시 AI 도우미 - 춘이",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API 키 설정
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

# 공공데이터 API 키
PUBLIC_API_KEY = "o2Ly83v52XUaFEc1EFz+VgHoNb2ErLSGPrkhn4wJ3J+478HUZCgn6DGzq7IHLKGU6C75oIpQYQvItH9nTRzamQ=="

# 스트림릿에 최적화된 CSS 스타일
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        margin-left: 25%;
        text-align: right;
    }
    
    .bot-message {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        margin-right: 25%;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 25px;
        border: 2px solid #667eea;
        color: #667eea;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .footer-info {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        width: 100%;
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(15px);
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        padding: 15px 20px;
        text-align: center;
        color: #6b7280;
        font-size: 0.9rem;
        z-index: 9999;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .main-content {
        padding-bottom: 120px;
    }
    
    .welcome-box {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

class ChuncheonDataLoader:
    """춘천시 데이터 로더 클래스"""
    
    def __init__(self):
        self.data_folders = [
            "dataSet",
            "dataset2", 
            "민원 관련"
        ]
        self.all_data = []
    
    def load_csv_data(self) -> List[Document]:
        """모든 CSV 파일에서 데이터 로드 - 토큰 제한 고려"""
        documents = []
        max_documents = 100  # 문서 수 제한
        
        for folder in self.data_folders:
            folder_path = os.path.join(os.getcwd(), folder)
            if not os.path.exists(folder_path):
                continue
                
            csv_files = glob.glob(os.path.join(folder_path, "*.csv")) + glob.glob(os.path.join(folder_path, "*.CSV"))
            
            for file_path in csv_files[:2]:  # 파일 수 제한
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='cp949')
                    except:
                        continue
                
                filename = os.path.basename(file_path)
                
                # 행 수 제한
                for idx, row in df.head(50).iterrows():
                    if len(documents) >= max_documents:
                        break
                        
                    content = f"파일: {filename}\n"
                    for col in df.columns:
                        if pd.notna(row[col]):
                            # 긴 텍스트 자르기
                            value = str(row[col])[:200]
                            content += f"{col}: {value}\n"
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={"source": filename, "row_id": idx}
                    ))
                
                if len(documents) >= max_documents:
                    break
        
        return documents

class ChuncheonPublicAPI:
    """춘천시 공공데이터 API 클래스"""
    
    def __init__(self, api_key: str = "4e51a9f2-b6b2-4b9c-9b2b-4b9c9b2b4b9c"):
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
                "numOfRows": "10",
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
                    items = data['response']['body'].get('items', [])
                    return items if isinstance(items, list) else [items] if items else []
            return []
        except Exception as e:
            return []
    
    def get_tourism_info(self, keyword: str = None) -> List[Dict]:
        """관광 정보 조회"""
        try:
            params = {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": "10",
                "_type": "json"
            }
            
            response = requests.get(
                f"{self.base_urls['tourism']}/getTourList",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'body' in data['response']:
                    items = data['response']['body'].get('items', [])
                    return items if isinstance(items, list) else [items] if items else []
            return []
        except Exception as e:
            return []

class EnhancedChuncheonChatbot:
    """RAG 기반 춘천시 챗봇"""
    
    def __init__(self):
        # API 키 설정
        self.api_key = None
        self.perplexity_api_key = None
        
        # OpenAI API 키 로드 (우선순위: Streamlit secrets > 환경변수)
        try:
            self.api_key = st.secrets["OPENAI_API_KEY"]
        except:
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            st.error("Streamlit Cloud Secrets에 OPENAI_API_KEY를 설정해주세요.")
            return
        
        # Perplexity API 키 로드
        try:
            self.perplexity_api_key = st.secrets["PERPLEXITY_API_KEY"]
        except:
            self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        
        # Tavily API 키 로드 (백업 검색용)
        try:
            self.tavily_api_key = st.secrets["TAVILY_API_KEY"]
        except:
            self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        if not self.perplexity_api_key and not self.tavily_api_key:
            st.warning("⚠️ 웹 검색 API 키가 설정되지 않았습니다. 검색 기능이 제한됩니다.")
        
        # 임베딩 및 LLM 초기화
        try:
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.api_key,
                model="text-embedding-3-small"
            )
            self.vector_store = self._create_vector_store()
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                openai_api_key=self.api_key
            )
        except Exception as e:
            st.error(f"챗봇 초기화 실패: {str(e)}")
            return
        
        # 프롬프트 템플릿 설정
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """
당신은 춘천시 전문 AI 도우미 '춘이'입니다.

**중요 지침:**
1. 춘천, 춘천시와 관련된 모든 질문에 적극적으로 답변하세요.
2. 카페, 맛집, 관광지, 정책, 교통, 충전소 등 춘천 지역의 모든 정보를 도움을 드립니다.
3. 제공된 데이터와 웹 검색 결과를 활용하여 최대한 유용한 정보를 제공하세요.
4. 정확한 정보가 없더라도 일반적인 춘천 관련 조언이나 추천을 해주세요.
5. 춘천과 전혀 관계없는 질문(예: 서울 맛집, 부산 여행)에만 "춘천시 관련 질문만 답변드릴 수 있습니다"라고 응답하세요.

**춘천시 기본 정보:**
- 대표 음식: 닭갈비, 막국수, 소양강 처녀막국수
- 주요 관광지: 남이섬, 소양강댐, 춘천호, 김유정문학촌, 애니메이션박물관
- 카페 거리: 춘천 명동, 온의동 카페거리
- 시청 전화: 033-250-3000
- 춘천역: 1544-7788
- 강원대학교 춘천캠퍼스, 한림대학교: 춘천시 한림대학길 1

**제공된 데이터:**
{context}

**웹 검색 결과:**
{web_search}

위 정보를 바탕으로 춘천시에 대한 질문에 친근하고 도움이 되는 답변을 해주세요.
            """),
            ("human", "{question}")
        ])
        
        # LLM 체인 생성
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
    def _create_vector_store(self):
        """벡터스토어 생성"""
        try:
            documents = ChuncheonDataLoader().load_csv_data()
            
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=500,
                    chunk_overlap=50
                )
                splits = text_splitter.split_documents(documents)
                
                # 배치 처리로 토큰 제한 방지
                batch_size = 20
                if len(splits) > batch_size:
                    splits = splits[:batch_size]
                
                vector_store = FAISS.from_documents(
                    documents=splits,
                    embedding=self.embeddings
                )
                return vector_store.as_retriever(search_kwargs={"k": 5})
                
        except Exception as e:
            st.warning(f"벡터스토어 생성 실패: {e}")
            return None
    
    def _get_perplexity_search_results(self, query: str) -> str:
        """Perplexity API를 사용한 웹 검색"""
        if not self.perplexity_api_key:
            return "로컬 데이터만 사용합니다."
        
        try:
            # 춘천 관련 검색어로 강화 - 더 구체적으로
            if "카페" in query:
                enhanced_query = f"춘천시 추천 카페 맛집 명동 온의동 카페거리 2024 2025"
            elif "청년" in query and "정책" in query:
                enhanced_query = f"춘천시 청년정책 청년일자리 청년창업 지원사업 2024 2025"
            elif "전기차" in query or "충전소" in query:
                enhanced_query = f"춘천시 전기차 충전소 위치 현황 2024 2025"
            else:
                enhanced_query = f"춘천시 {query} 2024 2025 최신 정보"
            
            url = "https://api.perplexity.ai/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "춘천시에 대한 정확하고 구체적인 최신 정보를 제공해주세요. 가능한 한 상세한 정보(주소, 전화번호, 운영시간 등)를 포함하여 한국어로 답변하세요."
                    },
                    {
                        "role": "user", 
                        "content": enhanced_query
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": ["naver.com", "daum.net", "chuncheon.go.kr", "gangwon.go.kr"],
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "month",
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return "웹 검색을 사용할 수 없습니다. 로컬 데이터만 사용합니다."
                
        except Exception as e:
            return "웹 검색을 사용할 수 없습니다. 로컬 데이터만 사용합니다."
    
    def _get_tavily_search_results(self, query: str) -> str:
        """Tavily API를 사용한 백업 웹 검색"""
        if not self.tavily_api_key or not TavilySearchResults:
            return ""
        
        try:
            tavily_search = TavilySearchResults(
                max_results=3,
                search_depth="advanced",
                include_answer=True,
                include_raw_content=False,
                include_images=False,
                api_key=self.tavily_api_key
            )
            
            # 춘천 관련 검색어로 강화
            enhanced_query = f"춘천시 {query} 2024 2025"
            results = tavily_search.run(enhanced_query)
            
            if results:
                formatted_results = []
                for result in results[:3]:
                    if isinstance(result, dict):
                        title = result.get('title', '')
                        content = result.get('content', '')
                        if title and content:
                            formatted_results.append(f"**{title}**\n{content}")
                
                return "\n\n".join(formatted_results) if formatted_results else ""
            
            return ""
            
        except Exception as e:
            return ""
    
    def _get_public_api_results(self, query: str) -> str:
        """춘천시 공공데이터 API 결과 가져오기"""
        try:
            results = []
            
            # 행사 관련 키워드 검색
            if any(keyword in query for keyword in ["행사", "공연", "축제", "이벤트"]):
                events = self.public_api.get_events()
                if events:
                    results.append("최신 행사 정보:")
                    for event in events[:3]:
                        if isinstance(event, dict):
                            name = event.get('eventNm', '비어있음')
                            date = event.get('eventDate', '비어있음')
                            place = event.get('eventPlace', '비어있음')
                            results.append(f"- {name} ({date}, {place})")
            
            # 관광 관련 키워드 검색
            if any(keyword in query for keyword in ["관광", "여행", "명소", "추천"]):
                tourism = self.public_api.get_tourism_info()
                if tourism:
                    results.append("관광지 정보:")
                    for place in tourism[:3]:
                        if isinstance(place, dict):
                            name = place.get('tourNm', '비어있음')
                            addr = place.get('tourAddr', '비어있음')
                            results.append(f"- {name} ({addr})")
            
            return "\n".join(results) if results else "공공데이터에서 관련 정보를 찾을 수 없습니다."
            
        except Exception as e:
            return "공공데이터 조회 중 오류가 발생했습니다."

    def generate_response(self, question: str) -> str:
        """질문에 대한 응답 생성"""
        try:
            # 벡터 스토어에서 관련 문서 검색
            if hasattr(self.vector_store, 'similarity_search'):
                relevant_docs = self.vector_store.similarity_search(question, k=5)
            else:
                # VectorStoreRetriever 객체인 경우
                relevant_docs = self.vector_store.get_relevant_documents(question)[:5]
            context = "\n".join([doc.page_content for doc in relevant_docs])
            
            # Perplexity 웹 검색 결과 가져오기
            web_search_results = self._get_perplexity_search_results(question)
            
            # Perplexity 결과가 부족하면 Tavily로 백업 검색
            tavily_results = ""
            if not web_search_results or "로컬 데이터만 사용합니다" in web_search_results:
                tavily_results = self._get_tavily_search_results(question)
            
            # 공공데이터 API 결과 가져오기
            public_data_results = self._get_public_api_results(question)
            
            # 모든 정보 결합
            all_search_results = []
            if web_search_results and "로컬 데이터만 사용합니다" not in web_search_results:
                all_search_results.append(f"Perplexity 검색: {web_search_results}")
            if tavily_results:
                all_search_results.append(f"Tavily 검색: {tavily_results}")
            
            combined_search = "\n\n".join(all_search_results) if all_search_results else "웹 검색 결과 없음"
            combined_info = f"{combined_search}\n\n공공데이터: {public_data_results}"
            
            # LLM 체인 실행
            response = self.chain.run(
                context=context,
                web_search=combined_info,
                question=question
            )
            
            return response
            
        except Exception as e:
            return f"죄송합니다. 오류가 발생했습니다: {str(e)}"

def initialize_chatbot():
    """RAG 챗봇 초기화 - 캐시 제거로 문제 해결"""
    try:
        with st.spinner("🚀 춘천시 RAG 챗봇 초기화 중..."):
            chatbot = EnhancedChuncheonChatbot()
        st.success("✅ 챗봇 초기화 완료!")
        return chatbot
    except Exception as e:
        st.error(f"❌ 챗봇 초기화 실패: {e}")
        st.info("💡 Streamlit Cloud Secrets에 OPENAI_API_KEY를 설정해주세요.")
        return None

def main():
    # 세션 상태 초기화
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chatbot_ready' not in st.session_state:
        st.session_state.chatbot_ready = False
    
    # 메인 컨테이너
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>🌸 춘천시 AI 도우미 춘이 🌸</h1>
        <p>춘천시 관광, 행사, 맛집 정보를 실시간으로 알려드려요!</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 챗봇 초기화
    chatbot = initialize_chatbot()
    if not chatbot:
        st.warning("⚠️ 챗봇이 준비되지 않았습니다. API 키를 확인해주세요.")
        return
    
    # 메인 컨테이너
    col1, col2, col3 = st.columns([1, 4, 1])
    
    with col2:
        # 환영 메시지
        if not st.session_state.messages:
            st.markdown("""
            <div class="welcome-box">
                <h3>👋 안녕하세요!</h3>
                <p>춘천에 대해 궁금한 것이 있으시면 언제든 물어보세요!</p>
                <p>아래 버튼을 클릭하거나 직접 질문을 입력해주세요.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 채팅 기록 표시
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant", avatar="🌸"):
                        st.write(f"**춘이:** {message['content']}")
    
            # 로딩 중인 메시지가 있으면 응답 생성
            if (st.session_state.messages and 
                st.session_state.messages[-1]["role"] == "assistant" and 
                "생각중" in st.session_state.messages[-1]["content"]):
                
                # 마지막 사용자 메시지 찾기
                user_message = None
                for msg in reversed(st.session_state.messages):
                    if msg["role"] == "user":
                        user_message = msg["content"]
                        break
        
                if user_message:
                    try:
                        response = chatbot.generate_response(user_message)
                        st.session_state.messages[-1] = {"role": "assistant", "content": response}
                        st.rerun()
                    except Exception as e:
                        st.session_state.messages[-1] = {"role": "assistant", "content": f"죄송합니다. 오류가 발생했습니다: {str(e)}"}
                        st.rerun()
        
        # 빠른 질문 버튼들 (접을 수 있음)
        with st.expander("🚀 빠른 질문", expanded=True):
            # 2행 4열로 배치
            row1_cols = st.columns(4)
            row2_cols = st.columns(4)
        
            quick_questions = [
                "춘천 닭갈비 맛집 추천해줘",
                "이번 주 춘천 행사 뭐 있어?",
                "춘천 전기차 충전소 어디 있어?",
                "춘천 관광지 추천해줘",
                "춘천시 청년 정책 알려줘",
                "춘천 카페 추천해줘",
                "춘천 숙박시설 알려줘",
                "시청 연락처 알려줘"
            ]
            
            # 첫 번째 행
            for i, question in enumerate(quick_questions[:4]):
                with row1_cols[i]:
                    if st.button(question, key=f"quick_{i}"):
                        # 사용자 질문 추가
                        st.session_state.messages.append({"role": "user", "content": question})
                        
                        # 로딩 메시지 추가
                        st.session_state.messages.append({"role": "assistant", "content": "🌸 춘이가 생각중..."})
                        
                        # 화면 업데이트하여 로딩 메시지 표시
                        st.rerun()
            
            # 두 번째 행
            for i, question in enumerate(quick_questions[4:]):
                with row2_cols[i]:
                    if st.button(question, key=f"quick_{i+4}"):
                        # 사용자 질문 추가
                        st.session_state.messages.append({"role": "user", "content": question})
                        
                        # 로딩 메시지 추가
                        st.session_state.messages.append({"role": "assistant", "content": "🌸 춘이가 생각중..."})
                        
                        # 화면 업데이트하여 로딩 메시지 표시
                        st.rerun()
        
        # 채팅 입력
        st.markdown("### 💬 직접 질문하기")
        user_input = st.chat_input("춘천에 대해 뭐든지 물어보세요...")
        
        if user_input:
            # 사용자 질문 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 로딩 메시지 추가
            st.session_state.messages.append({"role": "assistant", "content": "🌸 춘이가 답변을 생성하고 있습니다..."})
            
            # 화면 업데이트하여 로딩 메시지 표시
            st.rerun()
    
    # 메인 컨테이너 닫기
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 하단 정보 (화면 바닥 고정)
    st.markdown("""
    <div class="footer-info">
        <div>🌸 <strong>춘천시 주요 정보</strong> 🌸</div>
        <div>닭갈비 · 막국수 · 남이섬 · 소양강댐</div>
        <div>📞 춘천시청: 033-250-3000 | 🚂 춘천역: 1544-7788</div>
        <div style="margin-top: 8px; font-size: 0.8rem; opacity: 0.8;">2025 강원 프롬프톤 | 한림대 김재형, 김성호, 김강민</div>
        <div style="font-size: 0.75rem; opacity: 0.6; margin-top: 5px;">API: apis.data.go.kr/4180000/ccevent, cctour</div>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
