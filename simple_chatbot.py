"""
춘천시 AI 챗봇 - 간단한 LangChain 파이프라인 버전
Chuncheon City AI Chatbot - Simple LangChain Pipeline Version
"""

import os
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import json

# OpenAI API Key 설정
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"  # 실제 API 키로 변경하세요

def load_chuncheon_data():
    """춘천시 데이터 로드"""
    chuncheon_data = [
        {
            "name": "춘천시청",
            "category": "행정기관",
            "phone": "033-250-3000",
            "address": "강원특별자치도 춘천시 중앙로 1",
            "description": "춘천시 행정업무 총괄. 민원업무, 행정서비스, 시정안내를 제공합니다.",
            "services": ["민원업무", "행정서비스", "시정안내"]
        },
        {
            "name": "춘천닭갈비골목",
            "category": "음식점",
            "phone": "033-252-9995",
            "address": "강원특별자치도 춘천시 조양동",
            "description": "춘천의 대표 음식 닭갈비 전문거리. 50년 전통의 맛있는 닭갈비를 맛볼 수 있습니다.",
            "services": ["닭갈비", "막국수", "전통음식"],
            "specialty": "춘천닭갈비"
        },
        {
            "name": "남이섬",
            "category": "관광지",
            "phone": "031-580-8114",
            "address": "강원특별자치도 춘천시 남산면 남이섬길 1",
            "description": "춘천의 대표 관광명소. 아름다운 자연경관과 다양한 체험활동을 즐길 수 있습니다.",
            "services": ["관광", "숙박", "레저활동"]
        },
        {
            "name": "춘천역",
            "category": "교통시설",
            "phone": "1544-7788",
            "address": "강원특별자치도 춘천시 근화동 472-1",
            "description": "춘천의 주요 기차역. 서울과 춘천을 연결하는 중요한 교통 거점입니다.",
            "services": ["기차승차", "교통연결", "여행안내"]
        },
        {
            "name": "막국수체험박물관",
            "category": "체험시설",
            "phone": "033-244-8869",
            "address": "강원특별자치도 춘천시 신북읍 신샘밭로 264",
            "description": "막국수 만들기 체험과 시식을 할 수 있는 곳. 춘천의 대표 음식인 막국수를 직접 만들어볼 수 있습니다.",
            "services": ["막국수체험", "전시관람", "시식"],
            "specialty": "막국수"
        },
        {
            "name": "춘천호",
            "category": "관광지",
            "phone": "033-250-3089",
            "address": "강원특별자치도 춘천시 신북읍",
            "description": "아름다운 호수 경관을 자랑하는 춘천의 명소. 수상레저와 낚시를 즐길 수 있습니다.",
            "services": ["관광", "수상레저", "낚시"]
        }
    ]
    
    return chuncheon_data

def create_documents(data):
    """데이터를 Document 객체로 변환"""
    documents = []
    
    for item in data:
        content = f"""
이름: {item['name']}
카테고리: {item['category']}
전화번호: {item['phone']}
주소: {item['address']}
설명: {item['description']}
서비스: {', '.join(item['services'])}
"""
        if 'specialty' in item:
            content += f"특산품/특징: {item['specialty']}\n"
        
        documents.append(Document(
            page_content=content.strip(),
            metadata={
                "name": item['name'],
                "category": item['category'],
                "phone": item['phone']
            }
        ))
    
    return documents

def format_docs(docs):
    """검색된 문서들을 포맷팅"""
    return "\n\n".join([d.page_content for d in docs])

def create_chuncheon_chatbot():
    """춘천시 AI 챗봇 생성"""
    
    # 1. 데이터 로드 및 문서 생성
    print("춘천시 데이터를 로드하고 있습니다...")
    data = load_chuncheon_data()
    documents = create_documents(data)
    
    # 2. 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    split_docs = text_splitter.split_documents(documents)
    
    # 3. 임베딩 및 벡터스토어 생성
    print("벡터 스토어를 생성하고 있습니다...")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'}
    )
    
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    # 4. 프롬프트 템플릿
    template = """당신은 강원특별자치도 춘천시 전문 AI 가이드입니다.
주어진 정보를 바탕으로 춘천시에 대한 질문에 친절하고 정확하게 한국어로 답변해주세요.

춘천시 정보:
{context}

질문: {question}

답변할 때 다음 사항을 지켜주세요:
- 전화번호와 주소를 포함해서 구체적으로 답변
- 친근하고 도움이 되는 톤으로 대화
- 춘천의 특산품(닭갈비, 막국수)과 관광명소를 적극 추천
- 정확한 정보만 제공하고, 불확실한 경우 명시

답변:"""

    prompt = ChatPromptTemplate.from_template(template)
    
    # 5. LLM 설정
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3
    )
    
    # 6. 체인 구성
    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    print("춘천시 AI 챗봇이 준비되었습니다! 🌸")
    return chain

def main():
    """메인 실행 함수"""
    try:
        # 챗봇 생성
        chatbot_chain = create_chuncheon_chatbot()
        
        print("\n" + "="*50)
        print("🌸 춘천시 AI 가이드에 오신 것을 환영합니다! 🌸")
        print("="*50)
        print("춘천시에 대해 궁금한 것을 물어보세요!")
        print("예시: '닭갈비 맛집 추천해줘', '남이섬 가는 방법', '춘천역 연락처'")
        print("종료하려면 'quit' 또는 '종료'를 입력하세요.\n")
        
        while True:
            # 사용자 입력
            question = input("🙋 질문: ")
            
            # 종료 조건
            if question.lower() in ['quit', '종료', 'exit', '나가기']:
                print("🌸 춘천시 AI 가이드를 이용해주셔서 감사합니다! 안녕히 가세요!")
                break
            
            if not question.strip():
                print("질문을 입력해주세요.")
                continue
            
            try:
                # 챗봇 실행
                print("🤖 답변을 생성하고 있습니다...")
                result = chatbot_chain.invoke(question)
                print(f"\n🌸 춘천 AI: {result}\n")
                print("-" * 50)
                
            except Exception as e:
                print(f"❌ 오류가 발생했습니다: {e}")
                print("다시 시도해주세요.\n")
    
    except KeyboardInterrupt:
        print("\n\n🌸 춘천시 AI 가이드를 종료합니다. 안녕히 가세요!")
    except Exception as e:
        print(f"❌ 챗봇 초기화 중 오류가 발생했습니다: {e}")
        print("OpenAI API 키가 올바르게 설정되어 있는지 확인해주세요.")

if __name__ == "__main__":
    main()
