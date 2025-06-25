import asyncio
from sejong_library_api import SejongBookRecommendationRequest, crawler

async def test_sejong_api_direct():
    """세종대 API를 직접 테스트"""
    try:
        print("=== 세종대 API 직접 테스트 ===")
        
        # 요청 데이터 생성
        request = SejongBookRecommendationRequest(
            lecture_title="컴퓨터 프로그래밍",
            major_field="컴퓨터공학",
            interest_technology="파이썬",
            learning_difficulty="초급"
        )
        
        print("1단계: 키워드 생성 테스트...")
        keywords = await crawler.generate_search_keywords(request.lecture_title)
        print(f"생성된 키워드: {keywords}")
        
        print("\n2단계: 첫 번째 키워드로 검색 테스트...")
        if keywords:
            books = await crawler.search_books_by_keyword(keywords[0], limit=3)
            print(f"검색 결과: {len(books)}권")
            
            for i, book in enumerate(books, 1):
                print(f"\n{i}. {book.get('title', 'N/A')}")
                print(f"   저자: {book.get('author', 'N/A')}")
                print(f"   출판사: {book.get('publisher', 'N/A')}")
                print(f"   소장위치: {book.get('location', 'N/A')}")
                print(f"   도서상태: {book.get('availability', 'N/A')}")
                print(f"   청구기호: {book.get('call_number', 'N/A')}")
            
            if books:
                print("\n3단계: AI 추천 테스트...")
                try:
                    recommendation_result = await crawler.get_ai_book_recommendations(
                        books,
                        request.interest_technology,
                        request.learning_difficulty
                    )
                    print(f"AI 추천 완료: {len(recommendation_result['books'])}권")
                    print(f"추천 이유: {recommendation_result['reason'][:100]}...")
                except Exception as e:
                    print(f"AI 추천 오류: {e}")
        
        print("\n✅ 세종대 API 테스트 완료")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sejong_api_direct()) 