# 📚 Book Recommendation API

강의 제목을 기반으로 AI가 맞춤형 도서를 추천해주는 API입니다.

## 🚀 주요 기능

### 1단계: AI 키워드 생성
- OpenAI GPT-3.5를 사용해서 강의 제목으로부터 **관련 검색 키워드 10개**를 자동 생성

### 2단계: 대규모 도서 크롤링
- 생성된 키워드들로 **알라딘 도서 사이트**에서 각각 20개씩 크롤링
- **세부 페이지**에 접근해서 **목차, 설명, 출간일** 등 상세 정보 수집
- 전공분야 키워드로 **관련성 필터링**
- 최대 **200개 도서** 수집 및 중복 제거

### 3단계: AI 도서 추천
- 수집된 모든 도서 정보와 사용자의 **관심 기술**, **학습 난이도**를 AI에게 전달
- OpenAI가 **목차 내용 분석** 및 **유사도 계산**을 통해 **최적의 5개 도서** 선정

## 📋 API 명세

### 요청 (POST /recommend-books)

```json
{
  "lecture_title": "머신러닝과 딥러닝 기초",
  "major_field": "컴퓨터과학, 인공지능, 데이터사이언스",
  "interest_technology": "파이썬, 텐서플로우, 신경망, 자연어처리",
  "learning_difficulty": "초급자"
}
```

### 응답

```json
{
  "recommended_books": [
    {
      "title": "책 제목",
      "author": "저자명",
      "publisher": "출판사",
      "price": "가격",
      "image_url": "이미지 URL",
      "product_url": "구매 링크",
      "description": "책 설명",
      "table_of_contents": "목차 내용",
      "publication_date": "출간일"
    }
  ],
  "search_keywords": ["키워드1", "키워드2", ...],
  "total_books_analyzed": 150,
  "recommendation_reason": "AI 추천 이유"
}
```

## 🔧 설치 및 실행

### 1. 환경 설정
```bash
# 가상환경 활성화
source venv/bin/activate

# 패키지 설치 (이미 완료됨)
pip install -r requirements.txt
```

### 2. OpenAI API 키 설정
```bash
# 환경변수로 설정
export OPENAI_API_KEY="your-openai-api-key-here"

# 또는 .env 파일 생성
echo "OPENAI_API_KEY=your-openai-api-key-here" > .env
```

### 3. API 서버 실행
```bash
# 서버 시작
python book_recommendation_api.py

# 또는 uvicorn으로 실행
uvicorn book_recommendation_api:app --host 0.0.0.0 --port 8000 --reload
```

### 4. API 테스트
```bash
# 테스트 스크립트 실행
python test_api.py
```

## 🌐 API 엔드포인트

- **POST /recommend-books** - 도서 추천 메인 API
- **GET /** - API 정보 확인
- **GET /health** - 서버 상태 확인
- **GET /docs** - Swagger UI (http://localhost:8000/docs)

## 🎯 사용 예시

### cURL로 테스트
```bash
curl -X POST "http://localhost:8000/recommend-books" \
     -H "Content-Type: application/json" \
     -d '{
       "lecture_title": "웹 개발 입문",
       "major_field": "컴퓨터공학",
       "interest_technology": "React, Node.js, JavaScript",
       "learning_difficulty": "초급자"
     }'
```

### Python으로 테스트
```python
import requests

response = requests.post(
    "http://localhost:8000/recommend-books",
    json={
        "lecture_title": "데이터베이스 시스템",
        "major_field": "컴퓨터과학",
        "interest_technology": "SQL, MySQL, 데이터 모델링",
        "learning_difficulty": "중급자"
    }
)

result = response.json()
print(f"추천 도서 수: {len(result['recommended_books'])}")
```

## 🔍 기술 스택

- **FastAPI** - 고성능 비동기 웹 프레임워크
- **OpenAI GPT-3.5** - 키워드 생성 및 도서 추천 AI
- **BeautifulSoup** - 웹 크롤링
- **Pydantic** - 데이터 검증 및 직렬화
- **asyncio** - 비동기 처리

## ⚡ 성능 특징

- **비동기 처리** - 동시에 여러 페이지 크롤링
- **지능형 필터링** - 전공분야 관련성 자동 판단
- **중복 제거** - 동일 도서 자동 필터링
- **상세 분석** - 목차 내용까지 고려한 정밀 추천
- **확장 가능** - 키워드 개수, 크롤링 수량 조절 가능

## 🚨 주의사항

- OpenAI API 키가 필요합니다
- 크롤링 과정에서 시간이 다소 소요될 수 있습니다 (2-5분)
- 알라딘 서버 상태에 따라 일부 도서 정보가 누락될 수 있습니다
- API 호출 시 충분한 타임아웃 설정이 필요합니다

## 📞 문의

API 사용 중 문제가 발생하면 로그를 확인하거나 이슈를 제보해주세요. 