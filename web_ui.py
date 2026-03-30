import os
import logging
from flask import Flask, request, render_template_string
from dotenv import load_dotenv
import feedparser

from content_generator import generate_blog_post
from auto_pipeline import get_wp_token, publish_to_wp, generate_thumbnail, upload_media_to_wp

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>워드프레스 AI 포스팅 시스템</title>
    <style>
        body { font-family: 'Malgun Gothic', '맑은 고딕', sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .container { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 450px; text-align: center; }
        h1 { color: #333; margin-bottom: 30px; }
        input[type="text"] { width: 100%; padding: 15px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; box-sizing: border-box; }
        button { background-color: #ff4757; color: white; border: none; padding: 15px; width: 100%; border-radius: 5px; font-size: 18px; cursor: pointer; font-weight: bold; transition: background 0.3s; }
        button:hover { background-color: #ff6b81; }
        .message { margin-top: 20px; padding: 15px; border-radius: 5px; display: none; }
        .success { background-color: #d4edda; color: #155724; display: block; border: 1px solid #c3e6cb;}
        .trend-tag:hover { background-color: #d1d8dd; }
        .settings-btn { background: none; color: #888; border: none; font-size: 14px; text-decoration: underline; cursor: pointer; margin-bottom: 15px; text-align: left; display: block; padding: 0; }
        .settings-panel { display: none; text-align: left; background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #ddd; }
        .settings-panel input { width: 100%; padding: 10px; margin-top: 5px; margin-bottom: 10px; font-size: 13px; }
        .settings-panel label { font-size: 12px; font-weight: bold; color: #555; }
    </style>
    <script>
        function toggleSettings() {
            var panel = document.getElementById('settingsPanel');
            panel.style.display = (panel.style.display === 'block') ? 'none' : 'block';
        }
        function showLoading() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').innerText = 'AI가 글과 썸네일을 생성 중입니다... (약 1분 소요)';
            document.getElementById('loading').style.display = 'block';
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>🚀 워드프레스 자동 포스팅</h1>
        <p style="color: #666; margin-bottom: 20px;">원하는 주제를 입력하면 AI가 글과 썸네일을 만들고 바로 발행합니다.</p>
        
        <div class="trends" style="margin-bottom: 25px; text-align: left;">
            <p style="font-size: 13px; color: #888; margin-bottom: 10px; font-weight: bold;">🔥 오늘(실시간) 한국 구글 인기 검색어 (클릭 시 자동입력)</p>
            {% for t in trending_topics %}
                <span class="trend-tag" onclick="document.getElementById('topicInput').value='{{ t }}';" style="display: inline-block; background: #eef2f5; color: #333; padding: 6px 14px; border-radius: 20px; font-size: 13px; margin: 0 5px 8px 0; cursor: pointer; border: 1px solid #dcdcdc;">#{{ t }}</span>
            {% endfor %}
        </div>

        <form method="POST" onsubmit="showLoading()">
            <button type="button" class="settings-btn" onclick="toggleSettings()">⚙️ 환경설정 (API 키 및 계정 정보 입력)</button>
            <div id="settingsPanel" class="settings-panel">
                <p style="font-size: 12px; margin-top:0; color:#ff4757;">⚠️ 이 페이지를 공유받으셨다면, 본인의 정보를 입력하셔야 작동합니다.</p>
                <label>Gemini API Key</label>
                <input type="text" name="gemini_key" value="{{ env_gemini_key }}" placeholder="AIxxxxxxx...">
                <label>WordPress Site URL</label>
                <input type="text" name="wp_url" value="{{ env_wp_url }}" placeholder="http://myblog.com">
                <label>WordPress Admin Username</label>
                <input type="text" name="wp_user" value="{{ env_wp_user }}" placeholder="admin 아이디">
                <label>WordPress App Password</label>
                <input type="password" name="wp_pass" value="{{ env_wp_pass }}" placeholder="앱 비밀번호 24자리">
            </div>

            <input type="text" name="topic" id="topicInput" placeholder="발행할 주제 직접 입력 (예: 청년도약계좌 혜택)" required>
            <button type="submit" id="submitBtn">바로 워드프레스 발행하기</button>
        </form>
        <div id="loading" class="loading">⏳ 제미나이가 지식을 검색하여 글을 쓰는 중입니다...</div>
        {% if message %}
            <div class="message {{ status }}">{{ message|safe }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    # 인기 검색어 크롤링 (Google Trends RSS)
    trending_topics = []
    try:
        url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR"
        feed = feedparser.parse(url)
        trending_topics = [entry.title for entry in feed.entries[:10]] # 상위 10개만 추출
    except Exception as e:
        logging.error(f"Failed to fetch trends: {e}")
        trending_topics = ["2024년 청년도약계좌", "소상공인 지원금 신청", "애플 신제품 출시일", "해외여행 추천지"]

    load_dotenv()
    env_gemini_key = os.getenv("GEMINI_API_KEY", "")
    env_wp_url = os.getenv("WP_URL", "").rstrip('/')
    env_wp_user = os.getenv("WP_USERNAME", "")
    env_wp_pass = os.getenv("WP_PASSWORD", "")

    if request.method == "POST":
        topic = request.form.get("topic")
        gemini_api_key = request.form.get("gemini_key") or env_gemini_key
        wp_url = (request.form.get("wp_url") or env_wp_url).rstrip('/')
        wp_username = request.form.get("wp_user") or env_wp_user
        wp_password = request.form.get("wp_pass") or env_wp_pass
        
        if not topic:
            return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, env_gemini_key=env_gemini_key, env_wp_url=env_wp_url, env_wp_user=env_wp_user, env_wp_pass=env_wp_pass, message="주제를 입력해주세요.", status="error")
            
        if not gemini_api_key or not wp_password:
            return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, env_gemini_key=env_gemini_key, env_wp_url=env_wp_url, env_wp_user=env_wp_user, env_wp_pass=env_wp_pass, message="환경설정에서 API 키와 워드프레스 정보를 모두 입력해주세요.", status="error")
        
        # Override environment variables temporarily for this request's logic inside content_generator and auto_pipeline
        os.environ["GEMINI_API_KEY"] = gemini_api_key
        try:
            # 1. 제미나이 내용 생성 (articles가 None이면 내장 지식으로 생성하도록 수정됨)
            logging.info(f"UI Trigger: Generating post for '{topic}'")
            # None 대신 빈 리스트나 None을 넘겨서 자체 검색 유도
            generated_data = generate_blog_post(topic, articles=[])
            
            if not generated_data:
                return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, message="제미나이 텍스트 생성에 실패했습니다.", status="error")
                
            title = generated_data['title']
            body_html = generated_data['content']
            
            # 2. WP 로그인
            token = get_wp_token(wp_url, wp_username, wp_password)
            if not token:
                return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, message="워드프레스 로그인에 실패했습니다. API 설정을 확인하세요.", status="error")
                
            # 3. 텍스트 썸네일 생성 및 업로드
            logging.info("Generating text thumbnail...")
            image_path = generate_thumbnail(gemini_api_key, topic)
            media_id = None
            if image_path:
                logging.info("Uploading thumbnail to WP...")
                media_id, img_url = upload_media_to_wp(wp_url, token, image_path)
                
            # 4. 발행
            logging.info("Publishing to WordPress...")
            success = publish_to_wp(wp_url, token, title, body_html, media_id=media_id)
            
            if success:
                msg = f"🎉 <b>성공적으로 발행되었습니다!</b><br><br>작성된 글 제목:<br>[ {title} ]<br><br><a href='{wp_url}' target='_blank' style='color:#007bff; text-decoration:none;'>👉 내 워드프레스 확인 가기</a>"
                return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, env_gemini_key=env_gemini_key, env_wp_url=env_wp_url, env_wp_user=env_wp_user, env_wp_pass=env_wp_pass, message=msg, status="success")
            else:
                return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, env_gemini_key=env_gemini_key, env_wp_url=env_wp_url, env_wp_user=env_wp_user, env_wp_pass=env_wp_pass, message="워드프레스 발행 중 오류가 발생했습니다.", status="error")
                
        except Exception as e:
            return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, env_gemini_key=env_gemini_key, env_wp_url=env_wp_url, env_wp_user=env_wp_user, env_wp_pass=env_wp_pass, message=f"에러 발생: {str(e)}", status="error")

    return render_template_string(HTML_TEMPLATE, trending_topics=trending_topics, env_gemini_key=env_gemini_key, env_wp_url=env_wp_url, env_wp_user=env_wp_user, env_wp_pass=env_wp_pass)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
