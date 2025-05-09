import google.generativeai as genai
from config import GEMINI_API_KEY

# Google Gemini API 초기화
genai.configure(api_key=GEMINI_API_KEY)

def extract_facts_from_article(article_text):
    """기사 내용에서 객관적 사실만 추출
    
    Args:
        article_text: 기사 전체 내용 텍스트
        
    Returns:
        추출된 객관적 사실 텍스트
    """
    try:
        # Gemini 2.0 Flash 모델 사용
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        다음은 뉴스 기사입니다. 이 기사에서 객관적 사실만 추출해주세요.
        - 의견이나 추측 내용은 제외하고 검증 가능한 사실만 추출하세요.
        - 단순 나열이 아닌, 문맥을 유지하며 중요한 사실을 우선적으로 추출하세요.
        - 추출한 내용은 원문의 흐름을 유지하면서 간결하게 작성하세요.
        
        <기사>
        {article_text}
        </기사>
        """
        
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"사실 추출 AI 처리 오류: {e}")
        return f"AI 처리 중 오류가 발생했습니다: {str(e)}"

def neutralize_and_annotate_facts(facts_text):
    """추출된 사실에 중립적 관점의 주석 추가 및 편향성 완화
    
    Args:
        facts_text: 추출된 사실 텍스트
        
    Returns:
        주석이 추가된 중립적 텍스트
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        다음은 뉴스 기사에서 추출한 사실 정보입니다. 이 내용을 중립적 관점에서 분석하고 필요한 주석을 추가해주세요.
        
        요구사항:
        1. 편향된 표현이 있다면 더 중립적인 표현으로 대체하세요.
        2. 중요한 맥락이 생략되었다면 간결한 주석을 추가하세요.
        3. 필요한 경우 사실 관계를 명확히 하는 보충 정보를 추가하세요.
        4. 주석은 [주석: 내용] 형식으로 관련 문장 뒤에 추가하세요.
        5. 원문의 내용을 왜곡하지 말고, 중립성과 균형을 유지하세요.
        
        <추출된 사실>
        {facts_text}
        </추출된 사실>
        """
        
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"중립화 및 주석 AI 처리 오류: {e}")
        return f"AI 처리 중 오류가 발생했습니다: {str(e)}"

def summarize_for_readability(annotated_text):
    """주석이 추가된 내용을 가독성 높게 요약
    
    Args:
        annotated_text: 주석이 추가된 텍스트
        
    Returns:
        최종 요약본
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        prompt = f"""
        다음은 뉴스 기사에서 추출한 사실 정보와 주석입니다. 이 내용을 가독성 높은 형태로 요약해주세요.
        
        요구사항:
        1. 핵심 내용만 간결하게 요약하세요.
        2. 원문의 중요한 사실과 핵심 주석은 유지하세요.
        3. 문단 구분을 적절히 사용하여 가독성을 높이세요.
        4. 이해하기 쉬운 어휘와 문장 구조를 사용하세요.
        5. 최종 요약은 모바일 메신저로 읽기 적합하도록 구성하세요.
        
        <주석이 추가된 텍스트>
        {annotated_text}
        </주석이 추가된 텍스트>
        """
        
        response = model.generate_content(prompt)
        
        return response.text
    
    except Exception as e:
        print(f"요약 AI 처리 오류: {e}")
        return f"AI 처리 중 오류가 발생했습니다: {str(e)}"

def process_article(article_text):
    """기사 전체 처리 과정 (사실 추출 -> 중립화 및 주석 추가 -> 요약)
    
    Args:
        article_text: 기사 전체 내용 텍스트
        
    Returns:
        최종 처리된 요약본
    """
    try:
        # 1단계: 사실 추출
        facts = extract_facts_from_article(article_text)
        
        # 2단계: 중립화 및 주석 추가
        annotated = neutralize_and_annotate_facts(facts)
        
        # 3단계: 가독성 높은 요약
        summary = summarize_for_readability(annotated)
        
        return summary
    
    except Exception as e:
        print(f"기사 처리 오류: {e}")
        return f"기사 처리 중 오류가 발생했습니다: {str(e)}" 