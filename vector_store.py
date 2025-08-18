"""
춘천시 AI 챗봇용 벡터 스토어
Vector Store for Chuncheon AI Chatbot RAG System
"""

import json
import os
from typing import List, Dict, Any
import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChuncheonVectorStore:
    def __init__(self, persist_directory: str = "vector_store"):
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'}
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )
        self.vector_store = None
        
    def load_data(self, data_file: str = "chuncheon_data.json") -> List[Document]:
        """JSON 데이터를 Document 객체로 변환"""
        documents = []
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                # 각 시설/장소에 대한 텍스트 생성
                content = f"""
이름: {item['name']}
카테고리: {item['category']}
전화번호: {item['phone']}
주소: {item['address']}
설명: {item['description']}
서비스: {', '.join(item['services'])}
"""
                
                # 특별한 정보가 있다면 추가
                if 'specialty' in item:
                    content += f"특산품/특징: {item['specialty']}\n"
                
                # 메타데이터 설정
                metadata = {
                    "name": item['name'],
                    "category": item['category'],
                    "phone": item['phone'],
                    "address": item['address']
                }
                
                documents.append(Document(
                    page_content=content.strip(),
                    metadata=metadata
                ))
            
            logger.info(f"{len(documents)}개의 문서가 로드되었습니다.")
            return documents
            
        except FileNotFoundError:
            logger.error(f"데이터 파일 {data_file}을 찾을 수 없습니다.")
            return []
        except Exception as e:
            logger.error(f"데이터 로드 중 오류 발생: {e}")
            return []
    
    def create_vector_store(self, documents: List[Document]):
        """벡터 스토어 생성"""
        if not documents:
            logger.error("문서가 없어 벡터 스토어를 생성할 수 없습니다.")
            return
        
        # 텍스트 분할
        split_docs = self.text_splitter.split_documents(documents)
        logger.info(f"{len(split_docs)}개의 청크로 분할되었습니다.")
        
        # FAISS 벡터 스토어 생성
        self.vector_store = FAISS.from_documents(
            split_docs,
            self.embeddings
        )
        
        logger.info("벡터 스토어가 성공적으로 생성되었습니다.")
    
    def save_vector_store(self):
        """벡터 스토어 저장"""
        if self.vector_store is None:
            logger.error("저장할 벡터 스토어가 없습니다.")
            return
        
        os.makedirs(self.persist_directory, exist_ok=True)
        self.vector_store.save_local(self.persist_directory)
        logger.info(f"벡터 스토어가 {self.persist_directory}에 저장되었습니다.")
    
    def load_vector_store(self):
        """저장된 벡터 스토어 로드"""
        try:
            self.vector_store = FAISS.load_local(
                self.persist_directory,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("벡터 스토어가 성공적으로 로드되었습니다.")
            return True
        except Exception as e:
            logger.error(f"벡터 스토어 로드 실패: {e}")
            return False
    
    def search(self, query: str, k: int = 3) -> List[Document]:
        """유사도 검색"""
        if self.vector_store is None:
            logger.error("벡터 스토어가 초기화되지 않았습니다.")
            return []
        
        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.info(f"'{query}' 검색 결과: {len(results)}개")
            return results
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            return []
    
    def initialize(self, data_file: str = "chuncheon_data.json"):
        """벡터 스토어 초기화"""
        # 기존 벡터 스토어가 있다면 로드 시도
        if os.path.exists(self.persist_directory):
            if self.load_vector_store():
                logger.info("기존 벡터 스토어를 사용합니다.")
                return
        
        # 새로 생성
        logger.info("새로운 벡터 스토어를 생성합니다.")
        documents = self.load_data(data_file)
        if documents:
            self.create_vector_store(documents)
            self.save_vector_store()

if __name__ == "__main__":
    # 벡터 스토어 테스트
    vs = ChuncheonVectorStore()
    vs.initialize()
    
    # 검색 테스트
    if vs.vector_store:
        results = vs.search("닭갈비 맛집")
        for i, doc in enumerate(results):
            print(f"\n결과 {i+1}:")
            print(doc.page_content)
            print(f"메타데이터: {doc.metadata}")
