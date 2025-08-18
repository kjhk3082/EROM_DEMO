"""
춘천시 AI 챗봇 메인 클래스
Chuncheon City AI Chatbot with o1-mini and RAG
"""

import os
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains import RetrievalQA
from vector_store import ChuncheonVectorStore

# 환경 변수 로드
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChuncheonAIChatbot:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4")  # o1-mini는 아직 API에서 지원되지 않을 수 있음
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            openai_api_key=self.api_key,
            model_name=self.model_name,
            temperature=0.3,
            max_tokens=1000
        )
        
        # 벡터 스토어 초기화
        self.vector_store = ChuncheonVectorStore()
        self.vector_store.initialize()
        
        # 시스템 프롬프트 설정
        self.system_prompt = """
당신은 강원특별자치도 춘천시 전문 AI 가이드입니다. 
춘천시에 대한 모든 정보를 친절하고 정확하게 안내해드립니다.

역할:
- 춘천시의 관광지, 맛집, 시설, 교통, 행정서비스 등 모든 정보 제공
- 전화번호, 주소, 운영시간 등 실용적인 정보 포함
- 친근하고 도움이 되는 톤으로 대화
- 춘천의 특산품(닭갈비, 막국수)과 문화에 대한 깊은 이해

답변 원칙:
1. 정확한 정보만 제공 (불확실한 경우 명시)
2. 구체적인 연락처와 주소 포함
3. 사용자의 상황에 맞는 맞춤형 추천
4. 춘천의 매력을 잘 전달하는 설명

검색된 정보를 바탕으로 답변하되, 추가적인 도움이 될 만한 정보도 함께 제공해주세요.
"""
    
    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """쿼리와 관련된 컨텍스트 검색"""
        if not self.vector_store.vector_store:
            return "관련 정보를 찾을 수 없습니다."
        
        try:
            results = self.vector_store.search(query, k=k)
            
            if not results:
                return "관련 정보를 찾을 수 없습니다."
            
            context = "관련 정보:\n\n"
            for i, doc in enumerate(results, 1):
                context += f"{i}. {doc.page_content}\n\n"
            
            return context
            
        except Exception as e:
            logger.error(f"컨텍스트 검색 중 오류: {e}")
            return "정보 검색 중 오류가 발생했습니다."
    
    def generate_response(self, user_query: str) -> str:
        """사용자 질문에 대한 응답 생성"""
        try:
            # 관련 컨텍스트 검색
            context = self.get_relevant_context(user_query)
            
            # 프롬프트 구성
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"""
사용자 질문: {user_query}

{context}

위 정보를 바탕으로 사용자의 질문에 친절하고 정확하게 답변해주세요.
전화번호, 주소 등 구체적인 정보가 있다면 반드시 포함해주세요.
""")
            ])
            
            # LLM 호출
            messages = prompt.format_messages()
            response = self.llm(messages)
            
            return response.content
            
        except Exception as e:
            logger.error(f"응답 생성 중 오류: {e}")
            return "죄송합니다. 응답 생성 중 오류가 발생했습니다. 다시 시도해주세요."
    
    def chat(self, user_input: str) -> str:
        """메인 채팅 인터페이스"""
        if not user_input.strip():
            return "질문을 입력해주세요."
        
        logger.info(f"사용자 질문: {user_input}")
        
        # 인사말 처리
        greetings = ["안녕", "안녕하세요", "반갑습니다", "처음", "시작"]
        if any(greeting in user_input for greeting in greetings):
            return """안녕하세요! 춘천시 AI 가이드입니다! 🌸

저는 강원특별자치도 춘천시에 대한 모든 정보를 도와드리는 AI입니다.

다음과 같은 정보를 제공해드릴 수 있어요:
• 🏛️ 행정기관 및 공공시설 정보
• 🍽️ 맛집 및 특산품 (닭갈비, 막국수 등)
• 🎯 관광명소 (남이섬, 춘천호 등)
• 🚌 교통정보 및 시설
• 📞 각종 연락처 및 주소

궁금한 것이 있으시면 언제든 물어보세요!
예: "닭갈비 맛집 추천해줘", "춘천역 연락처 알려줘", "남이섬 가는 방법" 등"""

        # 일반 질문 처리
        response = self.generate_response(user_input)
        logger.info("응답 생성 완료")
        
        return response
    
    def get_facility_info(self, facility_name: str) -> Dict[str, Any]:
        """특정 시설 정보 조회"""
        results = self.vector_store.search(facility_name, k=1)
        
        if results:
            doc = results[0]
            return {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
        
        return {"content": "해당 시설 정보를 찾을 수 없습니다.", "metadata": {}}

if __name__ == "__main__":
    # 챗봇 테스트
    try:
        chatbot = ChuncheonAIChatbot()
        
        print("춘천시 AI 챗봇이 시작되었습니다!")
        print("종료하려면 'quit' 또는 '종료'를 입력하세요.\n")
        
        while True:
            user_input = input("사용자: ")
            
            if user_input.lower() in ['quit', '종료', 'exit']:
                print("춘천시 AI 챗봇을 종료합니다. 안녕히 가세요!")
                break
            
            response = chatbot.chat(user_input)
            print(f"춘천 AI: {response}\n")
            
    except KeyboardInterrupt:
        print("\n챗봇을 종료합니다.")
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        print(".env 파일에 OPENAI_API_KEY가 설정되어 있는지 확인해주세요.")
