import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, quote

def fetch_news_headlines_and_links(site_config, keyword, count=10):
    """특정 키워드로 뉴스 사이트에서 헤드라인과 링크 추출
    
    Args:
        site_config: 사이트 설정 정보 딕셔너리 (네이버 뉴스 검색용)
        keyword: 검색할 키워드
        count: 가져올 뉴스 개수
        
    Returns:
        뉴스 헤드라인과 링크 리스트
    """
    try:
        # 요청 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 키워드를 URL 인코딩하고, site_config의 URL과 조합
        encoded_keyword = quote(keyword)
        full_url = f"{site_config['headlines_section_url']}{encoded_keyword}"
        
        # 뉴스 검색 결과 페이지 요청
        print(f"Requesting URL: {full_url}") # 디버깅을 위한 URL 출력
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 헤드라인 요소 찾기 (블로그 참고: 'a.news_tit')
        # site_config['headline_selector']는 'a.news_tit'으로 설정되어 있어야 함
        headline_elements = soup.select(site_config['headline_selector'])
        
        results = []
        for element in headline_elements[:count]:
            title = element.get_text().strip()
            link = element['href'] # a.news_tit이 <a> 태그이므로 href 속성 직접 사용
            
            # 네이버 검색 결과의 링크는 대부분 절대 URL이지만, 만약을 위해 base_url과 조합
            # (site_config['base_url']은 'https://search.naver.com' 등으로 설정)
            # 다만, 뉴스 기사 링크는 news.naver.com 도메인이므로, urljoin이 적절하지 않을 수 있음.
            # 실제 링크가 절대 URL인지 확인 필요. 대부분 절대 URL임.
            # link = urljoin(site_config['base_url'], link) # 이 부분은 실제 링크 형태에 따라 주석 처리 또는 수정
            
            results.append({'title': title, 'url': link})
            
            # 너무 빠른 요청 방지
            time.sleep(random.uniform(0.1, 0.3))
            
        return results
    
    except Exception as e:
        print(f"키워드 뉴스 헤드라인 크롤링 에러: {e} (URL: {full_url if 'full_url' in locals() else 'URL 생성 전 오류'})")
        return []

def fetch_article_content(article_url, site_config):
    """뉴스 기사 본문 추출
    
    Args:
        article_url: 기사 URL
        site_config: 사이트 설정 정보 딕셔너리
        
    Returns:
        기사 본문 텍스트
    """
    try:
        # 요청 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 기사 페이지 요청
        response = requests.get(article_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 본문 요소 찾기
        article_body = soup.select_one(site_config['article_body_selector'])
        
        if not article_body:
            return "기사 본문을 찾을 수 없습니다."
        
        # 불필요한 요소 제거 (광고, 관련기사 등)
        for tag in article_body.select('script, style, iframe, .ad_area, .related_news'):
            tag.decompose()
        
        # 텍스트 추출 및 정리
        paragraphs = article_body.find_all(['p', 'div'], recursive=True)
        text_content = '\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        
        return text_content
    
    except Exception as e:
        print(f"기사 크롤링 에러: {e}")
        return f"기사를 가져오는 중 오류가 발생했습니다: {str(e)}" 