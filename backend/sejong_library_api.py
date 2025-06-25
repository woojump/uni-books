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

# 환경변수 로드
load_dotenv()

app = FastAPI(title="Sejong Library Book Recommendation API", version="1.0.0")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

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
    location: Optional[str] = None  # 소장위치
    availability: Optional[str] = None  # 도서상태 (대출가능/대출불가능)
    call_number: Optional[str] = None  # 청구기호
    subject_category: Optional[str] = None  # 주제분류
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
        
        # 세종대 학술정보원 주제 카테고리
        self.subject_categories = {
            "000": "총류",
            "100": "철학",
            "101": "철학일반",
            "110": "형이상학",
            "120": "인식론/방법론",
            "130": "철학의 체계",
            "140": "철학유파/철학사상",
            "150": "아시아철학/동양철학",
            "160": "서양철학",
            "170": "윤리학/도덕철학",
            "180": "고대철학",
            "190": "현대철학",
            "200": "종교",
            "300": "사회과학",
            "310": "통계학",
            "320": "정치학",
            "330": "경제학",
            "340": "법학",
            "350": "행정학",
            "360": "사회학/사회문제",
            "370": "교육학",
            "380": "풍습/예절",
            "390": "국방/군사학",
            "400": "언어학",
            "500": "순수과학",
            "510": "수학",
            "520": "물리학",
            "530": "화학",
            "540": "지구과학",
            "550": "생물과학",
            "560": "의학",
            "570": "농업",
            "580": "공학/기술과학",
            "590": "가정학/생활과학",
            "600": "응용과학",
            "700": "예술",
            "800": "언어",
            "900": "문학",
            "910": "한국문학",
            "920": "중국문학",
            "930": "일본문학",
            "940": "영미문학",
            "950": "독일문학",
            "960": "프랑스문학",
            "970": "스페인문학",
            "980": "이탈리아문학",
            "990": "기타문학"
        }
    
    async def generate_search_keywords(self, lecture_title: str) -> List[str]:
        """
        OpenAI API를 사용해서 강의 제목으로부터 검색 키워드 10개를 생성합니다.
        """
        try:
            prompt = f"""
            강의 제목: "{lecture_title}"
            
            이 강의와 관련성이 높은 도서 검색 키워드 10개를 생성해주세요.
            키워드는 구체적이고 실용적이어야 하며, 이 강의를 듣는 학생들이 읽으면 도움이 될 만한 책들을 찾을 수 있는 키워드여야 합니다.
            대학 도서관에서 검색할 만한 학술적인 키워드로 생성해주세요.
            
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
            
            # 응답에서 키워드 추출
            lines = content.strip().split('\n')
            for line in lines:
                if re.match(r'^\d+\.', line.strip()):
                    keyword = re.sub(r'^\d+\.\s*', '', line.strip())
                    if keyword:
                        keywords.append(keyword)
            
            return keywords[:10]
            
        except Exception as e:
            print(f"키워드 생성 실패: {e}")
            # 실패 시 기본 키워드 반환
            return [lecture_title, "입문", "기초", "이론", "실습", "개론", "개념", "방법론", "응용", "기본"]
    
    async def search_books_by_keyword(self, keyword: str, limit: int = 5) -> List[Dict]:
        """
        세종대 학술정보원에서 키워드로 도서를 검색합니다.
        """
        try:
            print(f"'{keyword}' 키워드로 세종대 학술정보원 검색 중...")
            
            # 검색 URL 구성
            search_url = f"{self.base_url}/search/Search.Result.ax"
            params = {
                'sid': '1',
                'q': keyword,
                'qt': '',
                'facet': 'Y',
                'gr': '1+2+3+4+5+6+7+8+9+10+12+13+20+',
                'pageSize': str(limit * 2)  # 여유분 확보
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            # 검색 결과에서 도서 정보 추출
            book_items = soup.find_all('li', class_='item-li')
            
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
        """
        검색 결과에서 기본 책 정보를 추출합니다.
        """
        book_info = {}
        
        try:
            # 제목과 상세 링크 추출
            title_elem = item.find('a', href=lambda x: x and 'DetailView.ax' in x)
            if title_elem:
                title = title_elem.get_text(strip=True)
                book_info['title'] = title
                
                # 상세 페이지 URL
                detail_url = title_elem.get('href')
                if detail_url and not detail_url.startswith('http'):
                    detail_url = self.base_url + detail_url
                book_info['detail_url'] = detail_url
            
            # 저자 정보 추출
            author_elem = item.find('span', class_='author')
            if author_elem:
                author = author_elem.get_text(strip=True)
                # 불필요한 텍스트 제거
                author = re.sub(r'\[.*?\]|\(.*?\)|지은이|저자|편저|역자', '', author).strip()
                if author:
                    book_info['author'] = author
            
            # 출판 정보 추출
            pub_info = item.find('span', class_='pub-info')
            if pub_info:
                pub_text = pub_info.get_text(strip=True)
                # 출판사와 출간년도 분리
                parts = pub_text.split(',')
                if len(parts) >= 2:
                    book_info['publisher'] = parts[0].strip()
                    year_match = re.search(r'\d{4}', parts[1])
                    if year_match:
                        book_info['publication_year'] = year_match.group()
            
            # 상세 정보 크롤링
            if book_info.get('detail_url'):
                detail_info = await self.crawl_book_detail(book_info['detail_url'])
                book_info.update(detail_info)
            
            return book_info
            
        except Exception as e:
            print(f"책 정보 추출 중 오류: {e}")
            return {}
    
    async def crawl_book_detail(self, detail_url: str) -> Dict:
        """
        개별 책의 상세 페이지에서 추가 정보를 크롤링합니다.
        """
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            detail_info = {}
            
            # ISBN 추출
            isbn_elem = soup.find('td', string=re.compile('ISBN'))
            if isbn_elem and isbn_elem.find_next_sibling('td'):
                isbn = isbn_elem.find_next_sibling('td').get_text(strip=True)
                detail_info['isbn'] = isbn
            
            # 청구기호 추출
            call_num_elem = soup.find('td', string=re.compile('청구기호'))
            if call_num_elem and call_num_elem.find_next_sibling('td'):
                call_number = call_num_elem.find_next_sibling('td').get_text(strip=True)
                detail_info['call_number'] = call_number
            
            # 주제분류 추출
            subject_elem = soup.find('td', string=re.compile('주제분류'))
            if subject_elem and subject_elem.find_next_sibling('td'):
                subject = subject_elem.find_next_sibling('td').get_text(strip=True)
                detail_info['subject_category'] = subject
            
            # 소장 정보 추출 (소장위치, 도서상태)
            holdings_table = soup.find('table', class_='table-holdings')
            if holdings_table:
                rows = holdings_table.find_all('tr')[1:]  # 헤더 제외
                if rows:
                    first_row = rows[0]
                    cells = first_row.find_all('td')
                    if len(cells) >= 3:
                        # 소장위치
                        location = cells[1].get_text(strip=True)
                        detail_info['location'] = location
                        
                        # 도서상태
                        availability = cells[2].get_text(strip=True)
                        detail_info['availability'] = availability
            
            # 목차나 책 설명 추출 시도
            content_div = soup.find('div', class_='book-content')
            if content_div:
                description = content_div.get_text(strip=True)[:500]
                detail_info['description'] = description
            
            await asyncio.sleep(0.5)  # 요청 간격 조절
            return detail_info
            
        except Exception as e:
            print(f"상세 정보 크롤링 실패 {detail_url}: {e}")
            return {}
    
    async def get_ai_book_recommendations(self, books: List[Dict], interest_technology: str, learning_difficulty: str) -> Dict:
        """
        OpenAI API를 사용해서 50개 책 정보와 관심기술의 유사도 분석으로 최적의 5개를 선정합니다.
        """
        try:
            # 50개 책 정보를 OpenAI에 전달
            books_data = []
            for i, book in enumerate(books[:50], 1):
                book_info = {
                    "번호": i,
                    "제목": book.get('title', 'N/A'),
                    "저자": book.get('author', 'N/A'),
                    "출판사": book.get('publisher', 'N/A'),
                    "소장위치": book.get('location', 'N/A'),
                    "도서상태": book.get('availability', 'N/A'),
                    "주제분류": book.get('subject_category', 'N/A'),
                    "설명": book.get('description', '')
                }
                books_data.append(book_info)
            
            books_json = json.dumps(books_data, ensure_ascii=False, indent=2)
            
            prompt = f"""
다음은 50개의 세종대학교 학술정보원 소장 도서 정보입니다:

{books_json}

사용자 정보:
- 관심 기술: {interest_technology}
- 학습 난이도: {learning_difficulty}

위 50개 도서 중에서 사용자의 관심 기술 "{interest_technology}"와 가장 관련성이 높고, 
학습 난이도 "{learning_difficulty}"에 적합한 5개의 책을 선정해주세요.

분석 기준:
1. 책 제목과 관심 기술의 연관성
2. 학습 난이도와의 적합성
3. 주제분류의 관련성
4. 실제 대출 가능 여부 (도서상태)

응답은 반드시 다음 JSON 형식으로 해주세요:
{{
  "selected_books": [1, 15, 23, 35, 42],
  "analysis_reason": "상세한 선정 이유와 각 책이 관심 기술과 어떻게 연관되는지 설명"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": "당신은 대학 도서관 전문 사서이자 도서 추천 분석가입니다."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            print(f"AI 분석 응답: {content}")
            
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

@app.post("/recommend-sejong-books", response_model=SejongBookRecommendationResponse)
async def recommend_sejong_books(request: SejongBookRecommendationRequest):
    """
    강의 제목을 바탕으로 세종대 학술정보원에서 도서를 추천하는 API
    """
    try:
        # 1단계: OpenAI API로 검색 키워드 생성
        print("1단계: 검색 키워드 생성 중...")
        keywords = await crawler.generate_search_keywords(request.lecture_title)
        print(f"생성된 키워드: {keywords}")
        
        # 2단계: 10개 키워드로 각각 5개씩 총 50개 책 크롤링
        print("2단계: 세종대 학술정보원 도서 크롤링 중...")
        all_books = []
        
        for i, keyword in enumerate(keywords[:10], 1):
            print(f"키워드 {i}/10: '{keyword}' 검색 중...")
            books = await crawler.search_books_by_keyword(keyword, limit=5)
            all_books.extend(books)
            print(f"키워드 '{keyword}': {len(books)}개 수집")
        
        # 중복 제거 (제목 기준)
        unique_books = []
        seen_titles = set()
        for book in all_books:
            title = book.get('title', '')
            if title and title not in seen_titles:
                unique_books.append(book)
                seen_titles.add(title)
        
        # 50개가 되도록 조정
        if len(unique_books) > 50:
            unique_books = unique_books[:50]
        
        print(f"총 {len(unique_books)}개의 고유 도서 수집 완료")
        
        if not unique_books:
            raise HTTPException(status_code=404, detail="검색된 도서가 없습니다.")
        
        # 3단계: AI 추천
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
        
        return SejongBookRecommendationResponse(
            recommended_books=recommended_books,
            search_keywords=keywords,
            total_books_analyzed=len(unique_books),
            recommendation_reason=recommendation_result['reason']
        )
        
    except Exception as e:
        print(f"API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

@app.get("/")
async def root():
    return {"message": "Sejong Library Book Recommendation API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # 다른 포트 사용 