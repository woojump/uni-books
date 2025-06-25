from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import httpx
import json
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="UniBooks Backend", version="1.0.0")

# CORS 설정 (Flutter 앱에서 API 호출 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI API 설정
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 세종대 학술정보원 크롤러 import
from sejong_library_api import (
    SejongBookRecommendationRequest,
    SejongBookRecommendationResponse, 
    SejongBookInfo,
    crawler as sejong_crawler
)

# 알라딘 크롤러 import
from book_recommendation_api import (
    BookRecommendationRequest as AladinRequest,
    BookRecommendationResponse as AladinResponse,
    BookInfo as AladinBookInfo,
    crawler as aladin_crawler
)

# Pydantic 모델 정의
class BookRecommendationRequest(BaseModel):
    lecture_title: str
    major_field: str
    interest_technology: str
    learning_difficulty: str

class BookRecommendation(BaseModel):
    title: str
    author: str
    description: str
    difficulty: str
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    publicationYear: Optional[str] = None
    rating: Optional[float] = None
    imageUrl: Optional[str] = None

class BookRecommendationResponse(BaseModel):
    books: List[BookRecommendation]
    status: str
    message: Optional[str] = None

# 유틸리티 함수
def create_prompt(lecture_title: str, major_field: str, interest_technology: str, learning_difficulty: str) -> str:
    return f"""
강의 제목: {lecture_title}
전공 분야: {major_field}
관심 기술: {interest_technology}
학습 난이도: {learning_difficulty}

위의 정보를 바탕으로 적합한 책 5권을 추천해주세요. 
각 책은 강의 내용과 전공 분야, 관심 기술에 맞고, 요청한 학습 난이도에 적합해야 합니다.
실제 존재하는 책들로만 추천해주시고, 한국어 번역서가 있다면 우선적으로 추천해주세요.
"""

# API 엔드포인트
@app.get("/")
async def root():
    return {"message": "UniBooks Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/test-api-key")
async def test_api_key():
    """OpenAI API 키 유효성 테스트"""
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="API 키가 설정되지 않았습니다.")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "max_tokens": 5,
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return {"valid": True, "message": "API 키가 유효합니다."}
            else:
                return {"valid": False, "message": f"API 키 테스트 실패: {response.status_code}"}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API 키 테스트 중 오류: {str(e)}")

@app.post("/api/v1/book-recommendations", response_model=BookRecommendationResponse)
async def get_book_recommendations(request: BookRecommendationRequest):
    """사용자 정보를 바탕으로 도서 추천"""
    
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="OpenAI API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    try:
        # 프롬프트 생성
        prompt = create_prompt(request.lecture_title, request.major_field, request.interest_technology, request.learning_difficulty)
        
        # OpenAI API 호출
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENAI_API_URL,
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": """당신은 대학생을 위한 전문 도서 추천 시스템입니다. 
                            사용자의 전공, 관심 기술, 학습 난이도에 맞는 책들을 추천해주세요.
                            응답은 반드시 JSON 배열 형태로만 제공하고, 다른 텍스트는 포함하지 마세요.
                            각 책 정보는 다음 형식을 따라주세요:
                            [
                              {
                                "title": "책 제목",
                                "author": "저자",
                                "description": "책 설명 (200자 이내)",
                                "difficulty": "초급/중급/고급",
                                "isbn": "ISBN (있는 경우)",
                                "publisher": "출판사",
                                "publicationYear": "출간년도",
                                "rating": 4.5,
                                "imageUrl": null
                              }
                            ]""",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7,
                },
                timeout=60.0
            )
            
            print(f"OpenAI API 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # JSON 파싱
                try:
                    books_data = json.loads(content)
                    books = [BookRecommendation(**book) for book in books_data]
                    
                    return BookRecommendationResponse(
                        books=books,
                        status="success",
                        message="도서 추천이 성공적으로 완료되었습니다."
                    )
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=500, 
                        detail=f"OpenAI 응답 파싱 오류: {str(e)}"
                    )
            else:
                error_data = response.json()
                error_message = f"API 요청 실패: {response.status_code}"
                
                if "error" in error_data:
                    error_message += f" - {error_data['error'].get('message', '알 수 없는 오류')}"
                
                raise HTTPException(status_code=response.status_code, detail=error_message)
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="API 요청 시간 초과")
    except Exception as e:
        print(f"오류 발생: {e}")
        raise HTTPException(status_code=500, detail=f"책 추천 요청 중 오류 발생: {str(e)}")

@app.get("/api/v1/mock-recommendations")
async def get_mock_recommendations():
    """테스트용 Mock 데이터 제공"""
    mock_books = [
        {
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "description": "소프트웨어 개발자를 위한 클린 코드 작성법을 다루는 필독서입니다.",
            "difficulty": "중급",
            "publisher": "인사이트",
            "publicationYear": "2013",
            "rating": 4.8,
        },
        {
            "title": "Flutter 완벽 가이드",
            "author": "김태헌",
            "description": "Flutter 프레임워크를 활용한 모바일 앱 개발의 모든 것을 다룹니다.",
            "difficulty": "중급",
            "publisher": "한빛미디어",
            "publicationYear": "2023",
            "rating": 4.5,
        },
        {
            "title": "자료구조와 알고리즘",
            "author": "홍정모",
            "description": "프로그래밍의 기초가 되는 자료구조와 알고리즘을 쉽게 설명합니다.",
            "difficulty": "초급",
            "publisher": "생능출판",
            "publicationYear": "2022",
            "rating": 4.3,
        },
    ]
    
    books = [BookRecommendation(**book) for book in mock_books]
    
    return BookRecommendationResponse(
        books=books,
        status="success",
        message="Mock 데이터가 성공적으로 반환되었습니다."
    )

@app.post("/api/v1/sejong-book-recommendations", response_model=SejongBookRecommendationResponse)
async def get_sejong_book_recommendations(request: SejongBookRecommendationRequest):
    """세종대 학술정보원에서 도서 추천 - 새로운 단순화된 로직"""
    try:
        print("=== main.py에서 세종대 도서 추천 API 시작 ===")
        
        # 1단계: 키워드 생성
        print("1단계: 검색 키워드 생성 중...")
        keywords = await sejong_crawler.generate_search_keywords(request.lecture_title)
        print(f"생성된 키워드: {keywords}")
        
        # 2단계: 키워드별로 도서 검색 (효율적으로 30개 정도까지)
        print("2단계: 세종대 학술정보원 도서 크롤링 중...")
        all_books = []
        
        for i, keyword in enumerate(keywords[:10], 1):
            print(f"키워드 {i}/10: '{keyword}' 검색 중...")
            books = await sejong_crawler.search_books_by_keyword(keyword, limit=5)
            all_books.extend(books)
            print(f"키워드 '{keyword}': {len(books)}개 수집")
            
            # 충분한 책이 모이면 중단 (효율성 개선)
            if len(all_books) >= 30:
                print(f"충분한 도서 수집 완료 ({len(all_books)}개), 검색 중단")
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
        recommendation_result = await sejong_crawler.get_ai_book_recommendations(
            unique_books,
            request.interest_technology,
            request.learning_difficulty
        )
        
        # 응답 데이터 구성 (단순화된 방식)
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
        print(f"❌ 세종대 도서 추천 API 오류: {e}")
        print(f"오류 타입: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"세종대 도서 추천 중 오류 발생: {str(e)}")

@app.post("/recommend-books", response_model=AladinResponse)
async def recommend_books(request: AladinRequest):
    """
    알라딘 크롤링 기반 도서 추천 API
    """
    try:
        # 1단계: OpenAI API로 검색 키워드 생성
        print("1단계: 검색 키워드 생성 중...")
        keywords = await aladin_crawler.generate_search_keywords(request.lecture_title)
        print(f"생성된 키워드: {keywords}")
        
        # 2단계: 10개 키워드로 각각 5개씩 총 50개 책 크롤링
        print("2단계: 도서 크롤링 중...")
        all_books = []
        
        for i, keyword in enumerate(keywords[:10], 1):  # 정확히 10개 키워드만
            print(f"키워드 {i}/10: '{keyword}' 검색 중...")
            books = await aladin_crawler.crawl_books_by_keyword(
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
        recommendation_result = await aladin_crawler.get_ai_book_recommendations(
            unique_books, 
            request.interest_technology, 
            request.learning_difficulty
        )
        
        # 응답 데이터 구성
        recommended_books = []
        for book in recommendation_result['books']:
            recommended_books.append(AladinBookInfo(**book))
        
        return AladinResponse(
            recommended_books=recommended_books,
            search_keywords=keywords,
            total_books_analyzed=len(unique_books),
            recommendation_reason=recommendation_result['reason']
        )
        
    except Exception as e:
        print(f"알라딘 API 오류: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 