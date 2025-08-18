"""
춘천시 향상된 RAG 기반 웹 챗봇
Enhanced Chuncheon City Web Chatbot with RAG
"""

from flask import Flask, render_template, request, jsonify, session
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import requests
import json
from datetime import datetime, timedelta
import glob
from typing import List, Dict, Any
from flask_cors import CORS
import uuid

# 환경 변수 로드
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'chuncheon-chatbot-secret-key-' + str(uuid.uuid4()))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
CORS(app, supports_credentials=True)

chatbot = None

# 세션별 ID 생성을 위한 UUID
import uuid

# API Keys 설정
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# 공공데이터 API 키
PUBLIC_API_KEY = "o2Ly83v52XUaFEc1EFz+VgHoNb2ErLSGPrkhn4wJ3J+478HUZCgn6DGzq7IHLKGU6C75oIpQYQvItH9nTRzamQ=="

class ChuncheonDataLoader:
    """춘천시 데이터 로더 클래스"""
    
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
                
                print(f"✅ {file_name} 로드 완료 ({len(df)}개 행)")
                
            except Exception as e:
                print(f"❌ {file_name} 로드 실패: {e}")
    
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
    """춘천시 공공 API 클라이언트"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_urls = {
            "events": "https://apis.data.go.kr/4180000/ccevent",
            "culture": "https://apis.data.go.kr/4180000/ccculture",
            "tourism": "https://apis.data.go.kr/4180000/cctour"
        }
    
    def get_events(self, event_name: str = None) -> List[Dict]:
        """공연행사 정보 조회 (현재 시간 이후 행사만)"""
        try:
            params = {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": "20",  # 더 많이 가져와서 필터링
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
                                    start_date = datetime.strptime(event['startDt'], '%Y%m%d')
                                    # 종료일이 현재보다 미래인 행사만
                                    if end_date >= current_date:
                                        filtered_events.append(event)
                            except:
                                continue
                        return filtered_events[:10]  # 최대 10개만 반환
            return []
            
        except Exception as e:
            print(f"이벤트 API 호출 실패: {e}")
            return []
    
    def get_culture_festivals(self, culture_name: str = None) -> List[Dict]:
        """문화축제 정보 조회"""
        try:
            params = {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": "10",
                "_type": "json"
            }
            
            if culture_name:
                params["cultureNm"] = culture_name
            
            response = requests.get(
                f"{self.base_urls['culture']}/getCultureList",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'body' in data['response']:
                    items = data['response']['body'].get('items', {})
                    if items and 'item' in items:
                        return items['item'] if isinstance(items['item'], list) else [items['item']]
            return []
            
        except Exception as e:
            print(f"문화축제 API 호출 실패: {e}")
            return []
    
    def get_tourist_spots(self, tour_name: str = None) -> List[Dict]:
        """관광지 정보 조회"""
        try:
            params = {
                "serviceKey": self.api_key,
                "pageNo": "1",
                "numOfRows": "10",
                "_type": "json"
            }
            
            if tour_name:
                params["tourNm"] = tour_name
            
            response = requests.get(
                f"{self.base_urls['tourism']}/getTourList",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'response' in data and 'body' in data['response']:
                    items = data['response']['body'].get('items', {})
                    if items and 'item' in items:
                        return items['item'] if isinstance(items['item'], list) else [items['item']]
            return []
            
        except Exception as e:
            print(f"관광지 API 호출 실패: {e}")
            return []

class EnhancedChuncheonChatbot:
    def __init__(self):
        print("🚀 춘천시 RAG 챗봇 초기화 중...")
        
        # OpenAI API 키 설정
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
        
        # Tavily API 키 설정
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not self.tavily_api_key:
            print("⚠️ TAVILY_API_KEY가 설정되지 않았습니다. 웹 검색 기능이 제한됩니다.")
        
        # 세션별 대화 기록 저장
        self.conversation_history = {}
        
        # 데이터 로더 초기화
        self.data_loader = ChuncheonDataLoader()
        self.api_client = ChuncheonAPIClient(PUBLIC_API_KEY)
        
        # 임베딩 및 벡터스토어 초기화
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self.retriever = None
        
        # Tavily 검색 초기화
        self.tavily_retriever = None
        if self.tavily_api_key:
            try:
                from langchain_community.retrievers import TavilySearchAPIRetriever
                self.tavily_retriever = TavilySearchAPIRetriever(
                    k=3,
                    api_key=self.tavily_api_key
                )
                print("✅ Tavily 웹 검색 기능 활성화")
            except Exception as e:
                print(f"⚠️ Tavily 초기화 실패: {e}")
                self.tavily_retriever = None
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        # 프롬프트 템플릿
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
        
        # LLMChain 초기화
        from langchain.chains import LLMChain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def initialize(self, csv_folder: str):
        """챗봇 초기화 - CSV 데이터 로드 및 벡터스토어 생성"""
        print("🚀 춘천시 RAG 챗봇 초기화 중...")
        
        # CSV 파일 로드
        self.data_loader.load_csv_files(csv_folder)
        
        # 벡터스토어 생성
        documents = self.data_loader.get_documents()
        if documents:
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            # retriever 생성
            self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})
            print(f"✅ 벡터스토어 생성 완료 ({len(documents)}개 문서)")
        else:
            print("⚠️ 로드된 문서가 없습니다")
    
    def search_local_data(self, query: str, k: int = 5) -> str:
        """로컬 벡터스토어에서 관련 정보 검색"""
        if not self.vector_store:
            return "로컬 데이터베이스가 준비되지 않았어요 ㅠㅠ"
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            if results:
                return "\n\n".join([doc.page_content for doc in results])
            return "관련 정보를 찾을 수 없어요"
        except Exception as e:
            return f"검색 중 오류 발생: {e}"
    
    def search_api_data(self, query: str) -> str:
        """공공 API에서 실시간 정보 검색"""
        api_results = []
        
        # 키워드 기반 API 호출 결정
        if any(word in query for word in ["전기차", "충전소", "충전", "EV", "전기자동차"]):
            # 전기차 충전소 정보
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
            # 음식점 정보 조회
            if "닭갈비" in query:
                api_results.append("\n🍗 춘천 닭갈비 맛집 추천:")
                api_results.append("""🍗 **춘천 닭갈비 맛집**:
- **춘천 닭갈비 1번지**: 
  • 📍 주소: 춘천시 중앙로 37
  • 📞 전화: 033-252-3377
  • ⏰ 영업시간: 10:00~22:00
  • 💝 추천 메뉴: 닭갈비 정식, 닭갈비 뼈찜
- **춘천 닭갈비 2번지**: 
  • 📍 주소: 춘천시 중앙로 45
  • 📞 전화: 033-252-3378
  • ⏰ 영업시간: 10:00~22:00
  • 💝 추천 메뉴: 닭갈비 정식, 닭갈비 뼈찜""")
            
            elif "막국수" in query:
                api_results.append("\n🍜 춘천 막국수 맛집 추천:")
                api_results.append("""🍜 **춘천 막국수 맛집**:
- **춘천 막국수 1번지**: 
  • 📍 주소: 춘천시 중앙로 50
  • 📞 전화: 033-252-3379
  • ⏰ 영업시간: 10:00~22:00
  • 💝 추천 메뉴: 막국수, 비빔막국수
- **춘천 막국수 2번지**: 
  • 📍 주소: 춘천시 중앙로 55
  • 📞 전화: 033-252-3380
  • ⏰ 영업시간: 10:00~22:00
  • 💝 추천 메뉴: 막국수, 비빔막국수""")
            
        elif any(word in query for word in ["행사", "공연", "이벤트", "축제", "문화"]):
            # 이벤트/축제 정보 조회
            events = self.api_client.get_events()
            if events:
                api_results.append("\n🎉 현재 진행중인 행사/공연:")
                for event in events[:3]:
                    api_results.append(f"- {event.get('eventNm', '행사명 없음')}: {event.get('eventPlace', '장소 미정')} ({event.get('eventStartDt', '')}~{event.get('eventEndDt', '')})")
            
            festivals = self.api_client.get_culture_festivals()
            if festivals:
                api_results.append("\n🎊 문화축제 정보:")
                for fest in festivals[:3]:
                    api_results.append(f"- {fest.get('cultureNm', '축제명 없음')}: {fest.get('culturePlace', '장소 미정')}")
        
        if any(word in query for word in ["관광", "여행", "명소", "가볼만한"]):
            # 관광지 정보 조회
            spots = self.api_client.get_tourist_spots()
            if spots:
                api_results.append("\n🏞️ 추천 관광지:")
                for spot in spots[:3]:
                    api_results.append(f"- {spot.get('tourNm', '관광지명 없음')}: {spot.get('tourAddr', '주소 미정')}")
        
        return "\n".join(api_results) if api_results else "실시간 API 정보 없음"
    
    def search_web(self, query: str) -> str:
        """Tavily를 통한 웹 검색"""
        try:
            # 춘천 관련 키워드 추가
            search_query = f"춘천시 {query}" if "춘천" not in query else query
            docs = self.tavily_retriever.invoke(search_query)
            if docs:
                return "\n\n".join([doc.page_content[:300] for doc in docs[:2]])
            return "웹 검색 결과 없음"
        except Exception as e:
            return f"웹 검색 오류: {e}"
    
    def generate_response(self, message: str, session_id: str = "default") -> str:
        """사용자 메시지에 대한 응답 생성"""
        try:
            # 세션별 대화 기록 관리
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
                print(f"✅ 새로운 세션 생성: {session_id}")
            
            print(f"\n{'='*50}")
            print(f"📥 세션 {session_id} - 받은 질문: {message}")
            print(f"📊 현재 대화 기록 수: {len(self.conversation_history[session_id])}")
            
            # 현재 메시지를 먼저 대화 기록에 추가
            self.conversation_history[session_id].append({"role": "user", "content": message})
            
            # 최근 10개 대화만 유지 (메모리 관리)
            if len(self.conversation_history[session_id]) > 10:
                self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
            
            # 이전 대화 컨텍스트 생성 (현재 메시지 제외)
            conversation_context = ""
            if len(self.conversation_history[session_id]) > 1:
                # 현재 메시지를 제외한 이전 대화들만
                recent_messages = self.conversation_history[session_id][:-1][-4:]  # 현재 제외, 최근 2턴
                conversation_context = "\n".join([
                    f"{msg['role']}: {msg['content'][:100]}..." if len(msg['content']) > 100 else f"{msg['role']}: {msg['content']}"
                    for msg in recent_messages
                ])
                print(f"📝 이전 대화 컨텍스트:\n{conversation_context}")
            
            # 1. 관련 문서 검색
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
                    print(f"웹 검색 오류: {e}")
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
            # 체인에 메시지 전달 및 응답 생성
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
            
            # 디버그 정보 제거 - text 필드만 반환
            if isinstance(response_text, str) and response_text.startswith('{') and 'text' in response_text:
                try:
                    import json
                    parsed = json.loads(response_text.replace("'", '"'))
                    if 'text' in parsed:
                        response_text = parsed['text']
                except:
                    pass
            
            # 답변만 대화 기록에 추가 (질문은 이미 위에서 추가함)
            self.conversation_history[session_id].append({"role": "assistant", "content": response_text})
            
            print(f"📤 생성된 답변: {response_text[:100]}...")
            print(f"✅ 대화 기록 업데이트 완료 (총 {len(self.conversation_history[session_id])}개)")
            print(f"{'='*50}")
            
            return response_text
            
        except Exception as e:
            print(f"답변 생성 실패: {e}")
            import traceback
            traceback.print_exc()
            return "죄송합니다. 답변 생성 중 문제가 발생했습니다. 다시 한 번 질문해주시겠어요?"

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('enhanced_index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """채팅 엔드포인트"""
    global chatbot
    
    if not chatbot:
        return jsonify({
            'success': False,
            'message': '챗봇이 초기화되지 않았습니다. 잠시 후 다시 시도해주세요.'
        })
    
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                'success': False,
                'message': '메시지를 입력해주세요.'
            })
        
        # 세션 ID 가져오기 (없으면 생성)
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            print(f"새 세션 ID 생성: {session['session_id']}")
        
        session_id = session['session_id']
        print(f"현재 세션 ID: {session_id}")
        print(f"받은 메시지: {user_message}")
        
        # 응답 생성
        response = chatbot.generate_response(user_message, session_id)
        print(f"반환할 응답: {response[:100]}...")
        
        return jsonify({
            'success': True,
            'message': response
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'앗, 죄송해요 ㅠㅠ 잠시 문제가 생겼어요: {str(e)}'
        })

@app.route('/quick-questions')
def quick_questions():
    """빠른 질문 목록 API"""
    questions = [
        {
            'icon': '🍗',
            'text': '춘천 닭갈비 맛집 어디가 진짜 맛있어?',
            'category': '맛집'
        },
        {
            'icon': '🎉',
            'text': '이번 주 춘천에서 뭐 재밌는 행사 있어?',
            'category': '행사'
        },
        {
            'icon': '💉',
            'text': '독감 예방접종 어디서 할 수 있어?',
            'category': '의료'
        },
        {
            'icon': '🏛️',
            'text': '주민등록등본 떼려면 어디로 가야해?',
            'category': '행정'
        },
        {
            'icon': '🚗',
            'text': '춘천에 전기차 충전소 많아?',
            'category': '교통'
        },
        {
            'icon': '🌸',
            'text': '봄에 가볼만한 춘천 명소 추천해줘',
            'category': '관광'
        },
        {
            'icon': '👴',
            'text': '우리 할머니 일자리 프로그램 있을까?',
            'category': '복지'
        },
        {
            'icon': '📞',
            'text': '시청 민원실 전화번호 알려줘',
            'category': '연락처'
        }
    ]
    
    return jsonify(questions)

@app.route('/initialize', methods=['POST'])
def initialize():
    """챗봇 초기화 엔드포인트"""
    try:
        csv_folder = "./민원 관련"
        chatbot.initialize(csv_folder)
        return jsonify({
            'success': True,
            'message': '챗봇이 성공적으로 초기화되었습니다!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'초기화 실패: {str(e)}'
        })

if __name__ == '__main__':
    # 서버 시작시 자동 초기화
    print("🏃 춘천시 RAG 챗봇 서버 시작...")
    csv_folder = "./민원 관련"
    chatbot = EnhancedChuncheonChatbot()
    chatbot.initialize(csv_folder)
    app.run(debug=True, host='0.0.0.0', port=8080)
