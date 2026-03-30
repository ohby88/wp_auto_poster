import os
import time
import json
import base64
import requests
import schedule
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import textwrap

# ==========================================
# ⚙️ 1. 환경 설정 및 JWT 인증 (워드프레스 로그인)
# ==========================================
def get_wp_token(wp_url, username, password):
    """
    워드프레스 JWT 플러그인을 사용하여 인증 토큰을 받아옵니다.
    반환값: 성공 시 토큰 문자열, 실패 시 None
    """
    token_url = f"{wp_url}/wp-json/jwt-auth/v1/token"
    try:
        resp = requests.post(token_url, json={"username": username, "password": password}, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("token")
        else:
            print(f"❌ [에러] JWT 토큰 발급 실패: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"❌ [에러] 워드프레스 연결 실패: {e}")
        return None


# ==========================================
# 📝 2. 블로그 내용 자동 생성 (Claude API)
# ==========================================
def generate_blog_content(api_key, theme):
    """
    Anthropic (Claude 3.5) API를 사용하여 주제, 제목, 본문을 자동 생성합니다.
    """
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # 💡 [수정 포인트] Claude 프롬프트를 변경하여 글의 어투나 스타일을 바꿀 수 있습니다.
    system_prompt = "당신은 한국 최고의 SEO 블로그 포스팅 전문가입니다."
    user_prompt = f"""
    블로그 테마: '{theme}'
    위 테마와 관련된 블로그 포스트를 작성해 주세요. 
    1. 사람들의 이목을 끄는 구체적인 첫 번째 '주제'를 선택하세요.
    2. 검색엔진에 최적화되고 눈길을 사로잡는 매력적인 '제목'을 생성하세요.
    3. HTML 구조로 작성된 '본문(content)'을 생성하세요. (서론, 3개 이상의 <h2> 소제목과 단락, 결론 포함)
       본문 삽입용 이미지는 추가하지 마세요. (썸네일은 다른 AI가 전담합니다.)

    아래 JSON 형식에 맞추어 답변해주시고, 다른 텍스트는 절대 출력하지 마세요.
    {{
      "topic": "주제",
      "title": "제목",
      "content": "<h2>...</h2> HTML 본문"
    }}
    """
    
    payload = {
        # 더 높은 품질을 원하시면 "claude-3-5-sonnet-20241022"로 변경하세요.
        "model": "claude-3-haiku-20240307", 
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            text = response.json()['content'][0]['text'].strip()
            # 마크다운 코드블록 제거
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("\n", 1)[0]
            
            data = json.loads(text)
            return data
        else:
            print(f"❌ [에러] 내용 생성 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ [에러] Claude API 오류: {e}")
        return None


# ==========================================
# 🎨 3. 텍스트 썸네일 자동 생성 (Pillow)
# ==========================================
def generate_thumbnail(api_key, topic_keyword, output_filename="thumbnail.png"):
    """
    Pillow를 사용하여 수익형 블로그 스타일의 깔끔한 텍스트 썸네일 이미지를 생성합니다.
    """
    width, height = 1080, 1080
    background_color = (255, 255, 255)
    img = Image.new('RGB', (width, height), color=background_color)
    draw = ImageDraw.Draw(img)
    
    # 두꺼운 빨간색 테두리
    border_width = 40
    border_color = (235, 69, 95) # 눈에 띄는 빨간색 계열
    border_padding = 40
    draw.rectangle([border_padding, border_padding, width-border_padding, height-border_padding], outline=border_color, width=border_width)
    
    # 폰트 로드 (윈도우 맑은 고딕 볼드)
    try:
        font_path = "C:\\Windows\\Fonts\\malgunbd.ttf"
        title_font = ImageFont.truetype(font_path, 110)
    except:
        title_font = ImageFont.load_default()
        
    # 텍스트 줄바꿈 (너무 길면 자르기)
    wrapper = textwrap.TextWrapper(width=12)
    lines = wrapper.wrap(text=topic_keyword)
    
    # 텍스트 수직 중앙 정렬 계산
    line_spacing = 40
    # getbbox returns (left, top, right, bottom)
    line_heights = [title_font.getbbox(line)[3] - title_font.getbbox(line)[1] for line in lines]
    total_text_height = sum(line_heights)
    total_height = total_text_height + (len(lines) - 1) * line_spacing
    
    y_text = (height - total_height) / 2
    
    for i, line in enumerate(lines):
        bbox = title_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x_text = (width - line_width) / 2
        # 글꼴 색상: 검정
        draw.text((x_text, y_text), line, font=title_font, fill=(30, 30, 30))
        y_text += line_heights[i] + line_spacing
        
    img.save(output_filename, format="PNG")
    print(f"🎨 텍스트 썸네일 생성 완료: {output_filename}")
    return output_filename


# ==========================================
# ☁️ 4. 워드프레스 미디어 라이브러리에 썸네일 업로드
# ==========================================
def upload_media_to_wp(wp_url, token, image_path):
    """
    생성된 썸네일 이미지를 워드프레스 서버에 업로드하고 미디어 ID를 반환합니다.
    """
    media_url = f"{wp_url}/wp-json/wp/v2/media"
    
    # 워드프레스에 파일 업로드 시 필요한 헤더 설정
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
        "Content-Type": "image/jpeg"
    }
    
    try:
        with open(image_path, "rb") as f:
            response = requests.post(media_url, headers=headers, data=f, timeout=60)
            
        if response.status_code in (200, 201):
            data = response.json()
            media_id = data.get('id')
            source_url = data.get('source_url')
            print(f"☁️ 미디어 업로드 성공! (미디어 ID: {media_id})")
            return media_id, source_url
        else:
            print(f"❌ [에러] 미디어 업로드 실패: {response.text}")
            return None, None
    except Exception as e:
        print(f"❌ [에러] 미디어 업로드 네트워크 오류: {e}")
        return None, None



# ==========================================
# 📰 5-B. 뉴스 기반 추천 주제 생성 (AI + 뉴스 RSS)
# ==========================================
def get_news_based_recommendations(api_key, num_topics=5):
    """
    한국 주요 뉴스 RSS를 크롤링하여 수집한 헤드라인을 Gemini에 넘기고,
    독자 유입이 폭발할 만한 수익형 블로그 주제를 추천받습니다.
    """
    import feedparser
    import re
    import google.generativeai as genai

    # 한국 주요 뉴스 RSS 피드 목록
    rss_feeds = [
        "https://www.yonhapnewstv.co.kr/rss",
        "https://feeds.feedburner.com/yonhap-news",
        "https://rss.etnews.com/Section901.xml",   # 전자신문 IT
        "https://www.mk.co.kr/rss/30000001/",      # 매경 경제
        "https://news.kbs.co.kr/rss/rss_news.xml", # KBS 뉴스
    ]

    headlines = []
    seen = set()
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                title = entry.get('title', '').strip()
                if title and title not in seen:
                    seen.add(title)
                    headlines.append(title)
                if len(headlines) >= 40:
                    break
        except Exception as e:
            print(f"  RSS 수집 실패: {feed_url} -> {e}")
        if len(headlines) >= 40:
            break

    # RSS 실패 시 Google Trends 폴백
    if len(headlines) < 5:
        try:
            import requests as req
            r = req.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR",
                        headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            feed = feedparser.parse(r.content)
            for entry in feed.entries[:15]:
                if entry.title not in seen:
                    headlines.append(entry.title)
        except Exception:
            pass

    if not headlines:
        return []

    headlines_text = "\n".join(f"- {h}" for h in headlines[:40])

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""당신은 한국 최고의 SEO 수익형 블로그 전문가입니다.
아래는 지금 한국에서 이슈가 되고 있는 최신 뉴스 헤드라인입니다.

{headlines_text}

이 중에서 정보성 블로그(생활 정보, 복지, 금융, IT, 건강, 절약 등)로 작성했을 때
독자 유입(검색량, 클릭률)이 가장 폭발적으로 나올 만한 블로그 주제 {num_topics}개를
검색하기 좋은 구체적인 문장 형태로 제안해주세요.

형식: 각 주제를 쉼표(,)로만 구분. 다른 말은 절대 금지.
예시: 2026년 청년도약계좌 신청 방법, 전국민 에너지바우처 신청 기간 및 금액, ...
"""
        response = model.generate_content(prompt)
        topics = [t.strip() for t in response.text.split(',') if t.strip()]
        return topics[:num_topics]
    except Exception as e:
        print(f"❌ AI 주제 추천 실패: {e}")
        return []


import re as _re

# ==========================================
# 🔗 5-A. CTA 링크 유효성 검증 & 자동 제거
# ==========================================
def validate_cta_links(html_content, timeout=5):
    """
    HTML 본문 내 모든 <a href="..."> 링크를 실제 HTTP 요청으로 확인합니다.
    - 접속 불가 (4xx, 5xx, 타임아웃)인 링크가 포함된 CTA 버튼 <div>를 자동 삭제합니다.
    - 유효한 링크는 그대로 유지합니다.
    """
    import re
    import requests as req

    # 패턴: href="...." 에서 URL 추출 (단순 '#' 제외)
    href_pattern = re.compile(r'href=["\']([^"\'#][^"\']*)["\']', re.IGNORECASE)
    urls = href_pattern.findall(html_content)
    
    dead_urls = set()
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; LinkValidator/1.0)'}
    
    for url in urls:
        if not url.startswith('http'):
            continue
        try:
            resp = req.head(url, allow_redirects=True, timeout=timeout, headers=headers)
            if resp.status_code >= 400:
                # HEAD 실패 시 GET으로 재시도
                resp = req.get(url, allow_redirects=True, timeout=timeout, headers=headers, stream=True)
                if resp.status_code >= 400:
                    dead_urls.add(url)
                    print(f"❌ [링크 검증] 접속 불가 ({resp.status_code}): {url}")
            else:
                print(f"✅ [링크 검증] 정상 ({resp.status_code}): {url}")
        except Exception as e:
            dead_urls.add(url)
            print(f"❌ [링크 검증] 연결 실패: {url} -> {e}")
    
    if not dead_urls:
        print("✅ [링크 검증] 모든 CTA 링크가 유효합니다.")
        return html_content

    # 死링크가 포함된 <a> 태그를 텍스트로 변환 (버튼 스타일 div도 함께 제거)
    cleaned_html = html_content
    for dead_url in dead_urls:
        # CTA 버튼 패턴: <div style="text-align:center..."><a href="dead_url"...>...</a></div>
        # 또는 단순 <a href="dead_url"...>...</a>
        # div 감싸기 패턴 먼저 시도
        div_pattern = re.compile(
            r'<div[^>]*text-align[^>]*center[^>]*>[\s]*<a[^>]*href=["\']' + re.escape(dead_url) + r'["\'][^>]*>.*?</a>[\s]*</div>',
            re.IGNORECASE | re.DOTALL
        )
        cleaned_html, n = div_pattern.subn('', cleaned_html)
        if n == 0:
            # div 패턴 없으면 단순 <a> 태그 제거
            a_pattern = re.compile(
                r'<a[^>]*href=["\']' + re.escape(dead_url) + r'["\'][^>]*>.*?</a>',
                re.IGNORECASE | re.DOTALL
            )
            cleaned_html = a_pattern.sub('', cleaned_html)
        print(f"🗑️  [링크 검증] 죽은 링크 제거 완료: {dead_url}")

    return cleaned_html


# ==========================================
# 🚀 5. 워드프레스 포스트 최종 발행
# ==========================================
def publish_to_wp(wp_url, token, title, content, media_id=None):
    """
    작성된 제목, 본문, 그리고 특성 이미지(썸네일)를 워드프레스에 즉시 발행합니다.
    """
    api_url = f"{wp_url}/wp-json/wp/v2/posts"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8"
    }
    
    payload = {
        "title": title,
        "content": content,
        "status": "publish"  # 즉시 발행 (임시저장은 "draft"로 변경)
    }
    
    # 썸네일 ID가 존재하면 포스트의 '특성 이미지'로 등록
    if media_id:
        payload["featured_media"] = media_id
        
    try:
        encoded_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        response = requests.post(api_url, headers=headers, data=encoded_data, timeout=30)
        
        if response.status_code in (200, 201):
            post_link = response.json().get('link')
            print(f"✅ 글 발행 완료! 링크: {post_link}")
            return True
        else:
            print(f"❌ [에러] 글 발행 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ [에러] 포스트 발행 중 예외 발생: {e}")
        return False


# ==========================================
# 🔄 메인 자동화 파이프라인 (스케줄러에서 실행됨)
# ==========================================
def run_auto_poster():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔥 블로그 자동 포스팅 파이프라인 시작 🔥")
    
    # 환경변수 로드
    load_dotenv()
    wp_url = os.getenv("WP_URL", "").rstrip('/')
    wp_username = os.getenv("WP_USERNAME")
    wp_password = os.getenv("WP_PASSWORD")
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    blog_theme = os.getenv("BLOG_THEME", "온라인 부업")
    
    if not all([wp_url, wp_username, wp_password, claude_api_key, gemini_api_key]):
        print("❌ [환경설정 오류] .env 파일에 필요한 모든 정보가 기입되었는지 확인해주세요.")
        return

    # [1단계] 워드프레스 인증
    print("▶ 1. 워드프레스 로그인 진행 중...")
    token = get_wp_token(wp_url, wp_username, wp_password)
    if not token:
        return
        
    # [2단계] Claude로 글 생성
    print(f"▶ 2. Claude AI 텍스트 생성 중... (주제: {blog_theme})")
    content_data = generate_blog_content(claude_api_key, blog_theme)
    if not content_data:
        return
        
    topic = content_data.get('topic', '블로그')
    title = content_data.get('title', '자동 생성 블로그 글')
    body_html = content_data.get('content', '<p>내용이 없습니다.</p>')
    print(f"  - 선정된 주제: {topic}")
    print(f"  - 생성된 제목: {title}")
    
    # [3단계] Gemini로 썸네일 생성
    print("▶ 3. Gemini AI 썸네일 이미지 생성 중...")
    image_path = generate_thumbnail(gemini_api_key, topic)
    media_id = None
    
    # (선택) 썸네일이 성공적으로 만들어졌다면 워드프레스에 업로드
    if image_path:
        print("▶ 4. 워드프레스 미디어 라이브러리에 이미지 업로드 중...")
        media_id, img_url = upload_media_to_wp(wp_url, token, image_path)
    
    # [4단계] 글 최종 발행
    print("▶ 5. 워드프레스에 최종 포스팅 중...")
    publish_to_wp(wp_url, token, title, body_html, media_id=media_id)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 파이프라인 1사이클 종료.\n")


# ==========================================
# ⏰ 실행 진입점 (6시간마다 반복)
# ==========================================
if __name__ == "__main__":
    # 처음 스크립트를 켜면 즉시 한 번 실행하게 하려면 아래의 주석을 푸세요 
    # run_auto_poster()
    
    # 💡 [수정 포인트] 숫자를 변경하여 원하는 주기(hours, minutes, days)로 변경할 수 있습니다.
    schedule.every(6).hours.do(run_auto_poster)
    
    print("=======================================")
    print("⏳ 블로그 자동 포스팅 스케줄러 가동 중...")
    print("⏳ 6시간마다 파이프라인이 자동 실행됩니다.")
    print("⏳ (터미널을 끄면 스케줄러도 종료됩니다.)")
    print("=======================================")
    
    while True:
        schedule.run_pending()
        time.sleep(60) # 1분마다 스케줄 확인
