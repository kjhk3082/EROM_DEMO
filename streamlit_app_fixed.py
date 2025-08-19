"""
춘천시 AI 챗봇 Streamlit 앱 - 완전 새로운 디자인
"""

import streamlit as st
import os
import pandas as pd
import numpy as np
from datetime import datetime
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
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="춘천시 AI 도우미 - 춘이",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 간단한 CSS 스타일
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }
    
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    
    .bot-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    
    .quick-btn {
        margin: 0.2rem;
        padding: 0.5rem 1rem;
        background-color: #667eea;
        color: white;
        border: none;
        border-radius: 20px;
        cursor: pointer;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: 1px solid #667eea;
        color: #667eea;
    }
    
    .stButton > button:hover {
        background-color: #667eea;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# API 키 설정
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

PUBLIC_API_KEY = "o2Ly83v52XUaFEc1EFz+VgHoNb2ErLSGPrkhn4wJ3J+478HUZCgn6DGzq7IHLKGU6C75oIpQYQvItH9nTRzamQ=="

class SimpleChuncheonChatbot:
    """간단하고 안정적인 춘천시 챗봇"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        self.prompt_template = """당신은 '춘이'라는 이름의 강원특별자치도 춘천시 AI 도우미입니다.

# 필수 지침:
1. 항상 친근하고 도움이 되는 태도로 한국어로 응답하세요
2. 춘천시와 관련된 정보를 우선적으로 제공하세요
3. 정확한 정보가 없으면 "정확한 정보를 찾을 수 없습니다"라고 답하세요
4. 존댓말을 사용하세요

# 현재 시각: {current_time}

# 사용자 질문: {question}

답변:"""
        
        self.prompt = ChatPromptTemplate.from_template(self.prompt_template)
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def generate_response(self, message: str) -> str:
        """사용자 메시지에 대한 응답 생성"""
        try:
            current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")
            
            response = self.chain.invoke({
                "question": message,
                "current_time": current_time
            })
            
            if isinstance(response, dict):
                return response.get('text', str(response))
            elif hasattr(response, 'content'):
                return response.content
            else:
                return str(response)
                
        except Exception as e:
            return f"죄송합니다. 답변 생성 중 문제가 발생했습니다: {str(e)}"

def initialize_chatbot():
    """챗봇 초기화"""
    if 'chatbot' not in st.session_state:
        try:
            st.session_state.chatbot = SimpleChuncheonChatbot()
            st.session_state.chatbot_ready = True
            return True
        except Exception as e:
            st.error(f"❌ 챗봇 초기화 실패: {e}")
            return False
    return True

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
    if not initialize_chatbot():
        st.stop()
    
    # 메인 컨테이너
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        # 환영 메시지
        if not st.session_state.messages:
            st.info("👋 안녕하세요! 춘천에 대해 궁금한 것이 있으시면 언제든 물어보세요!")
        
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
        st.subheader("🚀 빠른 질문")
        
        col_a, col_b, col_c, col_d = st.columns(4)
        
        quick_questions = [
            "춘천 닭갈비 맛집 추천",
            "이번 주 춘천 행사",
            "춘천 전기차 충전소",
            "춘천 관광지 추천",
            "춘천시 청년 정책",
            "춘천 카페 추천",
            "춘천 숙박시설",
            "시청 연락처"
        ]
        
        cols = [col_a, col_b, col_c, col_d]
        
        for i, question in enumerate(quick_questions):
            col = cols[i % 4]
            with col:
                if st.button(question, key=f"quick_{i}"):
                    st.session_state.messages.append({"role": "user", "content": question})
                    
                    # AI 응답 생성
                    with st.spinner("춘이가 생각중..."):
                        response = st.session_state.chatbot.generate_response(question)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    
                    st.rerun()
        
        # 채팅 입력
        user_input = st.chat_input("춘천에 대해 뭐든지 물어보세요...")
        
        if user_input:
            # 사용자 메시지 추가
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # AI 응답 생성
            with st.spinner("춘이가 답변을 준비중입니다..."):
                response = st.session_state.chatbot.generate_response(user_input)
                st.session_state.messages.append({"role": "assistant", "content": response})
            
            st.rerun()
    
    # 하단 정보
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🌸 <strong>춘천시 AI 도우미 춘이</strong> - 2025년 프롬프톤 출품작 🌸</p>
        <p>개발팀: 김재형(팀장), 김성호, 김강민 | 한림대학교</p>
        <p>🏛️ 춘천시청: 033-250-3000 | 🚂 춘천역: 1544-7788 | 🍗 특산품: 닭갈비, 막국수</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
