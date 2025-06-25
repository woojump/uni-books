# UniBooks Backend

UniBooks Flutter 앱의 백엔드 API 서버입니다. FastAPI를 사용하여 구현되었습니다.

## 기능

- OpenAI GPT-3.5-turbo를 사용한 도서 추천
- API 키 유효성 검사
- Mock 데이터 제공
- CORS 지원 (Flutter 앱 연동)

## 설치 및 실행

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env.example`을 `.env`로 복사하고 OpenAI API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일을 편집하여 실제 OpenAI API 키를 입력하세요:

```
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 3. 서버 실행

```bash
# 개발 모드
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 또는 Python으로 직접 실행
python main.py
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- API 서버: http://localhost:8000
- API 문서: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 1. 기본 정보
- `GET /` - API 기본 정보
- `GET /health` - 헬스 체크

### 2. 도서 추천
- `POST /api/v1/book-recommendations` - 도서 추천 요청
- `GET /api/v1/mock-recommendations` - Mock 데이터 반환

### 3. 유틸리티
- `POST /api/v1/test-api-key` - OpenAI API 키 테스트

## 요청 예시

### 도서 추천 요청

```bash
curl -X POST "http://localhost:8000/api/v1/book-recommendations" \
     -H "Content-Type: application/json" \
     -d '{
       "major": "컴퓨터공학",
       "interests": "Flutter, 모바일 개발",
       "difficulty": "중급"
     }'
```

## 개발 환경

- Python 3.8+
- FastAPI
- Uvicorn
- OpenAI API 