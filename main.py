import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from telegram.error import BadRequest

from config import TELEGRAM_BOT_TOKEN
# 상태 정의를 config.py에서 가져오거나 여기서 명시적으로 정의합니다.
# 예시: ASKING_KEYWORD, SELECTING_KEYWORD_NEWS = range(2) # config.py로 옮기는 것을 권장
# 아래는 main.py에 직접 정의하는 경우
ASKING_KEYWORD, SELECTING_KEYWORD_NEWS = range(2)

from database import init_db, get_managed_site_config
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
    
    await update.message.reply_text(
        "안녕하세요! 🤖 AI 뉴스 요약 봇입니다.\n"
        "분석하고 싶은 뉴스 검색 키워드를 입력해주세요."
    )
    
    return ASKING_KEYWORD

async def ask_keyword_again_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "분석하고 싶은 뉴스 검색 키워드를 다시 입력해주세요."
    )
    return ASKING_KEYWORD

async def handle_keyword(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyword = update.message.text
    user_id = update.message.from_user.id
    
    site_config = get_managed_site_config("네이버 뉴스")
    if not site_config:
        await update.message.reply_text("네이버 뉴스 설정을 찾을 수 없습니다. 관리자에게 문의하세요.")
        return ConversationHandler.END

    loading_message = await update.message.reply_text(f"'{keyword}'에 대한 뉴스를 네이버에서 검색 중입니다...")
    
    news_list = fetch_news_headlines_and_links(site_config, keyword, count=10)
    
    try:
        await loading_message.delete()
    except Exception as e:
        logger.info(f"메시지 삭제 실패 (이미 삭제되었을 수 있음): {e}")

    if not news_list:
        keyboard = [[InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"'{keyword}'에 대한 뉴스를 찾지 못했습니다. 다른 키워드로 시도해보세요.",
            reply_markup=reply_markup
        )
        return ASKING_KEYWORD
    
    news_cache[user_id] = {
        'site_config': site_config,
        'news_list': news_list,
        'keyword': keyword
    }
    
    keyboard = []
    for idx, news_item in enumerate(news_list):
        title = news_item['title']
        if len(title) > 40:
            title = title[:37] + "..."
        keyboard.append([InlineKeyboardButton(title, callback_data=f"news_{idx}")])
    
    keyboard.append([InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"'{keyword}'에 대한 네이버 뉴스 검색 결과입니다.\n"
        "읽고 싶은 기사를 선택해주세요.",
        reply_markup=reply_markup
    )
    return SELECTING_KEYWORD_NEWS

async def select_keyword_news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """사용자가 선택한 뉴스 기사 처리"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    user_cache = news_cache.get(user_id)
    if not user_cache:
        await query.edit_message_text(
            "세션이 만료되었거나 오류가 발생했습니다. 다른 키워드로 다시 검색해주세요.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]])
        )
        return ASKING_KEYWORD
    
    news_idx = int(query.data.split('_')[1])
    selected_news = user_cache['news_list'][news_idx]
    site_config = user_cache['site_config']
    current_keyword = user_cache['keyword']
    
    await query.edit_message_text(f"선택하신 기사를 분석 중입니다...\n\n제목: {selected_news['title']}")
    
    article_content = fetch_article_content(selected_news['url'], site_config)
    
    if not article_content or article_content.startswith("기사를 가져오는 중 오류가 발생했습니다") or article_content == "기사 본문을 찾을 수 없습니다.":
        keyboard = [
            [InlineKeyboardButton(f"'{current_keyword}' 목록으로 돌아가기", callback_data=f"keyword_showlist")],
            [InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"기사 내용을 가져오지 못했습니다: {article_content}. 다른 기사를 선택하거나 새 키워드로 검색해주세요.",
            reply_markup=reply_markup
        )
        return SELECTING_KEYWORD_NEWS
    
    await query.edit_message_text(f"AI가 기사를 분석 중입니다... (시간이 좀 걸릴 수 있어요)\n\n제목: {selected_news['title']}")
    summary_html = process_article(article_content)
    
    title_raw = selected_news['title']
    url_raw = selected_news['url']

    # HTML 태그 직접 사용
    result_text = (
        f"📰 <b>{title_raw}</b> (<i>{current_keyword}</i> 검색 결과)\n\n" 
        f"{summary_html}\n\n"  # AI가 생성한 summary (이미 HTML)
        f"<a href=\"{url_raw}\">원본 기사 보기</a>" # HTML 링크 사용 (f-string 내 따옴표 이스케이프 주의)
    )
    
    logger.info(f"Attempting to send HTML to Telegram (length: {len(result_text)}):\n{result_text}") # 로깅 추가

    keyboard = [
        [InlineKeyboardButton(f"'{current_keyword}' 목록으로 돌아가기", callback_data=f"keyword_showlist")],
        [InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        MAX_MESSAGE_LENGTH = 4096
        if len(result_text) > MAX_MESSAGE_LENGTH:
            logger.info(f"Message is too long ({len(result_text)} chars), attempting to split.")
            # 첫 메시지: 제목, 키워드, 링크 + 요약의 일부
            # 주의: 이 분할 방식은 HTML 태그를 중간에 자를 수 있어 완벽하지 않음
            # 더 나은 방법은 HTML 파서를 사용하여 안전하게 분할하는 것이나, 여기서는 길이 기반으로 단순 분할.
            
            # 헤더 부분 (제목, 키워드, 링크)을 먼저 구성
            header_part = f"📰 <b>{title_raw}</b> (<i>{current_keyword}</i> 검색 결과)\n\n"
            link_part = f"\n\n<a href=\"{url_raw}\">원본 기사 보기</a>"
            
            remaining_length_for_summary = MAX_MESSAGE_LENGTH - len(header_part) - len(link_part) - 50 # 약간의 여유 공간
            
            if remaining_length_for_summary < 100: # 요약이 들어갈 공간이 너무 작으면 그냥 첫 메시지에 다 보냄 (오류 발생 가능성 있음)
                logger.warning("Not enough space for summary in the first part of a split message. Sending as is.")
                await query.edit_message_text(
                    result_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
            else:
                # 첫 번째 메시지 전송 (요약 일부 포함)
                first_part_summary = summary_html[:remaining_length_for_summary]
                # HTML 태그가 잘릴 수 있으므로, 마지막 태그를 닫거나 하는 등의 처리가 필요할 수 있음 (여기서는 생략)
                # 간단하게는 마지막 단어까지만 자르는 방법도 고려 가능
                # 여기서는 일단 길이로만 자름
                
                # 혹시나 first_part_summary가 비어있지는 않은지 확인
                if not first_part_summary.strip(): 
                     first_part_summary = "요약 내용이 너무 길어 일부만 표시합니다..."

                message_part1 = f"{header_part}{first_part_summary}... (내용이 이어집니다)"
                
                await query.edit_message_text(
                    text=message_part1,
                    parse_mode='HTML',
                    disable_web_page_preview=True 
                    # 첫 메시지에는 버튼 미포함 또는 별도 처리 (여기서는 일단 미포함)
                )
                
                # 나머지 요약 및 링크, 버튼을 새 메시지로 전송
                # query.message.reply_text 또는 context.bot.send_message 사용 필요
                # edit_message_text는 한 번만 가능하므로, 두 번째 메시지는 새로 보내야 함.
                remaining_summary = summary_html[remaining_length_for_summary:]
                
                # 혹시나 remaining_summary가 비어있지는 않은지 확인
                if not remaining_summary.strip() and first_part_summary != "요약 내용이 너무 길어 일부만 표시합니다...":
                    # 이 경우는 거의 없겠지만, 혹시 summary_html이 remaining_length_for_summary 와 정확히 같다면
                    # remaining_summary 가 공백일 수 있음. 이런 경우 추가 메시지 불필요
                    pass 
                else:
                    message_part2 = f"... (이전 내용에서 이어짐)\n\n{remaining_summary}{link_part}"
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=message_part2,
                        reply_markup=reply_markup, # 버튼은 두 번째 메시지에 포함
                        parse_mode='HTML',
                        disable_web_page_preview=True
                    )
        else:
            # 메시지가 길지 않으면 한 번에 전송
            await query.edit_message_text(
                result_text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            
    except BadRequest as br_error:
        logger.error(f"Telegram BadRequest: {br_error}\nContent was: {result_text}")
        error_message_to_user = (
            "죄송합니다. 😥 메시지를 표시하는 중에 오류가 발생했어요.\n"
            f"(오류: {br_error.message})\n"
            "다른 기사를 선택하시거나 새로운 키워드로 검색해보시겠어요?"
        )
        try:
            await query.edit_message_text(
                text=error_message_to_user,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]])
            )
        except Exception as inner_e:
            logger.error(f"Error sending error message to user: {inner_e}")
        return ASKING_KEYWORD
    except Exception as e:
        logger.error(f"Generic error sending message: {e}\nContent was: {result_text}")
        error_message_to_user = (
            "죄송합니다. 😥 메시지를 처리하는 중 알 수 없는 오류가 발생했습니다.\n"
            "다른 기사를 선택하시거나 새로운 키워드로 검색해보시겠어요?"
        )
        await query.edit_message_text(
            text=error_message_to_user,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]])
        )
        return ASKING_KEYWORD

    return SELECTING_KEYWORD_NEWS

async def return_to_keyword_news_list_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    user_cache = news_cache.get(user_id)
    if not user_cache or 'news_list' not in user_cache or 'keyword' not in user_cache:
        await query.edit_message_text(
            "이전 검색 결과를 찾을 수 없습니다. 다른 키워드로 다시 검색해주세요.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")]])
        )
        return ASKING_KEYWORD

    news_list = user_cache['news_list']
    keyword = user_cache['keyword']

    keyboard_buttons = []
    for idx, news_item in enumerate(news_list):
        title = news_item['title']
        if len(title) > 40:
            title = title[:37] + "..."
        keyboard_buttons.append([InlineKeyboardButton(title, callback_data=f"news_{idx}")])
    
    keyboard_buttons.append([InlineKeyboardButton("다른 키워드로 검색하기", callback_data="ask_keyword_again")])
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)

    await query.edit_message_text(
        f"'{keyword}'에 대한 네이버 뉴스 검색 결과입니다.\n"
        "읽고 싶은 기사를 선택해주세요.",
        reply_markup=reply_markup
    )
    return SELECTING_KEYWORD_NEWS

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """대화 취소"""
    user = update.message.from_user if update.message else update.callback_query.from_user
    logger.info("사용자 %s가 대화를 취소하거나 완료했습니다.", user.first_name)
    
    reply_text = "대화가 종료되었습니다. 다시 시작하려면 /start 명령어를 입력해주세요."
    if update.message:
        await update.message.reply_text(reply_text)
    elif update.callback_query:
        try:
            await update.callback_query.edit_message_text(reply_text)
        except Exception as e:
            logger.error(f"메시지 수정 중 오류 (cancel): {e}")
            # Fallback: send a new message if editing fails
            await context.bot.send_message(chat_id=user.id, text=reply_text)
            
    news_cache.pop(user.id, None) 
    return ConversationHandler.END

def main():
    """메인 함수"""
    # 애플리케이션 생성
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 대화 핸들러 설정
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASKING_KEYWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_keyword),
                CallbackQueryHandler(ask_keyword_again_callback, pattern="^ask_keyword_again$")
            ],
            SELECTING_KEYWORD_NEWS: [
                CallbackQueryHandler(select_keyword_news, pattern=r"^news_\d+$"),
                CallbackQueryHandler(ask_keyword_again_callback, pattern="^ask_keyword_again$"),
                CallbackQueryHandler(return_to_keyword_news_list_callback, pattern="^keyword_showlist$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel), CallbackQueryHandler(cancel, pattern="^cancel$")],
    )
    
    # 대화 핸들러 등록
    application.add_handler(conv_handler)
    
    # 봇 실행
    application.run_polling()

if __name__ == "__main__":
    main() 