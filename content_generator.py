import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_gemini():
    """Gemini API 키를 설정합니다."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        logging.error("GEMINI_API_KEY is not set properly in .env")
        return False
    
    genai.configure(api_key=api_key)
    return True

def generate_blog_post(keyword, articles):
    """
    주어진 뉴스 기사들을 기반으로 워드프레스용 블로그 포스팅 HTML 콘텐츠를 생성합니다.
    """
    if not setup_gemini():
        return None
        
    if not articles:
        logging.info("No articles provided. Gemini will use its internal knowledge.")
        articles = []
        
    # 모델 선택 (빠르고 저렴하며 최신인 gemini-2.5-flash 권장)
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 기사 내용 포맷팅
        sources_text = ""
        if articles:
            for i, article in enumerate(articles):
                sources_text += f"\n[기사 {i+1}]\n"
                sources_text += f"제목: {article['title']}\n"
                sources_text += f"링크: {article['link']}\n"
                
                # 컨텍스트 길이 초과 방지를 위해 내용 잘라내기
                content_snippet = article.get('content', '')[:1000]
                sources_text += f"내용: {content_snippet}...\n"
        else:
            sources_text = "별도의 참고 기사가 제공되지 않았습니다. 당신의 최신 웹 지식 및 자체 정보를 활용하여 포스팅을 매우 자세고 정확하게 작성해주세요."
            
        prompt = f"""
당신은 월 수익 천만 원을 내는 최상위 SEO 전문 블로거입니다. 
제공된 주제 '{keyword}'와 뉴스 기사들을 바탕으로, 수익형 정보성 블로그와 완벽하게 동일한 구조와 스타일의 워드프레스 배포용 HTML 코드를 작성하세요.

[필수 구조 및 HTML/CSS 가이드라인]
1. 제목 영역 (눈에 띄는 박스 스타일):
   - 문서 최상단에 테두리가 있고 배경색이 들어간 박스로 감싼 <h1> 태그를 작성하세요.
   - 예: <div style="border: 2px solid #ff6b6b; padding: 20px; text-align: center; border-radius: 8px; margin-bottom: 20px; background-color: #fff8f8;"><h1 style="color: #333; margin: 0; font-size: 1.8em; font-weight: 800;">{keyword} 핵심 정리</h1></div>

2. 도입부 및 목차 (Table of Contents):
   - 독자의 묶어두기(체류시간 팽창)를 위해 해결책을 암시하는 흥미 유발 도입부를 2~3단락 작성하세요. 주요 키워드는 <strong>으로 강조하세요.
   - 글의 전개를 미리 알려주는 '목차(TOC)' 박스를 만드세요. 번호가 중복출력되지 않도록 <ul> 태그의 스타일을 지정하세요.
   - 예: <div style="background-color: #f8f9fa; padding: 15px 20px; border-radius: 8px; margin-bottom: 30px; border-left: 5px solid #007bff;"><h3 style="margin-top:0;">📝 이 글의 목차</h3><ul style="line-height: 1.6; list-style-type: none; padding-left: 0;"><li>1. ...</li><li>2. ...</li></ul></div>

3. 본문 구조 (소제목 + 내용 + 표 + CTA 버튼):
   - 각 본문 섹션은 '1. 소제목', '2. 소제목' 형태의 <h2> 태그로 시작하며, 시각적으로 매력적으로 스타일링하세요. (예: <h2 style="border-bottom: 2px solid #333; padding-bottom: 5px;">)
   - 복잡한 내용(특징, 비교, 장단점 등)이 있다면 반드시 한 눈에 들어오는 가독성 좋은 <table>(테이블) 태그로 깔끔하게 정리하세요. (테이블 헤더 <th>에는 회색 계열 배경색 적용)
   - 줄바꿈을 2~3문장마다 자주 하여 모바일 화면에서 숨막히지 않게 하세요. 불릿 포인트(<ul> <li>)를 적극 활용하세요.
   - 섹션 사이사이에 독자의 행동을 유도하는 눈에 띄는 CTA(Call to Action) 버튼을 최소 2곳 이상 배치하세요. 
   - [중요사항] CTA 버튼의 주소(href)에는 절대로 빈 링크나 '#'을 넣지 마세요. 제공된 뉴스 출처 링크나 해당 주제(키워드)와 관련된 공식 홈페이지(예: 정부24, 복지로, 공식 신청사이트 등)의 실제 존재할 가능성이 매우 높은 유효한 URL 주소를 만들어서 삽입하세요.
   - 버튼 예시: <div style="text-align: center; margin: 30px 0;"><a href="[실질적_참고_URL]" target="_blank" style="background-color: #ff4757; color: white; padding: 15px 30px; border-radius: 30px; text-decoration: none; font-weight: bold; font-size: 1.1em; display: inline-block; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">공식 신청 페이지 바로가기 ></a></div>

4. 강조 빛 형광펜 효과:
   - 핵심적인 문장이나 절대 놓치면 안 되는 혜택/결론 부분은 노란색 형광펜 효과(<span style="background-color: #fff0b3; font-weight: bold;">핵심 문장</span>)를 주어 시선을 사로잡으세요.

5. 결론 및 요약:
   - 마지막에 <h3 style="color: #ff4757;">💡 총평 및 요약</h3>을 만들어 3줄로 내용을 요약하세요.

오직 워드프레스 에디터(커스텀 HTML 블록)에 바로 복사/붙여넣기 할 수 있는 순수 HTML 태그 구조만 출력하세요. (```html 등의 마크다운 제외)

다음은 참고할 최신 뉴스 데이터입니다:
{sources_text}
"""
        logging.info("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        
        # 마크다운 코드 블록이 섞여나올 경우 제거
        html_content = response.text.replace('```html\n', '').replace('\n```', '').strip()
        if html_content.startswith('```'):
            html_content = html_content.replace('```', '').strip()
            
        import re
        
        # 제목을 H1 태그에서 파싱 (인라인 스타일 무시)
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html_content, re.IGNORECASE | re.DOTALL)
        
        if title_match:
            title = title_match.group(1).strip()
        else:
            title = f"[{keyword}] 최신 동향 및 뉴스 요약"
            
        return {
            "title": title,
            "content": html_content
        }
        
    except Exception as e:
        logging.error(f"Error during content generation: {e}")
        return None

if __name__ == "__main__":
    # 간단한 테스트
    logging.info("Testing content generator...")
    dummy_articles = [
        {"title": "AI 기술의 혁신적인 발전", "link": "http://example.com/1", "content": "인공지능 기술이 하루가 다르게 속도를 내며 발전하고 있습니다. 특히 언어 모델 분야에서 괄목할 성장이 두드러집니다."},
        {"title": "오픈AI 새로운 효율성 모델 발표", "link": "http://example.com/2", "content": "ChatGPT 개발사 오픈AI가 기존 대비 연산 효율성을 극대화한 새로운 AI 모델 아키텍처를 공개했습니다."}
    ]
    
    # 이 스크립트를 직접 실행하려면 .env 파일에 GEMINI_API_KEY가 세팅되어 있어야 합니다.
    result = generate_blog_post("AI 트렌드", dummy_articles)
    if result:
        print("\n--- Generated Post ---")
        print("Title:", result["title"])
        print("\nContent Snippet...")
        print(result["content"][:500])
