from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import asyncio
from typing import List, Dict, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
import urllib.parse
import urllib3

# 환경변수 로드
load_dotenv()

app = FastAPI(title="Sejong Library Book Recommendation API", version="2.0.0")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class SejongBookRecommendationRequest(BaseModel):
    lecture_title: str
    major_field: str
    interest_technology: str
    learning_difficulty: str

class SejongBookInfo(BaseModel):
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    publication_year: Optional[str] = None
    location: Optional[str] = None
    availability: Optional[str] = None
    call_number: Optional[str] = None
    subject_category: Optional[str] = None
    description: Optional[str] = None
    detail_url: Optional[str] = None

class SejongBookRecommendationResponse(BaseModel):
    recommended_books: List[SejongBookInfo]
    search_keywords: List[str]
    total_books_analyzed: int
    recommendation_reason: str

class SejongLibraryCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://library.sejong.ac.kr"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
        self.session.headers.update(self.headers)
        self.session.verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    async def generate_search_keywords(self, lecture_title: str) -> List[str]:
        """OpenAI API로 검색 키워드 10개 생성"""
        try:
            prompt = f"""
            강의 제목: "{lecture_title}"
            
            이 강의와 관련성이 높은 도서 검색 키워드 10개를 생성해주세요.
            키워드는 구체적이고 실용적이어야 하며, 대학 도서관에서 검색할 만한 학술적인 키워드로 생성해주세요.
            
            응답 형식:
            1. 키워드1
            2. 키워드2
            ...
            10. 키워드10
            
            키워드만 나열해주세요.
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 교육 전문가이자 도서 추천 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            keywords = []
            
            lines = content.strip().split('\n')
            for line in lines:
                if re.match(r'^\d+\.', line.strip()):
                    keyword = re.sub(r'^\d+\.\s*', '', line.strip())
                    if keyword:
                        keywords.append(keyword)
            
            return keywords[:10]
            
        except Exception as e:
            print(f"키워드 생성 실패: {e}")
            return [lecture_title, "입문", "기초", "이론", "실습", "개론", "개념", "방법론", "응용", "기본"]
    
    async def search_books_by_keyword(self, keyword: str, limit: int = 5) -> List[Dict]:
        """세종대 학술정보원에서 키워드로 도서 검색"""
        try:
            print(f"'{keyword}' 키워드로 세종대 학술정보원 검색 중...")
            
            # 메인 페이지 방문 (세션 유지)
            main_response = self.session.get(f"{self.base_url}/index.ax", verify=False)
            await asyncio.sleep(1)
            
            # 검색 URL 구성
            search_url = f"{self.base_url}/search/Search.Result.ax"
            params = {
                'sid': '1',
                'q': keyword,
                'facet': 'Y'
            }
            
            response = self.session.get(search_url, params=params, verify=False)
            response.raise_for_status()
            
            if "오류발생" in response.text:
                print("❌ 세종대 서버 오류 발생")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            # ul.listType01 li 구조에서 도서 정보 추출
            book_items = soup.select('ul.listType01 li')
            
            if not book_items:
                print("검색 결과를 찾을 수 없습니다.")
                return []
            
            print(f"✅ {len(book_items)}개 도서 발견")
            
            for item in book_items[:limit]:
                try:
                    book_info = await self.extract_book_info(item)
                    if book_info and book_info.get('title'):
                        books.append(book_info)
                        print(f"수집된 책: {book_info['title']}")
                    
                    if len(books) >= limit:
                        break
                        
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"책 정보 추출 실패: {e}")
                    continue
            
            return books
            
        except Exception as e:
            print(f"'{keyword}' 검색 실패: {e}")
            return []
    
    async def extract_book_info(self, item) -> Dict:
        """ul.listType01 li 구조에서 도서 정보 추출"""
        try:
            book_info = {
                'title': '',
                'author': '',
                'publisher': '',
                'publication_year': '',
                'location': '',
                'call_number': '',
                'availability': '',
                'isbn': '',
                'subject_category': '',
                'detail_url': ''
            }
            
            # dl.bookList 찾기
            book_list = item.find('dl', class_='bookList')
            if not book_list:
                return book_info
                
            # 제목 링크 찾기 (a.title)
            title_link = book_list.find('a', class_='title')
            if title_link:
                book_info['title'] = title_link.get_text().strip()
                
                # JavaScript 링크에서 ID 추출
                onclick = title_link.get('onclick', '')
                if 'goDetail(' in onclick:
                    match = re.search(r'goDetail\((\d+)\)', onclick)
                    if match:
                        book_id = match.group(1)
                        book_info['detail_url'] = f"{self.base_url}/search/DetailView.ax?cid={book_id}"
            
            # body div에서 저자, 출판사, 출판년도 정보 추출
            body_div = book_list.find('div', class_='body')
            if body_div:
                body_text = body_div.get_text()
                
                if '/' in body_text:
                    info_part = body_text.split('/', 1)[1].strip()
                    parts = info_part.split('.')
                    if len(parts) >= 2:
                        book_info['author'] = parts[0].strip()
                        
                        pub_part = parts[1].strip()
                        if ',' in pub_part:
                            pub_parts = pub_part.split(',')
                            book_info['publisher'] = pub_parts[0].strip()
                            if len(pub_parts) > 1:
                                year_text = pub_parts[1].strip()
                                year_match = re.search(r'\d{4}', year_text)
                                if year_match:
                                    book_info['publication_year'] = year_match.group()
            
            # 소장 정보 추출 (p.tag)
            tag_p = book_list.find('p', class_='tag')
            if tag_p:
                tag_text = tag_p.get_text()
                
                # 소장위치 추출
                location_link = tag_p.find('a')
                if location_link:
                    book_info['location'] = location_link.get_text().strip()
                
                # 청구기호 추출
                call_number_match = re.search(r'\[([^\]]+)\]', tag_text)
                if call_number_match:
                    book_info['call_number'] = call_number_match.group(1).strip()
                
                # 대출상태 추출
                if '대출가능' in tag_text:
                    book_info['availability'] = '대출가능'
                elif '대출중' in tag_text:
                    book_info['availability'] = '대출중'
                elif '이용불가' in tag_text:
                    book_info['availability'] = '이용불가'
                elif '정리중' in tag_text:
                    book_info['availability'] = '정리중'
            
            return book_info
            
        except Exception as e:
            print(f"도서 정보 추출 중 오류: {e}")
            return {
                'title': '',
                'author': '',
                'publisher': '',
                'publication_year': '',
                'location': '',
                'call_number': '',
                'availability': '',
                'isbn': '',
                'subject_category': '',
                'detail_url': ''
            }
    
    async def get_ai_book_recommendations(self, books: List[Dict], interest_technology: str, learning_difficulty: str) -> Dict:
        """AI를 사용해서 책들 중 최적의 5개 선정"""
        try:
            if len(books) <= 5:
                return {
                    'books': books,
                    'reason': f"총 {len(books)}권의 도서가 검색되어 모든 도서를 추천합니다."
                }
            
            # 책 정보를 OpenAI에 전달
            books_data = []
            for i, book in enumerate(books, 1):
                book_info = {
                    "번호": i,
                    "제목": book.get('title', 'N/A'),
                    "저자": book.get('author', 'N/A'),
                    "출판사": book.get('publisher', 'N/A'),
                    "소장위치": book.get('location', 'N/A'),
                    "도서상태": book.get('availability', 'N/A')
                }
                books_data.append(book_info)
            
            books_json = json.dumps(books_data, ensure_ascii=False, indent=2)
            
            prompt = f"""
다음은 세종대학교 학술정보원 소장 도서 정보입니다:

{books_json}

사용자 정보:
- 관심 기술: {interest_technology}
- 학습 난이도: {learning_difficulty}

위 도서 중에서 사용자의 관심 기술 "{interest_technology}"와 가장 관련성이 높고, 
학습 난이도 "{learning_difficulty}"에 적합한 5개의 책을 선정해주세요.

응답은 반드시 다음 JSON 형식으로 해주세요:
{{
  "selected_books": [1, 2, 3, 4, 5],
  "analysis_reason": "상세한 선정 이유"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 대학 도서관 전문 사서입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            
            # JSON 응답 파싱
            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    ai_response = json.loads(json_str)
                    
                    selected_indices = ai_response.get('selected_books', [])
                    reason = ai_response.get('analysis_reason', '')
                else:
                    numbers = re.findall(r'\d+', content)
                    selected_indices = [int(n) for n in numbers[:5]]
                    reason = "AI가 도서 정보 분석을 통해 관심 기술과 가장 연관성 높은 도서들을 선정했습니다."
                    
            except json.JSONDecodeError:
                numbers = re.findall(r'\d+', content)
                selected_indices = [int(n) for n in numbers[:5]]
                reason = "AI가 도서 정보 분석을 통해 관심 기술과 가장 연관성 높은 도서들을 선정했습니다."
            
            # 선정된 책들 반환
            recommended_books = []
            for idx in selected_indices:
                book_idx = idx - 1
                if 0 <= book_idx < len(books):
                    recommended_books.append(books[book_idx])
            
            # 5개 미만이면 앞에서부터 채우기
            if len(recommended_books) < 5:
                for book in books[:5]:
                    if book not in recommended_books:
                        recommended_books.append(book)
                        if len(recommended_books) >= 5:
                            break
            
            return {
                'books': recommended_books[:5],
                'reason': reason
            }
            
        except Exception as e:
            print(f"AI 추천 실패: {e}")
            return {
                'books': books[:5],
                'reason': f"시스템 오류로 인해 상위 5개 도서를 기본 추천합니다."
            }

# 전역 크롤러 인스턴스
crawler = SejongLibraryCrawler()

@app.post("/api/v1/sejong-book-recommendations", response_model=SejongBookRecommendationResponse)
async def get_sejong_book_recommendations(request: SejongBookRecommendationRequest):
    """세종대 학술정보원에서 도서 추천 - direct_test.py 로직 기반"""
    try:
        print("=== 세종대 도서 추천 API 시작 ===")
        
        # 1단계: 키워드 생성
        print("1단계: 검색 키워드 생성 중...")
        keywords = await crawler.generate_search_keywords(request.lecture_title)
        print(f"생성된 키워드: {keywords}")
        
        # 2단계: 키워드별로 도서 검색 (최대 50개)
        print("2단계: 세종대 학술정보원 도서 크롤링 중...")
        all_books = []
        
        for i, keyword in enumerate(keywords[:10], 1):
            print(f"키워드 {i}/10: '{keyword}' 검색 중...")
            books = await crawler.search_books_by_keyword(keyword, limit=5)
            all_books.extend(books)
            print(f"키워드 '{keyword}': {len(books)}개 수집")
            
            # 충분한 책이 모이면 중단
            if len(all_books) >= 30:
                break
        
        # 중복 제거 (제목 기준)
        unique_books = []
        seen_titles = set()
        for book in all_books:
            title = book.get('title', '')
            if title and title not in seen_titles:
                unique_books.append(book)
                seen_titles.add(title)
        
        print(f"총 {len(unique_books)}개의 고유 도서 수집 완료")
        
        if not unique_books:
            raise HTTPException(status_code=404, detail="검색된 도서가 없습니다.")
        
        # 3단계: AI 추천 (5개 선정)
        print("3단계: AI 도서 추천 분석 중...")
        recommendation_result = await crawler.get_ai_book_recommendations(
            unique_books,
            request.interest_technology,
            request.learning_difficulty
        )
        
        # 응답 데이터 구성
        recommended_books = []
        for book in recommendation_result['books']:
            recommended_books.append(SejongBookInfo(**book))
        
        print(f"✅ 최종 추천 도서 {len(recommended_books)}권 완료")
        
        return SejongBookRecommendationResponse(
            recommended_books=recommended_books,
            search_keywords=keywords,
            total_books_analyzed=len(unique_books),
            recommendation_reason=recommendation_result['reason']
        )
        
    except Exception as e:
        print(f"❌ API 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Sejong Library Book Recommendation API v2.0", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running perfectly!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 