import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, ContextTypes

from config import TELEGRAM_BOT_TOKEN, SELECTING_SITE, SELECTING_NEWS
from database import init_db, get_all_managed_sites, get_managed_site_config
from crawler import fetch_news_headlines_and_links, fetch_article_content
from ai_processor import process_article

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 뉴스 헤드라인 캐시
news_cache = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """봇 시작 명령어 처리"""
    # 데이터베이스 초기화
    init_db()
    
    # 관리 대상 뉴스 사이트 목록 가져오기
    sites = get_all_managed_sites()
    
    # 인라인 키보드 버튼 생성
    keyboard = []
    for site in sites:
        keyboard.append([InlineKeyboardButton(site['site_name'], callback_data=f"site_{site['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "안녕하세요! 🤖 AI 뉴스 셔츠체크 봇입니다.\n"
        "아래 목록에서 뉴스 사이트를 선택해주세요.",
        reply_markup=reply_markup
    )
    
    return SELECTING_SITE

async def select_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """사용자가 선택한 뉴스 사이트 처리"""
    query = update.callback_query
    await query.answer()
    
    # 콜백 데이터에서 사이트 ID 추출 (형식: "site_숫자")
    site_id = query.data.split('_')[1]
    
    # 선택한 사이트 정보 가져오기
    site_config = get_managed_site_config(site_id)
    
    if not site_config:
        await query.edit_message_text("사이트 정보를 찾을 수 없습니다. 다시 시도해주세요.")
        return ConversationHandler.END
    
    # 로딩 메시지 표시
    await query.edit_message_text(f"{site_config['site_name']}의 최신 뉴스를 가져오는 중입니다...")
    
    # 뉴스 헤드라인과 링크 가져오기
    news_list = fetch_news_headlines_and_links(site_config, count=10)
    
    if not news_list:
        await query.edit_message_text(
            f"{site_config['site_name']}에서 뉴스를 가져오지 못했습니다. 다시 시도해주세요.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("처음으로 돌아가기", callback_data="start_over")]])
        )
        return SELECTING_SITE
    
    # 뉴스 캐시에 저장
    context.user_data['current_site'] = site_config
    news_cache[query.from_user.id] = {
        'site_config': site_config,
        'news_list': news_list
    }
    
    # 인라인 키보드 버튼 생성
    keyboard = []
    for idx, news in enumerate(news_list):
        # 제목이 너무 길면 잘라내기
        title = news['title']
        if len(title) > 40:
            title = title[:37] + "..."
        
        keyboard.append([InlineKeyboardButton(title, callback_data=f"news_{idx}")])
    
    # 처음으로 돌아가기 버튼 추가
    keyboard.append([InlineKeyboardButton("다른 사이트 선택하기", callback_data="start_over")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"{site_config['site_name']}의 최신 뉴스 목록입니다.\n"
        "읽고 싶은 기사를 선택해주세요.",
        reply_markup=reply_markup
    )
    
    return SELECTING_NEWS

async def select_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """사용자가 선택한 뉴스 기사 처리"""
    query = update.callback_query
    await query.answer()
    
    # 사용자의 캐시된 뉴스 목록 가져오기
    user_cache = news_cache.get(query.from_user.id)
    if not user_cache:
        await query.edit_message_text(
            "세션이 만료되었습니다. 다시 시작해주세요.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("처음으로 돌아가기", callback_data="start_over")]])
        )
        return SELECTING_SITE
    
    # 콜백 데이터에서 뉴스 인덱스 추출 (형식: "news_숫자")
    news_idx = int(query.data.split('_')[1])
    
    # 선택한 뉴스 정보 가져오기
    selected_news = user_cache['news_list'][news_idx]
    site_config = user_cache['site_config']
    
    # 로딩 메시지 표시
    await query.edit_message_text(f"선택하신 기사를 분석 중입니다...\n\n제목: {selected_news['title']}")
    
    # 기사 본문 가져오기
    article_content = fetch_article_content(selected_news['url'], site_config)
    
    if not article_content or article_content.startswith("기사를 가져오는 중 오류가 발생했습니다"):
        await query.edit_message_text(
            f"기사 내용을 가져오지 못했습니다. 다시 시도해주세요.\n\n{article_content}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("뉴스 목록으로 돌아가기", callback_data=f"site_{site_config['id']}")]])
        )
        return SELECTING_NEWS
    
    # AI 처리 시작
    await query.edit_message_text(f"AI가 기사를 분석 중입니다...\n\n제목: {selected_news['title']}")
    
    # AI 처리 (사실 추출 -> 중립화 및 주석 추가 -> 요약)
    summary = process_article(article_content)
    
    # 결과 표시 (원본 기사 링크 포함)
    result_text = (
        f"📰 *{selected_news['title']}*\n\n"
        f"{summary}\n\n"
        f"[원본 기사 보기]({selected_news['url']})"
    )
    
    # 인라인 키보드 버튼 생성
    keyboard = [
        [InlineKeyboardButton("뉴스 목록으로 돌아가기", callback_data=f"site_{site_config['id']}")],
        [InlineKeyboardButton("처음으로 돌아가기", callback_data="start_over")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Markdown 형식으로 결과 표시
    await query.edit_message_text(
        result_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True  # 링크 미리보기 비활성화
    )
    
    return SELECTING_NEWS

async def start_over(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """처음으로 돌아가기"""
    query = update.callback_query
    await query.answer()
    
    # 관리 대상 뉴스 사이트 목록 가져오기
    sites = get_all_managed_sites()
    
    # 인라인 키보드 버튼 생성
    keyboard = []
    for site in sites:
        keyboard.append([InlineKeyboardButton(site['site_name'], callback_data=f"site_{site['id']}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "뉴스 사이트를 선택해주세요.",
        reply_markup=reply_markup
    )
    
    return SELECTING_SITE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대화 취소"""
    user = update.message.from_user
    logger.info("사용자 %s가 대화를 취소했습니다.", user.first_name)
    
    await update.message.reply_text(
        "대화가 취소되었습니다. 다시 시작하려면 /start 명령어를 입력해주세요."
    )
    
    return ConversationHandler.END

def main():
    """메인 함수"""
    # 애플리케이션 생성
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 대화 핸들러 설정
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_SITE: [
                CallbackQueryHandler(select_site, pattern=r"^site_\d+$"),
                CallbackQueryHandler(start_over, pattern="^start_over$")
            ],
            SELECTING_NEWS: [
                CallbackQueryHandler(select_news, pattern=r"^news_\d+$"),
                CallbackQueryHandler(select_site, pattern=r"^site_\d+$"),
                CallbackQueryHandler(start_over, pattern="^start_over$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # 대화 핸들러 등록
    application.add_handler(conv_handler)
    
    # 봇 실행
    application.run_polling()

if __name__ == "__main__":
    main() 