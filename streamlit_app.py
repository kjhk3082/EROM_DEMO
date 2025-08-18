"""
춘천시 AI 챗봇 Streamlit 웹 인터페이스
Chuncheon City AI Chatbot Web Interface
"""

import streamlit as st
import os
from chatbot import ChuncheonAIChatbot
from data_collector import ChuncheonDataCollector
import json

# 페이지 설정
st.set_page_config(
    page_title="춘천시 AI 가이드",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E8B57;
        font-size: 2.5em;
        margin-bottom: 0.5em;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.2em;
        margin-bottom: 2em;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
    }
    .bot-message {
        background-color: #F1F8E9;
        border-left: 4px solid #4CAF50;
    }
    .info-box {
        background-color: #FFF3E0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9800;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_chatbot():
    """챗봇 초기화"""
    if 'chatbot' not in st.session_state:
        try:
            st.session_state.chatbot = ChuncheonAIChatbot()
            st.session_state.chatbot_ready = True
        except Exception as e:
            st.session_state.chatbot_ready = False
            st.session_state.error_message = str(e)

def initialize_session_state():
    """세션 상태 초기화"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'chatbot_ready' not in st.session_state:
        st.session_state.chatbot_ready = False

def main():
    # 세션 상태 초기화
    initialize_session_state()
    
    # 헤더
    st.markdown('<h1 class="main-header">🌸 춘천시 AI 가이드</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">강원특별자치도 춘천시의 모든 정보를 안내해드립니다</p>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("🎯 주요 기능")
        st.markdown("""
        - **🏛️ 행정기관 정보**
        - **🍽️ 맛집 & 특산품**
        - **🎪 관광명소**
        - **🚌 교통정보**
        - **📞 연락처 안내**
        """)
        
        st.header("🔧 시스템 설정")
        
        # API 키 확인
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            st.success("✅ OpenAI API 키 설정됨")
        else:
            st.error("❌ OpenAI API 키가 필요합니다")
            st.info("💡 .env 파일에 OPENAI_API_KEY를 설정해주세요")
        
        # 데이터 수집 버튼
        if st.button("🔄 데이터 업데이트"):
            with st.spinner("춘천시 데이터를 수집하고 있습니다..."):
                try:
                    collector = ChuncheonDataCollector()
                    data = collector.collect_all_data()
                    collector.save_data(data)
                    st.success(f"✅ {len(data)}개의 데이터가 업데이트되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 데이터 업데이트 실패: {e}")
        
        # 벡터 스토어 재구축 버튼
        if st.button("🔨 벡터 스토어 재구축"):
            with st.spinner("벡터 스토어를 재구축하고 있습니다..."):
                try:
                    from vector_store import ChuncheonVectorStore
                    vs = ChuncheonVectorStore()
                    vs.initialize()
                    st.success("✅ 벡터 스토어가 재구축되었습니다!")
                    # 챗봇 재초기화
                    if 'chatbot' in st.session_state:
                        del st.session_state.chatbot
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 벡터 스토어 재구축 실패: {e}")
    
    # 메인 컨텐츠
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 챗봇 초기화
        initialize_chatbot()
        
        if not st.session_state.chatbot_ready:
            st.error("❌ 챗봇 초기화에 실패했습니다.")
            if 'error_message' in st.session_state:
                st.error(f"오류: {st.session_state.error_message}")
            st.info("💡 .env 파일에 OPENAI_API_KEY가 올바르게 설정되어 있는지 확인해주세요.")
            return
        
        # 채팅 인터페이스
        st.subheader("💬 춘천시 AI와 대화하기")
        
        # 채팅 메시지 표시
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>👤 사용자:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message"><strong>🤖 춘천 AI:</strong><br>{message["content"]}</div>', unsafe_allow_html=True)
        
        # 사용자 입력
        user_input = st.chat_input("춘천에 대해 궁금한 것을 물어보세요! (예: '닭갈비 맛집 추천해줘')")
        
        if user_input:
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # 챗봇 응답 생성
            with st.spinner("답변을 생성하고 있습니다..."):
                try:
                    response = st.session_state.chatbot.chat(user_input)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            st.rerun()
        
        # 대화 초기화 버튼
        if st.button("🗑️ 대화 초기화"):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        # 빠른 질문 버튼들
        st.subheader("🚀 빠른 질문")
        
        quick_questions = [
            "춘천 닭갈비 맛집 추천해줘",
            "남이섬 가는 방법 알려줘",
            "춘천시청 연락처는?",
            "춘천역에서 시내 가는 버스",
            "막국수 체험할 수 있는 곳",
            "춘천 호수 관광 정보",
            "춘천 전통시장 위치",
            "춘천시립도서관 정보"
        ]
        
        for question in quick_questions:
            if st.button(question, key=f"quick_{question}"):
                # 질문을 채팅에 추가
                st.session_state.messages.append({"role": "user", "content": question})
                
                # 챗봇 응답 생성
                with st.spinner("답변을 생성하고 있습니다..."):
                    try:
                        response = st.session_state.chatbot.chat(question)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                
                st.rerun()
        
        # 정보 박스
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("**💡 사용 팁**")
        st.markdown("""
        - 구체적인 질문을 해주세요
        - 시설명, 음식명 등을 포함해주세요
        - 전화번호나 주소가 필요하다면 명시해주세요
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 춘천 정보 요약
        st.subheader("📍 춘천시 주요 정보")
        st.markdown("""
        **🏛️ 춘천시청**  
        📞 033-250-3000  
        📍 중앙로 1
        
        **🚂 춘천역**  
        📞 1544-7788  
        📍 근화동 472-1
        
        **🍽️ 특산품**  
        🍗 춘천닭갈비  
        🍜 막국수
        
        **🎯 주요 관광지**  
        🏝️ 남이섬  
        🌊 춘천호  
        🏛️ 춘천시민회관
        """)

if __name__ == "__main__":
    main()
