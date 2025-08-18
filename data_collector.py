"""
춘천시 데이터 수집기
Chuncheon City Data Collector for RAG System
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import time
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChuncheonDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def collect_government_data(self) -> List[Dict[str, Any]]:
        """춘천시청 공식 데이터 수집"""
        data = []
        
        # 춘천시 주요 시설 정보
        facilities = [
            {
                "name": "춘천시청",
                "category": "행정기관",
                "phone": "033-250-3000",
                "address": "강원특별자치도 춘천시 중앙로 1",
                "description": "춘천시 행정업무 총괄",
                "services": ["민원업무", "행정서비스", "시정안내"]
            },
            {
                "name": "춘천시립도서관",
                "category": "문화시설",
                "phone": "033-250-3600",
                "address": "강원특별자치도 춘천시 평화로 125",
                "description": "시민을 위한 도서관 서비스",
                "services": ["도서대출", "열람실", "문화프로그램"]
            },
            {
                "name": "춘천시민회관",
                "category": "문화시설",
                "phone": "033-259-5800",
                "address": "강원특별자치도 춘천시 금강로 11",
                "description": "시민을 위한 문화공연장",
                "services": ["공연관람", "대관서비스", "문화행사"]
            },
            {
                "name": "춘천중앙시장",
                "category": "전통시장",
                "phone": "033-251-3648",
                "address": "강원특별자치도 춘천시 중앙로 67",
                "description": "춘천의 대표 전통시장",
                "services": ["장보기", "먹거리", "전통상품"]
            },
            {
                "name": "남이섬",
                "category": "관광지",
                "phone": "031-580-8114",
                "address": "강원특별자치도 춘천시 남산면 남이섬길 1",
                "description": "춘천의 대표 관광명소",
                "services": ["관광", "숙박", "레저활동"]
            },
            {
                "name": "춘천호",
                "category": "관광지",
                "phone": "033-250-3089",
                "address": "강원특별자치도 춘천시 신북읍",
                "description": "아름다운 호수 경관",
                "services": ["관광", "수상레저", "낚시"]
            }
        ]
        
        data.extend(facilities)
        logger.info(f"수집된 시설 정보: {len(facilities)}개")
        
        return data
    
    def collect_restaurant_data(self) -> List[Dict[str, Any]]:
        """춘천 맛집 정보 수집"""
        restaurants = [
            {
                "name": "춘천닭갈비골목",
                "category": "음식점",
                "phone": "033-252-9995",
                "address": "강원특별자치도 춘천시 조양동",
                "description": "춘천의 대표 음식 닭갈비 전문거리",
                "services": ["닭갈비", "막국수", "전통음식"],
                "specialty": "춘천닭갈비"
            },
            {
                "name": "막국수체험박물관",
                "category": "체험시설",
                "phone": "033-244-8869",
                "address": "강원특별자치도 춘천시 신북읍 신샘밭로 264",
                "description": "막국수 만들기 체험과 시식",
                "services": ["막국수체험", "전시관람", "시식"],
                "specialty": "막국수"
            },
            {
                "name": "춘천명동닭갈비",
                "category": "음식점",
                "phone": "033-253-6600",
                "address": "강원특별자치도 춘천시 명동길 9",
                "description": "50년 전통의 닭갈비 전문점",
                "services": ["닭갈비", "볶음밥", "전통음식"],
                "specialty": "닭갈비"
            }
        ]
        
        logger.info(f"수집된 맛집 정보: {len(restaurants)}개")
        return restaurants
    
    def collect_transportation_data(self) -> List[Dict[str, Any]]:
        """교통 정보 수집"""
        transportation = [
            {
                "name": "춘천역",
                "category": "교통시설",
                "phone": "1544-7788",
                "address": "강원특별자치도 춘천시 근화동 472-1",
                "description": "춘천의 주요 기차역",
                "services": ["기차승차", "교통연결", "여행안내"]
            },
            {
                "name": "춘천터미널",
                "category": "교통시설",
                "phone": "033-252-6441",
                "address": "강원특별자치도 춘천시 온의동 664-2",
                "description": "춘천의 시외버스터미널",
                "services": ["시외버스", "고속버스", "교통연결"]
            },
            {
                "name": "춘천시내버스",
                "category": "교통서비스",
                "phone": "033-250-3470",
                "address": "춘천시 전역",
                "description": "춘천시 시내버스 운행",
                "services": ["시내교통", "버스노선안내", "교통카드"]
            }
        ]
        
        logger.info(f"수집된 교통 정보: {len(transportation)}개")
        return transportation
    
    def collect_all_data(self) -> List[Dict[str, Any]]:
        """모든 데이터 수집"""
        all_data = []
        
        logger.info("춘천시 데이터 수집 시작...")
        
        # 각 카테고리별 데이터 수집
        all_data.extend(self.collect_government_data())
        all_data.extend(self.collect_restaurant_data())
        all_data.extend(self.collect_transportation_data())
        
        logger.info(f"총 {len(all_data)}개의 데이터 수집 완료")
        
        return all_data
    
    def save_data(self, data: List[Dict[str, Any]], filename: str = "chuncheon_data.json"):
        """수집된 데이터 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"데이터가 {filename}에 저장되었습니다.")

if __name__ == "__main__":
    collector = ChuncheonDataCollector()
    data = collector.collect_all_data()
    collector.save_data(data)
