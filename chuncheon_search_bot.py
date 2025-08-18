"""
춘천시 실시간 검색 AI 챗봇
Chuncheon City Real-time Search AI Chatbot with Tavily API
"""

import os
from langchain_openai import ChatOpenAI
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# API Keys 설정
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"  # 실제 OpenAI API 키로 변경
os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"  # 실제 Tavily API 키로 변경

def format_docs(docs):
    """검색된 문서들을 포맷팅"""
    return "\n\n".join([d.page_content for d in docs])

def create_chuncheon_search_query(question):
    """춘천시 관련 검색 쿼리 최적화"""
    chuncheon_keywords = ["춘천", "춘천시", "강원도", "강원특별자치도"]
    
    # 이미 춘천 관련 키워드가 있는지 확인
    has_chuncheon = any(keyword in question for keyword in chuncheon_keywords)
    
    if not has_chuncheon:
        # 춘천 키워드가 없으면 추가
        return f"춘천시 {question}"
    
    return question

# 춘천시 전용 프롬프트 템플릿
template = """당신은 강원특별자치도 춘천시 전문 AI 가이드입니다.
아래 검색된 최신 정보를 바탕으로 춘천시에 대한 질문에 친절하고 정확하게 한국어로 답변해주세요.

검색된 최신 정보:
{context}

질문: {question}

답변 가이드라인:
- 춘천시와 관련된 정보만 제공하세요
- 전화번호, 주소, 운영시간 등 구체적인 정보를 포함하세요
- 친근하고 도움이 되는 톤으로 답변하세요
- 춘천의 특산품(닭갈비, 막국수)과 관광명소를 적극 추천하세요
- 최신 정보임을 강조하고, 변경될 수 있음을 안내하세요
- 만약 춘천과 관련 없는 질문이라면 춘천 관련 정보로 안내하세요

답변:"""

# LangChain 컴포넌트 설정
prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
retriever = TavilySearchAPIRetriever(k=5)  # 더 많은 검색 결과

# 춘천시 검색 체인 구성
def create_search_chain():
    """춘천시 검색 체인 생성"""
    
    def enhanced_retriever(question):
        """춘천시 관련 검색 쿼리 최적화 후 검색"""
        optimized_query = create_chuncheon_search_query(question)
        print(f"🔍 검색 쿼리: {optimized_query}")
        return retriever.invoke(optimized_query)
    
    chain = (
        {"context": enhanced_retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
    )
    
    return chain

def main():
    """메인 실행 함수"""
    print("🌸 춘천시 실시간 검색 AI 가이드 🌸")
    print("=" * 50)
    print("최신 정보를 실시간으로 검색해서 답변드립니다!")
    print("예시 질문:")
    print("- '춘천 닭갈비 맛집 추천해줘'")
    print("- '남이섬 입장료 얼마야?'")
    print("- '춘천 날씨 어때?'")
    print("- '춘천 축제 일정 알려줘'")
    print("- '춘천역에서 남이섬 가는 방법'")
    print("종료하려면 'quit' 또는 '종료'를 입력하세요.")
    print("=" * 50)
    
    try:
        # 검색 체인 생성
        search_chain = create_search_chain()
        
        while True:
            # 사용자 입력
            question = input("\n🙋 질문: ")
            
            # 종료 조건
            if question.lower() in ['quit', '종료', 'exit', '나가기']:
                print("🌸 춘천시 검색 AI를 이용해주셔서 감사합니다! 안녕히 가세요!")
                break
            
            if not question.strip():
                print("질문을 입력해주세요.")
                continue
            
            try:
                # 실시간 검색 및 답변 생성
                print("🔍 춘천시 관련 최신 정보를 검색하고 있습니다...")
                result = search_chain.invoke(question)
                print(f"\n🌸 춘천 AI: {result.content}\n")
                print("-" * 50)
                
            except Exception as e:
                print(f"❌ 검색 중 오류가 발생했습니다: {e}")
                print("API 키가 올바르게 설정되어 있는지 확인해주세요.\n")
    
    except KeyboardInterrupt:
        print("\n\n🌸 춘천시 검색 AI를 종료합니다. 안녕히 가세요!")
    except Exception as e:
        print(f"❌ 초기화 중 오류가 발생했습니다: {e}")
        print("OpenAI API 키와 Tavily API 키가 올바르게 설정되어 있는지 확인해주세요.")

# 개별 질문 테스트 함수
def test_question(question):
    """개별 질문 테스트"""
    try:
        search_chain = create_search_chain()
        print(f"질문: {question}")
        print("🔍 검색 중...")
        result = search_chain.invoke(question)
        print(f"답변: {result.content}")
        return result.content
    except Exception as e:
        print(f"오류: {e}")
        return None

if __name__ == "__main__":
    # 메인 실행
    main()
    
    # 테스트 예시 (주석 해제해서 사용)
    # test_question("춘천 닭갈비 맛집 추천해줘")
