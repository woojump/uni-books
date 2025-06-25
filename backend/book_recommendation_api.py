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

# 환경변수 로드
load_dotenv()

app = FastAPI(title="Book Recommendation API", version="1.0.0")

# OpenAI 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"))

class BookRecommendationRequest(BaseModel):
    lecture_title: str
    major_field: str
    interest_technology: str
    learning_difficulty: str

class BookInfo(BaseModel):
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    product_url: Optional[str] = None
    description: Optional[str] = None
    table_of_contents: Optional[str] = None
    publication_date: Optional[str] = None

class BookRecommendationResponse(BaseModel):
    recommended_books: List[BookInfo]
    search_keywords: List[str]
    total_books_analyzed: int
    recommendation_reason: str

class AdvancedBookCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
    
    async def generate_search_keywords(self, lecture_title: str) -> List[str]:
        """
        OpenAI API를 사용해서 강의 제목으로부터 검색 키워드 10개를 생성합니다.
        """
        try:
            prompt = f"""
            강의 제목: "{lecture_title}"
            
            이 강의와 관련성이 높은 도서 검색 키워드 10개를 생성해주세요.
            키워드는 구체적이고 실용적이어야 하며, 이 강의를 듣는 학생들이 읽으면 도움이 될 만한 책들을 찾을 수 있는 키워드여야 합니다.
            
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
            return [lecture_title, "입문서", "기초", "이론", "실습", "가이드", "교재", "참고서", "개론", "핸드북"]
    
    async def crawl_book_detail(self, product_url: str) -> Dict[str, str]:
        """
        개별 책의 상세 페이지에서 목차와 상세 정보를 크롤링합니다.
        """
        try:
            response = self.session.get(product_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            detail_info = {}
            
            # 책 설명 추출
            desc_elem = soup.find('div', class_='Ere_prod_mconts_R')
            if desc_elem:
                detail_info['description'] = desc_elem.get_text(strip=True)[:500]
            
            # 목차 추출 - 여러 선택자 시도
            toc_selectors = [
                'div.Ere_prod_mconts_LS',  # 알라딘 목차 영역
                'div#div_PublisherDesc',   # 출판사 서평
                'div.Ere_prod_mconts_R',   # 상세 설명
                'div.book_info_inner'      # 도서 정보
            ]
            
            toc_text = ""
            for selector in toc_selectors:
                toc_elem = soup.select_one(selector)
                if toc_elem:
                    text = toc_elem.get_text(strip=True)
                    if '목차' in text or '차례' in text or len(text) > 100:
                        toc_text = text[:1000]  # 목차는 1000자로 제한
                        break
            
            detail_info['table_of_contents'] = toc_text
            
            # 출간일 추출
            date_elem = soup.find('li', class_='Ere_sub2_title')
            if date_elem:
                date_text = date_elem.get_text()
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_text)
                if date_match:
                    detail_info['publication_date'] = date_match.group(1)
            
            await asyncio.sleep(0.5)  # 요청 간격 조절
            return detail_info
            
        except Exception as e:
            print(f"상세 정보 크롤링 실패 {product_url}: {e}")
            return {}
    
    async def crawl_books_by_keyword(self, keyword: str, major_field: str, limit: int = 20) -> List[Dict]:
        """
        특정 키워드로 알라딘에서 책을 크롤링합니다.
        """
        try:
            print(f"'{keyword}' 키워드로 검색 중...")
            
            # 알라딘 검색 URL
            search_url = "https://www.aladin.co.kr/search/wsearchresult.aspx"
            params = {
                'SearchTarget': 'Book',
                'SearchWord': keyword,
                'x': '0',
                'y': '0'
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            books = []
            
            # 도서 목록 추출
            book_items = soup.find_all('div', class_='ss_book_box')
            
            for i, item in enumerate(book_items[:limit]):
                try:
                    book_info = await self.extract_book_info_with_details(item, major_field)
                    if book_info and book_info.get('title'):
                        books.append(book_info)
                        print(f"크롤링 완료: {len(books)}/{limit} - {book_info['title']}")
                    
                    if len(books) >= limit:
                        break
                        
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    print(f"책 정보 추출 실패: {e}")
                    continue
            
            return books
            
        except Exception as e:
            print(f"'{keyword}' 크롤링 실패: {e}")
            return []
    
    async def extract_book_info_with_details(self, item, major_field: str) -> Dict:
        """
        기본 책 정보를 추출하고 상세 페이지 정보도 가져옵니다.
        """
        book_info = {}
        
        try:
            # 제목 추출
            title_elem = item.find('a', class_='bo3')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                title_text = re.sub(r'\[.*?\]', '', title_text).strip()
                book_info['title'] = title_text
            
            # 전체 텍스트에서 정보 추출
            full_text = item.get_text()
            
            # 전공분야와 관련성 체크 (간단한 키워드 매칭)
            if major_field and not self.is_relevant_to_major(full_text, major_field):
                return None
            
            # 저자 추출
            author_patterns = [
                r'([가-힣a-zA-Z\s,]+)\s*\(지은이\)',
                r'([가-힣a-zA-Z\s,]+)\s*저',
                r'저자\s*:\s*([^|]+)',
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, full_text)
                if match:
                    author = match.group(1).strip()
                    author = re.sub(r'\(.*?\)', '', author).strip()
                    if author and len(author) < 50:
                        book_info['author'] = author
                        break
            
            # 출판사 추출
            publisher_patterns = [
                r'([가-힣a-zA-Z0-9\s]+)\s*\|\s*\d{4}',
                r'\|\s*([가-힣a-zA-Z0-9\s]+)\s*\|\s*\d{4}',
            ]
            
            for pattern in publisher_patterns:
                match = re.search(pattern, full_text)
                if match:
                    publisher = match.group(1).strip()
                    if publisher and len(publisher) < 30:
                        book_info['publisher'] = publisher
                        break
            
            # 가격 추출
            price_elem = item.find('span', class_='ss_p2')
            if price_elem:
                book_info['price'] = price_elem.get_text(strip=True)
            
            # 이미지 URL
            img_elem = item.find('img')
            if img_elem and img_elem.get('src'):
                img_url = img_elem.get('src')
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                book_info['image_url'] = img_url
            
            # 상품 링크
            link_elem = item.find('a', href=lambda x: x and 'ItemId=' in x)
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('/'):
                    product_url = 'https://www.aladin.co.kr' + href
                else:
                    product_url = href
                book_info['product_url'] = product_url
                
                # 상세 정보 크롤링
                detail_info = await self.crawl_book_detail(product_url)
                book_info.update(detail_info)
            
            return book_info
            
        except Exception as e:
            print(f"책 정보 추출 중 오류: {e}")
            return None
    
    def is_relevant_to_major(self, text: str, major_field: str) -> bool:
        """
        텍스트가 전공분야와 관련이 있는지 간단히 체크합니다.
        """
        if not major_field:
            return True
        
        # 전공분야 키워드를 공백으로 분리
        major_keywords = major_field.replace(',', ' ').split()
        
        # 텍스트에 전공분야 키워드가 하나라도 포함되면 관련성 있음
        for keyword in major_keywords:
            if keyword.strip().lower() in text.lower():
                return True
        
        return True  # 기본적으로 관련성 있다고 가정
    
    async def get_ai_book_recommendations(self, books: List[Dict], interest_technology: str, learning_difficulty: str) -> Dict:
        """
        OpenAI API를 사용해서 50개 책의 목차와 관심기술의 유사도 분석으로 최적의 5개를 선정합니다.
        """
        try:
            # 정확히 50개 책 정보를 OpenAI에 전달
            books_data = []
            for i, book in enumerate(books[:50], 1):  # 정확히 50개만
                book_info = {
                    "번호": i,
                    "제목": book.get('title', 'N/A'),
                    "저자": book.get('author', 'N/A'), 
                    "출판사": book.get('publisher', 'N/A'),
                    "목차": book.get('table_of_contents', ''),
                    "설명": book.get('description', '')
                }
                books_data.append(book_info)
            
            # JSON 형태로 책 정보 구성
            books_json = json.dumps(books_data, ensure_ascii=False, indent=2)
            
            prompt = f"""
다음은 50개의 도서 정보가 담긴 JSON 데이터입니다:

{books_json}

사용자 정보:
- 관심 기술: {interest_technology}
- 학습 난이도: {learning_difficulty}

위 50개 도서의 목차와 설명을 사용자의 관심 기술 "{interest_technology}"와 유사도 분석을 통해 비교하여, 
사용자에게 가장 적합한 5개의 책을 선정해주세요.

분석 기준:
1. 책의 목차 내용과 관심 기술의 유사도
2. 학습 난이도와의 적합성
3. 실무 적용 가능성
4. 학습 체계의 완성도

응답은 반드시 다음 JSON 형식으로 해주세요:
{{
  "selected_books": [1, 15, 23, 35, 42],
  "analysis_reason": "상세한 선정 이유와 각 책이 관심 기술과 어떻게 연관되는지 설명"
}}
"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo-16k",  # 16k 모델 사용으로 토큰 한계 확장
                messages=[
                    {"role": "system", "content": "당신은 전문 도서 추천 분석가입니다. 사용자의 관심 기술과 도서의 목차를 정밀하게 분석하여 최적의 추천을 제공하세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.2
            )
            
            content = response.choices[0].message.content
            print(f"AI 분석 응답: {content}")
            
            # JSON 응답 파싱
            try:
                # JSON 부분만 추출
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    ai_response = json.loads(json_str)
                    
                    selected_indices = ai_response.get('selected_books', [])
                    reason = ai_response.get('analysis_reason', '')
                else:
                    # JSON 파싱 실패 시 숫자만 추출
                    numbers = re.findall(r'\d+', content)
                    selected_indices = [int(n) for n in numbers[:5]]
                    reason = "AI가 목차 분석을 통해 관심 기술과 가장 연관성 높은 도서들을 선정했습니다."
                    
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 숫자만 추출
                numbers = re.findall(r'\d+', content)
                selected_indices = [int(n) for n in numbers[:5]]
                reason = "AI가 목차 분석을 통해 관심 기술과 가장 연관성 높은 도서들을 선정했습니다."
            
            # 선정된 책들 반환 (1-based index를 0-based로 변환)
            recommended_books = []
            for idx in selected_indices:
                book_idx = idx - 1  # 1-based를 0-based로 변환
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
            # 실패 시 첫 5개 책 반환
            return {
                'books': books[:5],
                'reason': f"시스템 오류로 인해 상위 5개 도서를 기본 추천합니다. 오류: {str(e)}"
            }

# 전역 크롤러 인스턴스
crawler = AdvancedBookCrawler()

@app.post("/recommend-books", response_model=BookRecommendationResponse)
async def recommend_books(request: BookRecommendationRequest):
    """
    강의 제목을 바탕으로 도서를 추천하는 API
    """
    try:
        # 1단계: OpenAI API로 검색 키워드 생성
        print("1단계: 검색 키워드 생성 중...")
        keywords = await crawler.generate_search_keywords(request.lecture_title)
        print(f"생성된 키워드: {keywords}")
        
        # 2단계: 10개 키워드로 각각 5개씩 총 50개 책 크롤링
        print("2단계: 도서 크롤링 중...")
        all_books = []
        
        for i, keyword in enumerate(keywords[:10], 1):  # 정확히 10개 키워드만
            print(f"키워드 {i}/10: '{keyword}' 검색 중...")
            books = await crawler.crawl_books_by_keyword(
                keyword, 
                request.major_field, 
                limit=5  # 각 키워드당 정확히 5개
            )
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
        
        # 정확히 50개가 되도록 조정
        if len(unique_books) > 50:
            unique_books = unique_books[:50]
        elif len(unique_books) < 50:
            print(f"경고: 중복 제거 후 {len(unique_books)}개만 수집됨 (목표: 50개)")
        
        print(f"총 {len(unique_books)}개의 고유 도서 수집 완료 (목표: 50개)")
        
        if not unique_books:
            raise HTTPException(status_code=404, detail="검색된 도서가 없습니다.")
        
        # 3단계: 50개 책 정보와 관심기술 유사도 분석으로 AI 추천
        print("3단계: 50개 도서 목차 분석 및 AI 추천 중...")
        recommendation_result = await crawler.get_ai_book_recommendations(
            unique_books, 
            request.interest_technology, 
            request.learning_difficulty
        )
        
        # 응답 데이터 구성
        recommended_books = []
        for book in recommendation_result['books']:
            recommended_books.append(BookInfo(**book))
        
        return BookRecommendationResponse(
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
    return {"message": "Book Recommendation API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 