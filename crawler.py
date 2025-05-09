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
    full_url = ""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        encoded_keyword = quote(keyword)
        full_url = f"{site_config['headlines_section_url']}{encoded_keyword}"
        
        print(f"Requesting URL: {full_url}")
        response = requests.get(full_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # headline_selector는 database.py에서 'div.group_news a.n6AJosQA40hUOAe_Vplg' 등으로 설정됨
        news_link_elements = soup.select(site_config['headline_selector'])
        
        print(f"사용된 선택자: {site_config['headline_selector']}")
        print(f"선택된 뉴스 링크 요소 개수: {len(news_link_elements)}")

        if not news_link_elements:
            print("뉴스 링크 요소를 찾지 못했습니다.")
            # print(soup.prettify()) # 전체 HTML 확인 필요시 주석 해제
            return []
        
        results = []
        for link_element in news_link_elements[:count]:
            link = link_element['href']
            title = None 
            
            title_span_specific = link_element.find('span', class_='sds-comps-text-type-headline1')
            if title_span_specific:
                title = title_span_specific.get_text().strip()
            
            if not title:
                spans_in_link = link_element.find_all('span', recursive=False)
                if spans_in_link:
                    # 첫 번째 span의 텍스트를 사용하거나, 모든 span 텍스트를 합칠 수 있음
                    # 여기서는 첫 번째 span의 텍스트를 사용
                    title = spans_in_link[0].get_text().strip()
                    if title:
                        print(f"정보: '{link}' 링크에서 특정 클래스 span 못찾음. 첫번째 span 사용: '{title}'")
                    else:
                        title = None 
            
            if not title: 
                title = "제목을 찾을 수 없음"
                print(f"경고: '{link}' 링크에서 제목을 최종적으로 찾지 못함.")

            # 제목이 비어있거나, 특정 키워드(예: 언론사명)만 있는 경우를 추가적으로 필터링 할 수도 있음
            # 예: if not title or title in ["네이버뉴스", "연합뉴스"] : continue # 이런 뉴스는 건너뛰기

            print(f"추출 결과 - 제목: {title}, 링크: {link}")
            results.append({'title': title, 'url': link})
            time.sleep(random.uniform(0.1, 0.3))
                
        return results

    except Exception as e:
        print(f"키워드 뉴스 헤드라인 크롤링 에러: {e} (URL: {full_url if full_url else 'URL 생성 전 오류'})")
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