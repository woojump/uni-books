import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import re


class ImprovedBooksCrawler:
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
    
    def crawl_aladin_books_improved(self, keyword, limit=10):
        """
        개선된 알라딘 크롤링 - 더 정확한 정보 추출
        """
        print(f"알라딘에서 '{keyword}' 키워드로 검색합니다...")
        
        try:
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
            
            # 알라딘 도서 목록 추출 - 여러 패턴 시도
            book_items = soup.find_all('div', class_='ss_book_box')
            
            if not book_items:
                book_items = soup.find_all('table', {'bgcolor': '#FFFFFF'})
            
            if not book_items:
                book_items = soup.find_all('tr', class_='search_list')
            
            print(f"알라딘에서 {len(book_items)}개의 도서를 찾았습니다.")
            
            for i, item in enumerate(book_items[:limit]):
                try:
                    book_info = self.extract_aladin_book_info_improved(item)
                    if book_info and book_info.get('title'):
                        books.append(book_info)
                        print(f"크롤링 완료: {len(books)}/{limit} - {book_info['title']}")
                    
                    if len(books) >= limit:
                        break
                        
                    time.sleep(0.3)  # 요청 간격 조절
                    
                except Exception as e:
                    print(f"책 정보 추출 실패: {e}")
                    continue
            
            return books
            
        except Exception as e:
            print(f"알라딘 크롤링 실패: {e}")
            return []
    
    def extract_aladin_book_info_improved(self, item):
        """
        개선된 알라딘 HTML에서 책 정보를 추출합니다.
        """
        book_info = {}
        
        try:
            # 제목 추출 - 여러 선택자 시도
            title_elem = item.find('a', class_='bo3')
            if not title_elem:
                title_elem = item.find('b', class_='bo3')
            if not title_elem:
                title_elem = item.find('a', href=lambda x: x and 'ItemId=' in x)
            
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # 불필요한 텍스트 제거
                title_text = re.sub(r'\[.*?\]', '', title_text).strip()
                book_info['title'] = title_text
            
            # 전체 텍스트에서 정보 추출
            full_text = item.get_text()
            
            # 저자 추출 - 정규식 사용
            author_patterns = [
                r'저자\s*:\s*([^|]+)',
                r'지은이\s*:\s*([^|]+)',
                r'글\s*:\s*([^|]+)',
                r'([가-힣a-zA-Z\s,]+)\s*\(지은이\)',
                r'([가-힣a-zA-Z\s,]+)\s*저',
            ]
            
            for pattern in author_patterns:
                match = re.search(pattern, full_text)
                if match:
                    author = match.group(1).strip()
                    # 불필요한 정보 제거
                    author = re.sub(r'\(.*?\)', '', author).strip()
                    if author and len(author) < 50:  # 너무 긴 텍스트는 제외
                        book_info['author'] = author
                        break
            
            # 출판사 추출 - 정규식 사용
            publisher_patterns = [
                r'출판사\s*:\s*([^|]+)',
                r'출판\s*:\s*([^|]+)',
                r'([가-힣a-zA-Z0-9\s]+)\s*\|\s*\d{4}',
                r'\|\s*([가-힣a-zA-Z0-9\s]+)\s*\|\s*\d{4}',
            ]
            
            for pattern in publisher_patterns:
                match = re.search(pattern, full_text)
                if match:
                    publisher = match.group(1).strip()
                    if publisher and len(publisher) < 30:  # 너무 긴 텍스트는 제외
                        book_info['publisher'] = publisher
                        break
            
            # 가격 추출
            price_elem = item.find('span', class_='ss_p2')
            if not price_elem:
                price_elem = item.find('b', class_='ss_p2')
            if not price_elem:
                # 가격 패턴으로 찾기
                price_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*원', full_text)
                if price_match:
                    book_info['price'] = price_match.group(1) + '원'
            else:
                book_info['price'] = price_elem.get_text(strip=True)
            
            # 이미지 URL 추출
            img_elem = item.find('img')
            if img_elem and img_elem.get('src'):
                img_url = img_elem.get('src')
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    img_url = 'https://www.aladin.co.kr' + img_url
                book_info['image_url'] = img_url
            
            # 상품 링크 추출
            link_elem = item.find('a', href=lambda x: x and 'ItemId=' in x)
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('/'):
                    book_info['product_url'] = 'https://www.aladin.co.kr' + href
                else:
                    book_info['product_url'] = href
            
            return book_info
            
        except Exception as e:
            print(f"알라딘 책 정보 추출 중 오류: {e}")
            return None
    
    def crawl_cooking_books_comprehensive(self, limit=10):
        """
        요리 관련 다양한 키워드로 종합 검색
        """
        keywords = ['요리', '레시피', '쿠킹', '요리책', '홈쿠킹', '베이킹']
        all_books = []
        
        for keyword in keywords:
            if len(all_books) >= limit:
                break
                
            print(f"\n'{keyword}' 키워드로 검색 중...")
            books = self.crawl_aladin_books_improved(keyword, limit=3)
            
            for book in books:
                # 중복 제거
                if not any(existing_book['title'] == book['title'] for existing_book in all_books):
                    all_books.append(book)
                    
                if len(all_books) >= limit:
                    break
            
            time.sleep(1)  # 키워드 간 대기
        
        return all_books[:limit]
    
    def save_to_json(self, books, filename='improved_cooking_books.json'):
        """
        크롤링된 책 정보를 JSON 파일로 저장합니다.
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(books, f, ensure_ascii=False, indent=2)
            print(f"결과를 {filename}에 저장했습니다.")
        except Exception as e:
            print(f"파일 저장 실패: {e}")
    
    def save_to_csv(self, books, filename='improved_cooking_books.csv'):
        """
        크롤링된 책 정보를 CSV 파일로 저장합니다.
        """
        try:
            df = pd.DataFrame(books)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"결과를 {filename}에 저장했습니다.")
        except Exception as e:
            print(f"CSV 저장 실패: {e}")


def main():
    """
    메인 실행 함수 - 개선된 실제 데이터 크롤링
    """
    print("개선된 실제 요리 관련 도서 크롤링을 시작합니다...")
    print("다양한 키워드로 종합 검색")
    print("크롤링 개수: 10개")
    print("-" * 50)
    
    crawler = ImprovedBooksCrawler()
    
    # 종합 검색으로 다양한 요리 관련 책 수집
    books = crawler.crawl_cooking_books_comprehensive(limit=10)
    
    if books:
        print(f"\n총 {len(books)}개의 실제 도서를 크롤링했습니다.")
        print("\n=== 개선된 실제 크롤링 결과 ===")
        
        for i, book in enumerate(books, 1):
            print(f"\n{i}. {book.get('title', 'N/A')}")
            print(f"   저자: {book.get('author', 'N/A')}")
            print(f"   출판사: {book.get('publisher', 'N/A')}")
            print(f"   가격: {book.get('price', 'N/A')}")
            if book.get('product_url'):
                print(f"   링크: {book.get('product_url')}")
        
        # 파일로 저장
        crawler.save_to_json(books)
        crawler.save_to_csv(books)
        
        print(f"\n개선된 실제 크롤링 데이터가 성공적으로 저장되었습니다!")
        
    else:
        print("\n실제 크롤링 결과가 없습니다.")


if __name__ == "__main__":
    main() 