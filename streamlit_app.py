"""
춘천시 AI 챗봇 Streamlit 앱 - 완전 새로운 디자인
"""

import streamlit as st
import os
from datetime import datetime
import uuid
from typing import List, Dict, Any

# AI 라이브러리 import
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_community.retrievers import TavilySearchAPIRetriever
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
        text-align: center;
        color: #6b7280;
        padding: 1rem;
        border-top: 1px solid #e5e7eb;
        margin-top: 2rem;
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
        """모든 CSV 파일에서 데이터 로드"""
        documents = []
        
        for folder in self.data_folders:
            folder_path = os.path.join(os.getcwd(), folder)
            if not os.path.exists(folder_path):
                continue
                
            csv_files = glob.glob(os.path.join(folder_path, "*.csv")) + glob.glob(os.path.join(folder_path, "*.CSV"))
            
            for file_path in csv_files:
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='cp949')
                    except:
                        continue
                
                filename = os.path.basename(file_path)
                
                for idx, row in df.iterrows():
                    content = f"파일: {filename}\n"
                    for col in df.columns:
                        if pd.notna(row[col]):
                            content += f"{col}: {row[col]}\n"
                    
                    documents.append(Document(
                        page_content=content,
                        metadata={"source": filename, "row_id": idx}
                    ))
        
        return documents

class EnhancedChuncheonChatbot:
    """RAG 기반 춘천시 챗봇"""
    
    def __init__(self):
        # API 키 설정
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        
        # 데이터 로더 초기화
        self.data_loader = ChuncheonDataLoader()
        
        # 임베딩 및 벡터스토어 초기화
        self.embeddings = OpenAIEmbeddings()
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
            except Exception as e:
                st.warning(f"Tavily 초기화 실패: {e}")
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        # 벡터스토어 생성
        self._create_vector_store()
        
        # 프롬프트 템플릿
        self.prompt_template = """당신은 '춘이'라는 이름의 강원특별자치도 춘천시 AI 도우미입니다.

# 필수 지침:
1. 항상 친근하고 도움이 되는 태도로 한국어로 응답하세요
2. **절대 추측하거나 가짜 정보를 만들지 마세요**
3. **주소, 전화번호, 영업시간 등 구체적 정보는 반드시 제공된 데이터에서만 사용하세요**
4. 정보가 없으면 "정확한 정보를 찾을 수 없습니다"라고 답하세요
5. 존댓말을 사용하세요
6. 춘천시와 관련된 정보를 우선적으로 제공하세요

# 현재 시각: {current_time}

# 관련 데이터:
{context}

# 웹 검색 결과:
{web_results}

# 사용자 질문: {question}

답변:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def _create_vector_store(self):
        """벡터스토어 생성"""
        try:
            documents = self.data_loader.load_csv_data()
            
            if documents:
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=200
                )
                splits = text_splitter.split_documents(documents)
                
                self.vector_store = Chroma.from_documents(
                    documents=splits,
                    embedding=self.embeddings
                )
                self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
                
        except Exception as e:
            st.warning(f"벡터스토어 생성 실패: {e}")
    
    def generate_response(self, message: str) -> str:
        """사용자 메시지에 대한 응답 생성"""
        try:
            current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
            
            # RAG 검색
            context = ""
            if self.retriever:
                try:
                    docs = self.retriever.get_relevant_documents(message)
                    context = "\n\n".join([doc.page_content for doc in docs[:3]])
                except:
                    context = "관련 데이터를 찾을 수 없습니다."
            
            # 웹 검색
            web_results = ""
            if self.tavily_retriever:
                try:
                    web_docs = self.tavily_retriever.get_relevant_documents(f"춘천시 {message}")
                    web_results = "\n\n".join([doc.page_content for doc in web_docs[:2]])
                except:
                    web_results = "웹 검색 결과가 없습니다."
            
            response = self.chain.invoke({
                "question": message,
                "current_time": current_time,
                "context": context,
                "web_results": web_results
            })
            
            if isinstance(response, dict):
                return response.get('text', str(response))
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            return f"죄송합니다. 답변 생성 중 문제가 발생했습니다: {str(e)}"

@st.cache_resource
def initialize_chatbot():
    """RAG 챗봇 초기화 - 캐싱으로 최적화"""
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
        
        # 채팅 메시지 표시
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f"""
                <div class="chat-message user-message">
                    <strong>👤 사용자:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-message bot-message">
                    <strong>🤖 춘이:</strong><br>
                    {message["content"]}
                </div>
                """, unsafe_allow_html=True)
        
        # 빠른 질문 버튼들
        st.markdown("### 🚀 빠른 질문")
        
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
                    st.session_state.messages.append({"role": "user", "content": question})
                    
                    # AI 응답 생성
                    with st.spinner("춘이가 생각중..."):
                        response = chatbot.generate_response(question)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    st.rerun()
        
        # 두 번째 행
        for i, question in enumerate(quick_questions[4:]):
            with row2_cols[i]:
                if st.button(question, key=f"quick_{i+4}"):
                    st.session_state.messages.append({"role": "user", "content": question})
                    
                    # AI 응답 생성
                    with st.spinner("춘이가 생각중..."):
                        response = chatbot.generate_response(question)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    st.rerun()
        
        # 채팅 입력
        st.markdown("### 💬 직접 질문하기")
        user_input = st.chat_input("춘천에 대해 뭐든지 물어보세요...")
        
        if user_input:
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            with st.chat_message("assistant"):
                with st.spinner("춘이가 답변을 생성하고 있습니다..."):
                    response = chatbot.generate_response(user_input)
                st.write(response)
            
            st.rerun()
    
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
