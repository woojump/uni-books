import requests
import json
import asyncio

# 테스트용 요청 데이터
test_request = {
    "lecture_title": "컴퓨터 프로그래밍",
    "major_field": "컴퓨터공학",
    "interest_technology": "파이썬",
    "learning_difficulty": "초급"
}

async def test_sejong_api():
    """세종대 학술정보원 API 테스트"""
    try:
        print("=== 세종대 학술정보원 도서 추천 API 테스트 ===")
        print(f"요청 데이터: {json.dumps(test_request, ensure_ascii=False, indent=2)}")
        
        # API 요청
        response = requests.post(
            "http://localhost:8000/api/v1/sejong-book-recommendations",
            json=test_request,
            timeout=120  # 2분 타임아웃
        )
        
        print(f"\n응답 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n=== 추천 결과 ===")
            print(f"검색 키워드: {result['search_keywords']}")
            print(f"분석된 총 도서 수: {result['total_books_analyzed']}")
            print(f"추천 이유: {result['recommendation_reason']}")
            
            print(f"\n=== 추천 도서 {len(result['recommended_books'])}권 ===")
            for i, book in enumerate(result['recommended_books'], 1):
                print(f"\n{i}. {book['title']}")
                print(f"   저자: {book.get('author', 'N/A')}")
                print(f"   출판사: {book.get('publisher', 'N/A')}")
                print(f"   출간년도: {book.get('publication_year', 'N/A')}")
                print(f"   소장위치: {book.get('location', 'N/A')}")
                print(f"   도서상태: {book.get('availability', 'N/A')}")
                print(f"   주제분류: {book.get('subject_category', 'N/A')}")
                print(f"   청구기호: {book.get('call_number', 'N/A')}")
                if book.get('description'):
                    print(f"   설명: {book['description'][:100]}...")
                if book.get('detail_url'):
                    print(f"   상세 URL: {book['detail_url']}")
            
        else:
            print(f"API 요청 실패: {response.text}")
            try:
                error_data = response.json()
                print(f"오류 상세: {json.dumps(error_data, ensure_ascii=False, indent=2)}")
            except:
                print(f"응답 텍스트: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        print("API 요청 시간 초과 (2분)")
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")

def test_direct_crawler():
    """크롤러 직접 테스트"""
    from sejong_library_api import SejongLibraryCrawler
    
    async def run_test():
        crawler = SejongLibraryCrawler()
        
        print("=== 키워드 생성 테스트 ===")
        keywords = await crawler.generate_search_keywords("컴퓨터 프로그래밍")
        print(f"생성된 키워드: {keywords}")
        
        print("\n=== 첫 번째 키워드로 검색 테스트 ===")
        if keywords:
            books = await crawler.search_books_by_keyword(keywords[0], limit=3)
            print(f"'{keywords[0]}' 검색 결과: {len(books)}권")
            
            for i, book in enumerate(books, 1):
                print(f"\n{i}. {book.get('title', 'N/A')}")
                print(f"   저자: {book.get('author', 'N/A')}")
                print(f"   출판사: {book.get('publisher', 'N/A')}")
                print(f"   소장위치: {book.get('location', 'N/A')}")
                print(f"   도서상태: {book.get('availability', 'N/A')}")
    
    # 비동기 함수 실행
    asyncio.run(run_test())

if __name__ == "__main__":
    print("1. 전체 API 테스트")
    print("2. 크롤러 직접 테스트")
    choice = input("선택하세요 (1 또는 2): ")
    
    if choice == "1":
        asyncio.run(test_sejong_api())
    elif choice == "2":
        test_direct_crawler()
    else:
        print("잘못된 선택입니다.") 