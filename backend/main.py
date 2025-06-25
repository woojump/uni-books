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
                    "model": "gpt-3.5-turbo",
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
                    "model": "gpt-3.5-turbo",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 