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
        logging.warning("No articles provided for generation.")
        return None
        
    # 모델 선택 (빠르고 저렴하며 컨텍스트 윈도우가 큰 gemini-1.5-flash 권장)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 기사 내용 포맷팅
        sources_text = ""
        for i, article in enumerate(articles):
            sources_text += f"\n[기사 {i+1}]\n"
            sources_text += f"제목: {article['title']}\n"
            sources_text += f"링크: {article['link']}\n"
            
            # 컨텍스트 길이 초과 방지를 위해 내용 잘라내기
            content_snippet = article.get('content', '')[:1000]
            sources_text += f"내용: {content_snippet}...\n"
            
        prompt = f"""
당신은 전문적인 IT 및 트렌드 전문 블로거입니다. 
다음 '{keyword}'와 관련된 최신 뉴스 기사들을 바탕으로, 독자들이 읽기 편하고 매력적인 블로그 포스팅을 작성해 주세요.

작성 가이드라인:
1. 결과물은 워드프레스 에디터에 바로 붙여넣기 할 수 있는 완전한 HTML 형식만 출력하세요. (```html 등 마크다운 코드 블록 제외, 순수 HTML 구조만 작성)
2. 글의 구성은 반드시 다음 요소들을 포함해야 합니다:
   - <h1> 매력적이고 시선을 끄는 제목 </h1>
   - 서론 (주제에 대한 흥미 유발 및 자연스러운 도입)
   - 본문 (제공된 기사의 핵심 내용을 종합하여 2~3개의 <h2> 소제목으로 나누어 체계적으로 설명)
   - 결론 및 요약 (본문 내용 정리 및 개인적인 인사이트 추가)
   - <h3> 참고 자료 </h3> (원문 기사 링크들을 <ul><li><a href="...">태그 형태로 나열)
3. 문체는 "~합니다", "~습니다.", "~일까요?" 와 같이 친근하면서도 신뢰감을 주는 존댓말 블로그 어투를 사용하세요.

다음은 요약 및 분석에 사용할 뉴스 데이터입니다:
{sources_text}
"""
        logging.info("Sending request to Gemini API...")
        response = model.generate_content(prompt)
        
        # 마크다운 코드 블록이 섞여나올 경우 제거
        html_content = response.text.replace('```html\n', '').replace('\n```', '').strip()
        if html_content.startswith('```'):
            html_content = html_content.replace('```', '').strip()
            
        # 제목을 H1 태그에서 파싱
        title_start = html_content.find("<h1>")
        title_end = html_content.find("</h1>")
        
        if title_start != -1 and title_end != -1:
            title = html_content[title_start+4:title_end].strip()
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
