"""
춘천시 AI 챗봇 Streamlit 웹 인터페이스 - Flask 디자인 매칭 버전
Chuncheon City AI Chatbot Web Interface - Matching Flask Design
"""

import streamlit as st
import os
from data_collector import ChuncheonDataCollector
import json
from datetime import datetime
import sys
import uuid

# AI 라이브러리 import
try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_core.prompts import ChatPromptTemplate
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
    import pandas as pd
    import glob
except ImportError as e:
    st.error(f"❌ 필요한 라이브러리를 찾을 수 없습니다: {e}")
    st.info("💡 requirements.txt의 모든 패키지가 설치되어 있는지 확인해주세요.")
    st.stop()

# API 키 설정 (Streamlit Secrets 우선, 없으면 환경변수)
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

class StreamlitChuncheonChatbot:
    """Streamlit용 간소화된 춘천시 AI 챗봇"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            api_key=self.api_key
        )
        
        # 춘천시 데이터 로드
        self.chuncheon_data = self._load_chuncheon_data()
        
        # 프롬프트 템플릿
        self.prompt_template = """당신은 '춘이'라는 이름의 강원특별자치도 춘천시 AI 도우미입니다.

# 필수 지침:
1. 항상 친근하고 도움이 되는 태도로 한국어로 응답하세요
2. 존댓말을 사용하세요
3. 춘천시와 관련된 정보를 우선적으로 제공하세요
4. 정확한 정보만 제공하고, 불확실한 경우 명시하세요

# 춘천시 기본 정보:
{chuncheon_info}

# 사용자 질문: {question}

위 정보를 바탕으로 정확하고 도움이 되는 답변을 제공하세요.
응답은 반드시 한국어로 작성하고, 존댓말을 사용해주세요.

답변:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
    
    def _load_chuncheon_data(self):
        """춘천시 기본 데이터 로드"""
        return """
춘천시 주요 정보:

🏛️ 춘천시청
- 주소: 강원특별자치도 춘천시 중앙로 1
- 전화: 033-250-3000
- 업무: 민원업무, 행정서비스, 시정안내

🍗 춘천 닭갈비 맛집
- 춘천 닭갈비 1번지: 춘천시 중앙로 37 (033-252-3377)
- 춘천 닭갈비 2번지: 춘천시 중앙로 45 (033-252-3378)
- 영업시간: 10:00~22:00

🍜 막국수 맛집
- 막국수체험박물관: 춘천시 신북읍 신샘밭로 264 (033-244-8869)
- 체험 및 시식 가능

🏞️ 주요 관광지
- 남이섬: 춘천시 남산면 남이섬길 1 (031-580-8114)
- 춘천호: 춘천시 신북읍 (033-250-3089)
- 춘천시민회관: 춘천시 금강로 11 (033-259-5800)

🚗 교통 정보
- 춘천역: 춘천시 근화동 472-1 (1544-7788)
- 춘천터미널: 춘천시 온의동 664-2 (033-252-6441)
- 전기차 충전소: 105개소 운영 중

🏥 의료 및 복지
- 독감 예방접종: 춘천시 보건소 및 위탁의료기관
- 노인일자리 프로그램: 춘천시 사회복지과 (033-250-3000)
- 장애인 지원 서비스: 춘천시 장애인복지과

📞 주요 연락처
- 춘천시청 대표: 033-250-3000
- 민원실: 033-250-3000
- 관광안내: 033-250-3089
        """
    
    def generate_response(self, question: str, session_id: str = "default"):
        """AI 응답 생성"""
        try:
            # 프롬프트에 데이터 포함하여 응답 생성
            response = self.llm.invoke([
                {"role": "system", "content": self.prompt_template.format(
                    chuncheon_info=self.chuncheon_data,
                    question=question
                )}
            ])
            
            return response.content
            
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
    /* 전체 페이지 스타일 */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 헤더 스타일 - Flask 버전과 동일 */
    .chuni-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px 30px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .chuni-logo {
        width: 80px;
        height: 80px;
        margin: 0 auto 15px;
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .chuni-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 15px 0 10px 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .chuni-subtitle {
        font-size: 1.1rem;
        opacity: 0.9;
        margin-bottom: 20px;
    }
    
    .status-indicator {
        display: inline-flex;
        align-items: center;
        background: rgba(255,255,255,0.2);
        padding: 8px 16px;
        border-radius: 25px;
        font-size: 0.9rem;
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
    
    /* 채팅 메시지 스타일 */
    .chat-message {
        margin: 15px 0;
        padding: 15px 20px;
        border-radius: 18px;
        max-width: 85%;
        word-wrap: break-word;
        line-height: 1.6;
        animation: fadeIn 0.3s ease-in;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        margin-left: auto;
        text-align: right;
    }
    
    .bot-message {
        background: #f8f9fa;
        color: #333;
        border: 1px solid #e9ecef;
        margin-right: auto;
    }
    
    .bot-info {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 10px;
    }
    
    .bot-avatar {
        width: 35px;
        height: 35px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea, #764ba2);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 0.8rem;
    }
    
    .bot-name {
        font-weight: 600;
        color: #667eea;
        font-size: 0.9rem;
    }
    
    /* 빠른 질문 버튼 스타일 */
    .quick-question-btn {
        display: inline-block;
        margin: 5px;
        padding: 10px 20px;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border: 2px solid #667eea;
        border-radius: 25px;
        color: #667eea;
        text-decoration: none;
        font-weight: 500;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    
    .quick-question-btn:hover {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
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
    
    /* 사이드바 숨기기 */
    .css-1d391kg {display: none;}
    
    /* 메인 컨테이너 스타일 */
    .block-container {
        max-width: 900px;
        padding: 20px;
    }
    
    /* 버튼 스타일 통일 */
    .stButton > button {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
</style>
""", unsafe_allow_html=True)

def display_chuni_header():
    """춘이 캐릭터 헤더 표시"""
    st.markdown("""
    <div class="chuni-header">
        <div class="chuni-logo">
            <svg width="80" height="80" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
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
    """빠른 질문 버튼들 표시"""
    st.markdown("### 🚀 빠른 질문")
    
    # Flask 버전과 동일한 질문들
    quick_questions = [
        {"icon": "🍗", "text": "춘천 닭갈비 맛집 추천해줘", "category": "맛집"},
        {"icon": "🎉", "text": "이번 주 춘천에서 뭐 재밌는 행사 있어?", "category": "행사"},
        {"icon": "💉", "text": "독감 예방접종 어디서 할 수 있어?", "category": "의료"},
        {"icon": "🏛️", "text": "주민등록등본 떼려면 어디로 가야해?", "category": "행정"},
        {"icon": "🚗", "text": "춘천에 전기차 충전소 많아?", "category": "교통"},
        {"icon": "🌸", "text": "봄에 가볼만한 춘천 명소 추천해줘", "category": "관광"},
        {"icon": "👴", "text": "우리 할머니 일자리 프로그램 있을까?", "category": "복지"},
        {"icon": "📞", "text": "시청 민원실 전화번호 알려줘", "category": "연락처"}
    ]
    
    # 2열로 배치
    cols = st.columns(2)
    for i, q in enumerate(quick_questions):
        col = cols[i % 2]
        with col:
            if st.button(f"{q['icon']} {q['text']}", key=f"quick_{i}", use_container_width=True):
                if st.session_state.chatbot_ready:
                    # 질문을 채팅에 추가
                    st.session_state.messages.append({"role": "user", "content": q['text']})
                    # 실제 AI 응답 생성
                    with st.spinner("춘이가 답변을 준비하고 있습니다..."):
                        try:
                            bot_response = st.session_state.chatbot.generate_response(
                                q['text'], 
                                st.session_state.session_id
                            )
                            st.session_state.messages.append({"role": "assistant", "content": bot_response})
                        except Exception as e:
                            error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                            st.session_state.messages.append({"role": "assistant", "content": error_msg})
                else:
                    st.error("❌ 춘이 AI가 아직 준비되지 않았습니다.")
                st.rerun()

def display_chat_message(message, is_user=False):
    """채팅 메시지 표시"""
    if is_user:
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
    """실제 AI 챗봇 초기화"""
    if 'chatbot' not in st.session_state:
        try:
            with st.spinner("춘이 AI를 깨우는 중입니다... 🤖"):
                st.session_state.chatbot = StreamlitChuncheonChatbot()
                st.session_state.chatbot_ready = True
                st.session_state.session_id = str(uuid.uuid4())
                st.success("✅ 춘이 AI가 준비되었습니다!")
        except Exception as e:
            st.session_state.chatbot_ready = False
            st.session_state.error_message = str(e)
            st.error(f"❌ 춘이 AI 초기화 실패: {e}")
            if "OPENAI_API_KEY" not in os.environ or not os.environ["OPENAI_API_KEY"]:
                st.info("💡 Streamlit Cloud Secrets에 OPENAI_API_KEY를 설정해주세요.")

def initialize_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chatbot_ready' not in st.session_state:
        st.session_state.chatbot_ready = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

def main():
    # 세션 상태 초기화
    initialize_session_state()
    
    # 춘이 헤더 표시
    display_chuni_header()
    
    # 챗봇 초기화
    initialize_chatbot()
    
    # 챗봇 상태 확인 및 환영 메시지
    if not st.session_state.chatbot_ready:
        st.warning("⚠️ 춘이 AI를 준비하고 있습니다. 잠시만 기다려주세요...")
        st.info("💡 API 키가 올바르게 설정되어 있는지 확인해주세요.")
        return
    
    # 환영 메시지 (메시지가 없을 때만)
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align: center; padding: 40px; background: #f8f9fa; border-radius: 15px; margin: 20px 0;">
            <h3 style="color: #667eea; margin-bottom: 15px;">안녕하세요! 춘천시 AI 헬퍼 <strong>춘이</strong>입니다! 🌸</h3>
            <p style="color: #6b7280; margin-bottom: 10px;">춘천의 관광, 맛집, 행사, 정책 등 뭐든지 물어보세요!</p>
            <p style="color: #6b7280;">예를 들어 이런 걸 물어보실 수 있어요:</p>
            <div style="text-align: left; display: inline-block; margin-top: 15px; color: #495057;">
                • 이번주 춘천 행사 뭐 있어?<br>
                • 춘천 닭갈비 맛집 추천해줘<br>
                • 춘천 전기차 충전소 어디 있어?<br>
                • 춘천시 청년 정책 알려줘
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 채팅 메시지 표시
    for message in st.session_state.messages:
        if message["role"] == "user":
            display_chat_message(message["content"], is_user=True)
        else:
            display_chat_message(message["content"], is_user=False)
    
    # 빠른 질문 섹션
    st.markdown("---")
    display_quick_questions()
    
    # 채팅 입력
    st.markdown("---")
    user_input = st.chat_input("춘천에 대해 뭐든지 물어보세요...", key="chat_input")
    
    if user_input:
        if st.session_state.chatbot_ready:
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 실제 AI 응답 생성
            with st.spinner("춘이가 생각중입니다..."):
                try:
                    response = st.session_state.chatbot.generate_response(
                        user_input, 
                        st.session_state.session_id
                    )
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        else:
            st.error("❌ 춘이 AI가 아직 준비되지 않았습니다. 페이지를 새로고침해주세요.")
        
        st.rerun()
    
    # 하단 정보
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🏛️ 춘천시청**  
        📞 033-250-3000  
        📍 중앙로 1
        """)
    
    with col2:
        st.markdown("""
        **🚂 춘천역**  
        📞 1544-7788  
        📍 근화동 472-1
        """)
    
    with col3:
        st.markdown("""
        **🍽️ 특산품**  
        🍗 춘천닭갈비  
        🍜 막국수
        """)
    
    # 하단 푸터
    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #6b7280; font-size: 0.9rem; margin-top: 30px;">
        <p>🌸 <strong>춘천시 AI 도우미 춘이</strong> - 2025년 프롬프톤 출품작 🌸</p>
        <p>개발팀: 김재형(팀장), 김성호, 김강민 | 한림대학교</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()