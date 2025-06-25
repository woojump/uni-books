import requests
from bs4 import BeautifulSoup
import urllib3
import asyncio

# SSL 경고 비활성화
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

async def analyze_sejong_html():
    """성공한 세종대 검색 결과 HTML 분석"""
    
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    print("=== 세종대 검색 결과 HTML 분석 ===")
    
    try:
        # 메인 페이지 방문
        main_response = session.get("https://library.sejong.ac.kr/index.ax")
        print(f"메인 페이지 상태코드: {main_response.status_code}")
        
        await asyncio.sleep(1)
        
        # 검색 실행
        search_url = "https://library.sejong.ac.kr/search/Search.Result.ax"
        params = {
            'sid': '1',
            'q': '프로그래밍',
            'facet': 'Y'
        }
        
        response = session.get(search_url, params=params)
        print(f"검색 상태코드: {response.status_code}")
        print(f"응답 길이: {len(response.text)} 문자")
        
        # HTML 파일로 저장
        with open('sejong_working_result.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("✅ HTML 파일 저장: sejong_working_result.html")
        
        # 구조 분석
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n=== 모든 테이블 찾기 ===")
        tables = soup.find_all('table')
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            if len(rows) > 1:  # 헤더만 있는 테이블 제외
                print(f"테이블 {i+1}: {len(rows)}행, 클래스={table.get('class', [])}")
                
                # 첫 번째 데이터 행 확인
                if len(rows) > 1:
                    first_data_row = rows[1]
                    cells = first_data_row.find_all(['td', 'th'])
                    if len(cells) > 0:
                        first_cell_text = cells[0].get_text().strip()[:100]
                        print(f"   첫 번째 데이터: {first_cell_text}...")
                        
                        # 링크 확인
                        links = first_data_row.find_all('a')
                        if links:
                            for j, link in enumerate(links[:2]):
                                href = link.get('href', '')
                                text = link.get_text().strip()[:50]
                                print(f"   링크 {j+1}: {text}... (href: {href[:50]}...)")
        
        print("\n=== 모든 div 클래스 확인 ===")
        divs_with_class = soup.find_all('div', class_=True)
        class_counts = {}
        for div in divs_with_class:
            classes = div.get('class', [])
            for cls in classes:
                class_counts[cls] = class_counts.get(cls, 0) + 1
        
        # 자주 나타나는 클래스들 출력
        sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
        print("상위 div 클래스들:")
        for cls, count in sorted_classes[:10]:
            print(f"  .{cls}: {count}개")
            
        print("\n=== 검색 결과 관련 텍스트 찾기 ===")
        result_texts = [
            '검색결과', '총', '건', '권', 'result', 'total', 'found'
        ]
        
        for text in result_texts:
            elements = soup.find_all(string=lambda s: s and text in s.lower())
            for elem in elements[:3]:  # 처음 3개만
                parent = elem.parent if elem.parent else None
                if parent:
                    print(f"'{text}' 발견: {elem.strip()[:100]}... (태그: {parent.name})")
        
        # JavaScript 검색
        print("\n=== JavaScript 검색 ===")
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and ('result' in script.string.lower() or '검색' in script.string.lower()):
                content = script.string.strip()[:200]
                print(f"관련 스크립트 발견: {content}...")
                
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_sejong_html()) 