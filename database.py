import sqlite3
from config import DB_PATH

def init_db():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # managed_news_sites 테이블 생성
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS managed_news_sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site_name TEXT NOT NULL UNIQUE,
        base_url TEXT NOT NULL,
        headlines_section_url TEXT NOT NULL,
        headline_selector TEXT NOT NULL,
        link_selector TEXT NOT NULL,
        article_body_selector TEXT NOT NULL
    )
    ''')
    
    # 초기 데이터 삽입 (중복 방지를 위한 조건부 삽입)
    sites = [
        (
            "네이버 뉴스",
            "https://search.naver.com",
            "https://search.naver.com/search.naver?where=news&query=",
            "a.news_tit",
            "a.news_tit",
            "article#dic_area"
        )
        # 다른 사이트 설정은 일단 주석 처리하거나 삭제 (현재는 네이버 키워드 검색에 집중)
        # (
        #     "다음 뉴스",
        #     "https://news.daum.net",
        #     "https://news.daum.net/ranking/popular",
        #     "a.link_txt",
        #     "a.link_txt",
        #     "div.article_view"
        # ),
        # (
        #     "중앙일보",
        #     "https://www.joongang.co.kr",
        #     "https://www.joongang.co.kr/ranks/clicknews",
        #     "h2.headline a",
        #     "h2.headline a",
        #     "div#article_body"
        # )
    ]
    
    for site in sites:
        cursor.execute("""
        INSERT OR IGNORE INTO managed_news_sites 
        (site_name, base_url, headlines_section_url, headline_selector, link_selector, article_body_selector) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, site)
    
    conn.commit()
    conn.close()

def get_all_managed_sites():
    """모든 관리 대상 뉴스 사이트 정보 반환 (현재는 네이버 뉴스만 반환하도록 수정)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 네이버 뉴스 설정만 가져오도록 하거나, 첫 번째 설정만 사용하도록 가정
    cursor.execute("SELECT * FROM managed_news_sites WHERE site_name = ?", ("네이버 뉴스",))
    site = cursor.fetchone()
    
    conn.close()
    return [dict(site)] if site else [] # 단일 사이트지만 리스트 형태로 반환

def get_managed_site_config(site_id_or_name):
    """특정 사이트의 설정 정보 반환
    
    Args:
        site_id_or_name: 사이트 ID(정수) 또는 사이트 이름(문자열)
    
    Returns:
        사이트 설정 정보 딕셔너리 또는 None
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if isinstance(site_id_or_name, int) or site_id_or_name.isdigit():
        cursor.execute("SELECT * FROM managed_news_sites WHERE id = ?", (site_id_or_name,))
    else:
        cursor.execute("SELECT * FROM managed_news_sites WHERE site_name = ?", (site_id_or_name,))
    
    row = cursor.fetchone()
    result = dict(row) if row else None
    
    conn.close()
    return result 