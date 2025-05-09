# AI 기반 뉴스 셔츠체크 및 요약 봇

텔레그램을 통해 사용자가 선택한 뉴스 사이트의 최신 기사를 제공하고, Google Gemini API를 활용하여 선택한 기사의 사실 정보 추출, 중립적 주석 추가, 가독성 높은 요약을 제공하는 AI 봇입니다.

## 주요 기능

- **뉴스 사이트 선택**: 미리 정의된 주요 뉴스 사이트 목록에서 원하는 사이트 선택
- **최신 뉴스 목록 확인**: 선택한 사이트의 최신 뉴스 헤드라인 목록 제공
- **AI 기반 뉴스 처리**: 선택한 기사에 대해 다음 과정 수행
  1. **팩트 추출**: 기사 내용에서 객관적 사실만 추출
  2. **중립성 확보 및 주석**: 추출된 사실에 중립적 관점의 주석 추가
  3. **요약 및 재구성**: 처리된 내용을 가독성 높게 요약

## 기술 스택

- **Python**: 프로그래밍 언어
- **python-telegram-bot**: 텔레그램 봇 API 연동
- **BeautifulSoup4**: 웹 크롤링 및 파싱
- **Google Gemini API**: AI 처리 (사실 추출, 중립화, 요약)
- **SQLite**: 데이터 저장 및 관리

## 설치 및 실행 방법

1. 저장소 클론
   ```bash
   git clone https://github.com/yourusername/newsutral.git
   cd newsutral
   ```

2. 필요한 패키지 설치
   ```bash
   pip install -r requirements.txt
   ```

3. 환경 변수 설정
   - `.env` 파일 생성 및 다음 내용 입력:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. 봇 실행
   ```bash
   python main.py
   ```

## 봇 사용 방법

1. 텔레그램에서 봇 검색 및 시작 (`/start` 명령어 입력)
2. 표시된 뉴스 사이트 목록에서 원하는 사이트 선택
3. 최신 뉴스 목록에서 읽고 싶은 기사 선택
4. AI가 처리한 뉴스 요약 확인

## 디렉토리 구조

- `main.py`: 메인 애플리케이션 및 텔레그램 봇 설정
- `crawler.py`: 뉴스 크롤링 모듈
- `ai_processor.py`: Google Gemini API를 사용한 AI 처리 모듈
- `database.py`: SQLite 데이터베이스 관리 모듈
- `config.py`: 설정 파일
- `requirements.txt`: 필요한 패키지 목록

## 개발자 정보

- 개발자 이름
- 이메일 주소
- GitHub 프로필 링크
- 라이센스 정보
