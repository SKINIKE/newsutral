import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 로드
load_dotenv()

# 텔레그램 봇 토큰
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "이곳에 텔레그램 봇 토큰을 넣으세요")

# Google Gemini API 키
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "이곳에 Gemini API 키를 넣으세요")

# 데이터베이스 경로
DB_PATH = "newsutral.db"

# 대화 상태 정의 (키워드 기반으로 변경)
ASKING_KEYWORD, SELECTING_KEYWORD_NEWS = range(2)
# SELECTING_SITE, SELECTING_NEWS = range(2) # 이전 상태 정의는 주석 처리 또는 삭제 