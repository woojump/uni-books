import requests
import json
import asyncio

def test_book_recommendation_api():
    """
    도서 추천 API를 테스트하는 함수
    """
    # API 엔드포인트
    url = "http://localhost:8000/recommend-books"
    
    # 테스트 데이터
    test_data = {
        "lecture_title": "머신러닝과 딥러닝 기초",
        "major_field": "컴퓨터과학, 인공지능, 데이터사이언스",
        "interest_technology": "파이썬, 텐서플로우, 신경망, 자연어처리",
        "learning_difficulty": "초급자"
    }
    
    print("=== 도서 추천 API 테스트 ===")
    print(f"요청 데이터: {json.dumps(test_data, ensure_ascii=False, indent=2)}")
    print("\nAPI 호출 중...")
    
    try:
        # POST 요청 전송
        response = requests.post(
            url, 
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5분 타임아웃
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n✅ API 호출 성공!")
            print(f"📊 분석된 총 도서 수: {result['total_books_analyzed']}")
            print(f"🔍 검색 키워드: {', '.join(result['search_keywords'])}")
            print(f"💡 추천 이유: {result['recommendation_reason']}")
            
            print("\n📚 추천 도서 목록:")
            print("=" * 80)
            
            for i, book in enumerate(result['recommended_books'], 1):
                print(f"\n{i}. 📖 {book['title']}")
                print(f"   👨‍💼 저자: {book.get('author', 'N/A')}")
                print(f"   🏢 출판사: {book.get('publisher', 'N/A')}")
                print(f"   💰 가격: {book.get('price', 'N/A')}")
                if book.get('description'):
                    print(f"   📝 설명: {book['description'][:100]}...")
                if book.get('table_of_contents'):
                    print(f"   📋 목차: {book['table_of_contents'][:150]}...")
                if book.get('product_url'):
                    print(f"   🔗 링크: {book['product_url']}")
                print("-" * 80)
            
            # 결과를 파일로 저장
            with open('api_test_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("\n💾 결과가 'api_test_result.json'에 저장되었습니다.")
            
        else:
            print(f"❌ API 호출 실패: {response.status_code}")
            print(f"오류 메시지: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")

def test_health_check():
    """
    헬스 체크 API를 테스트하는 함수
    """
    try:
        response = requests.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("✅ 서버가 정상적으로 실행 중입니다.")
            return True
        else:
            print(f"❌ 서버 상태 확인 실패: {response.status_code}")
            return False
    except:
        print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        return False

if __name__ == "__main__":
    print("도서 추천 API 테스트를 시작합니다...\n")
    
    # 헬스 체크 먼저 수행
    if test_health_check():
        print("\n서버 연결 확인 완료. 본격적인 테스트를 시작합니다...\n")
        test_book_recommendation_api()
    else:
        print("\n서버를 먼저 실행해주세요:")
        print("python book_recommendation_api.py") 