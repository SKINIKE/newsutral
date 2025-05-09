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

        # headline_selector는 이제 각 뉴스 아이템을 감싸는 div.sds-comps-vertical-layout... 입니다.
        news_item_containers = soup.select(site_config['headline_selector'])
        
        print(f"사용된 아이템 컨테이너 선택자: {site_config['headline_selector']}")
        print(f"선택된 뉴스 아이템 컨테이너 개수: {len(news_item_containers)}")

        if not news_item_containers:
            print(f"뉴스 아이템 컨테이너를 찾지 못했습니다. HTML 일부: {str(soup)[:500]}")
            return []
        
        results = []
        for item_container in news_item_containers[:count]: 
            # 1. item_container 내에서 실제 기사 제목 링크(title_link_element)와 제목(title) 추출
            # link_selector는 'a.n6AJosQA40hUOAe_Vplg.cdv6mdm2_kpW2D6slkm6'
            title_link_element = item_container.select_one(site_config['link_selector'])
            
            if not title_link_element:
                # print(f"정보: 현 아이템 컨테이너 내에서 제목 링크({site_config['link_selector']})를 찾지 못했습니다. 컨테이너 HTML: {str(item_container)[:300]}...")
                continue

            title = None
            # 제목은 title_link_element 안의 특정 span 에서 추출 시도
            # 예: <span class="sds-comps-text sds-comps-text-ellipsis-1 sds-comps-text-type-headline1">
            title_span = title_link_element.select_one('span.sds-comps-text-type-headline1') 
            if title_span:
                title = title_span.get_text().strip()
            else: # 못찾으면 title_link_element 자체의 텍스트 사용 (간혹 span 없이 a 태그에 바로 텍스트가 있을 수 있음)
                title = title_link_element.get_text().strip()
            
            if not title or title == "제목을 찾을 수 없음":
                # print(f"정보: 유효한 제목을 찾을 수 없어 건너<0xEB><0x9B><0x84>니다. 링크 요소: {title_link_element}")
                continue

            # 2. item_container 내에서 '네이버뉴스' 링크 찾기
            #    <span class="sds-comps-text sds-comps-text-type-body2 sds-comps-text-weight-sm sds-comps-profile-info-subtext">
            #       <a href="...n.news.naver.com..." class="n6AJosQA40hUOAe_Vplg tNtRMm1EBtRE0aoB5qXm">
            #           <span class="sds-comps-text sds-comps-text-type-body2 sds-comps-text-weight-sm">네이버뉴스</span>
            #       </a>
            #    </span>
            naver_news_link_element = None
            # 네이버뉴스 링크를 포함하는 모든 a 태그를 먼저 찾습니다.
            possible_naver_links = item_container.select('a[href*="n.news.naver.com"]')
            for link in possible_naver_links:
                # 해당 a 태그 또는 그 자식 span에 "네이버뉴스" 텍스트가 있는지 확인합니다.
                if '네이버뉴스' in link.get_text(strip=True):
                    # 추가적으로, 이 링크가 언론사 정보(profile) 영역에 있는지 확인하여 정확도를 높일 수 있습니다.
                    # 예: link.find_parent('div', class_='sds-comps-profile-info')
                    # 여기서는 일단 텍스트 기반으로 찾습니다.
                    naver_news_link_element = link
                    break 
            
            if title_link_element and naver_news_link_element: # 제목과 네이버뉴스 링크가 모두 있어야 함
                naver_news_url = naver_news_link_element['href']
                # URL 완전성 보장 (보통은 절대 URL이지만)
                if not naver_news_url.startswith('http'):
                    naver_news_url = urljoin(site_config['base_url'], naver_news_url)

                print(f"추출 성공: 제목='{title}', 네이버뉴스 링크='{naver_news_url}'")
                results.append({'title': title, 'url': naver_news_url})
            # else:
                # if not title_link_element:
                #     print(f"디버그: 아이템 컨테이너에서 제목 링크 못찾음. 컨테이너: {str(item_container)[:200]}")
                # if not naver_news_link_element:
                #      print(f"디버그: 아이템 컨테이너 '{title}' 에서 네이버뉴스 링크 못찾음. 컨테이너: {str(item_container)[:200]}")

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
        # div#newsct_article 요소 내부의 전체 텍스트를 가져오고, strip=True로 각 줄의 앞뒤 공백을 제거하며, separator='\n'으로 줄바꿈을 유지합니다.
        text_content = article_body.get_text(separator='\n', strip=True)
        
        return text_content
    
    except Exception as e:
        print(f"기사 크롤링 에러: {e}")
        return f"기사를 가져오는 중 오류가 발생했습니다: {str(e)}" 