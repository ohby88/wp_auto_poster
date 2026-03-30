import os
import re
import datetime
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
        
    # 최신 모델로 업데이트 (더 깊이 있는 응답 생성)
    try:
        model = genai.GenerativeModel(
            'gemini-2.5-pro-preview-03-25',
            generation_config={
                "temperature": 1.0,
                "max_output_tokens": 8192
            }
        )
        
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
당신은 대한민국 최고의 SEO 정보성 블로거이며, 10년 경력의 콘텐츠 마케터입니다.
아래 주제로 블로그 글을 워드프레스에 바로 발행 가능한 HTML 형식으로 작성해 주세요.

주제: {keyword}
오늘 날짜: {__import__('datetime').date.today().strftime('%Y년 %m월 %d일')}

[글 작성 지침 - 반드시 준수]

★ 글 퀄리티 요구사항:
- 분량: 최소 2,000자 이상의 풍부하고 실용적인 정보를 담아주세요.
- 전문성: 해당 주제의 전문가처럼 구체적인 숫자(금액, %, 날짜, 기간 등)와 실제 사례를 들어서 설명하세요.
- 독창성: 다른 블로그에서 볼 수 없는 핵심 꿀팁과 주의사항을 반드시 포함하세요.
- SEO: 제목에 핵심 키워드를 포함하고, 자연스럽게 키워드를 본문에 반복하여 검색 최적화를 달성하세요.
- 신뢰성: 독자가 이 글 하나만 읽어도 해당 주제에 대해 완벽하게 이해할 수 있도록 작성하세요.

★ HTML 구조 (아래 형식 엄수):

1. 제목 박스:
<div style="border: 3px solid #ff6b6b; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 25px; background: linear-gradient(135deg, #fff8f8, #fff);"><h1 style="color: #c0392b; margin: 0; font-size: 1.9em; font-weight: 900; line-height: 1.4;">[제목 작성]</h1></div>

2. 핵심요약 박스 (독자 체류시간 증가):
<div style="background: #fff3cd; border-left: 6px solid #ffc107; padding: 18px 22px; border-radius: 6px; margin-bottom: 25px;"><b>⚡ 이 글의 핵심 요약</b><ul style="margin: 8px 0 0 0; padding-left: 20px; line-height: 2;"><li>포인트 1</li><li>포인트 2</li><li>포인트 3</li></ul></div>

3. 클릭 유도 도입부 (2~3문단): 독자의 공감을 이끌어내는 상황 묘사 → 이 글이 해결책임을 암시

4. 목차 TOC:
<div style="background: #f0f4ff; padding: 18px 22px; border-radius: 8px; margin: 25px 0; border-left: 5px solid #3498db;"><h3 style="margin-top: 0; color: #2c3e50;">📋 목차</h3><ul style="line-height: 2; padding-left: 20px; margin: 0;"><li>1. ...</li><li>2. ...</li></ul></div>

5. 본문 섹션 (최소 5개 이상 H2 소제목):
<h2 style="background: linear-gradient(to right, #3498db, #5dade2); color: white; padding: 12px 18px; border-radius: 6px; font-size: 1.2em;">1. 소제목</h2>
- 각 섹션마다 반드시 구체적인 수치, 사례, 또는 팁을 담아야 합니다.
- 비교·정리가 필요할 때는 스타일이 적용된 HTML 테이블 사용:
<table style="width:100%; border-collapse:collapse; margin: 15px 0;"><thead><tr style="background:#2c3e50; color:white;"><th style="padding:10px; text-align:left;">항목</th><th style="padding:10px;">내용</th></tr></thead><tbody><tr style="background:#f9f9f9;"><td style="padding:10px; border:1px solid #ddd;">...</td><td style="padding:10px; border:1px solid #ddd;">...</td></tr></tbody></table>
- 형광펜 강조: <span style="background: linear-gradient(to right, #fff176, #ffee58); padding: 2px 5px; font-weight: bold;">핵심 수치나 조건</span>
- 주의사항 박스: <div style="background:#fff0f0; border:1px solid #ffcccc; padding:14px; border-radius:6px; margin:15px 0;">⚠️ <b>주의사항</b>: ...</div>

6. 중간 CTA 버튼 (섹션 중간에 최소 2곳):
<div style="text-align:center; margin:30px 0;"><a href="[해당 주제 공식 관련 URL - 정부24, 복지로 등 실제 가능성 높은 URL로]" target="_blank" style="background: linear-gradient(135deg, #e74c3c, #c0392b); color:white; padding:16px 35px; border-radius:30px; text-decoration:none; font-weight:bold; font-size:1.1em; box-shadow:0 4px 15px rgba(231,76,60,0.4); display:inline-block;">🔴 공식 신청하러 가기 ▶</a></div>

7. 결론 요약 박스:
<div style="background: linear-gradient(135deg, #667eea, #764ba2); color:white; padding:22px; border-radius:10px; margin:30px 0;"><h3 style="margin-top:0;">💡 총정리 및 핵심 행동 지침</h3><p style="line-height:1.8; margin:0;">...</p></div>

8. FAQ 섹션 (자주 묻는 질문 3~5개):
<h2 style="...와 동일 스타일">❓ 자주 묻는 질문 (FAQ)</h2>
<details style="border:1px solid #ddd; border-radius:6px; padding:12px; margin-bottom:10px;"><summary style="cursor:pointer; font-weight:bold;">Q. 질문 내용</summary><p style="margin:8px 0 0; color:#555;">A. 상세 답변</p></details>

[절대 금지사항]
- ```html 마크다운 블록 사용 금지
- href="#" 같은 빈 링크 사용 금지  
- 주제와 무관한 일반적 내용 작성 금지
- 짧고 성의없는 답변 금지

참고 데이터:
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
