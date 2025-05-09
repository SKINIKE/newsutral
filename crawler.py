import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin

def fetch_news_headlines_and_links(site_config, count=10):
    """뉴스 사이트에서 헤드라인과 링크 추출
    
    Args:
        site_config: 사이트 설정 정보 딕셔너리
        count: 가져올 뉴스 개수
        
    Returns:
        뉴스 헤드라인과 링크 리스트
    """
    try:
        # 요청 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # 뉴스 헤드라인 페이지 요청
        response = requests.get(site_config['headlines_section_url'], headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 헤드라인 요소 찾기
        headline_elements = soup.select(site_config['headline_selector'])
        
        results = []
        for element in headline_elements[:count]:
            # 제목 추출
            title = element.get_text().strip()
            
            # 링크 추출 (링크 선택자가 헤드라인 선택자와 다른 경우)
            if site_config['link_selector'] != site_config['headline_selector']:
                link_element = element.select_one(site_config['link_selector'])
                link = link_element['href'] if link_element else element['href']
            else:
                link = element['href']
            
            # 상대 URL을 절대 URL로 변환
            link = urljoin(site_config['base_url'], link)
            
            results.append({'title': title, 'url': link})
            
            # 너무 빠른 요청 방지
            time.sleep(random.uniform(0.1, 0.3))
            
        return results
    
    except Exception as e:
        print(f"헤드라인 크롤링 에러: {e}")
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