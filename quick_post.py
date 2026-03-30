import os
import logging
from dotenv import load_dotenv
from content_generator import generate_blog_post
from auto_pipeline import get_wp_token, publish_to_wp, generate_thumbnail, upload_media_to_wp

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_quick_post():
    load_dotenv()
    
    keyword = "2024년 청년도약계좌 및 청년내일저축계좌 자격 조건과 혜택 완벽 정리"
    dummy_articles = [
        {"title": "청년도약계좌 가입 대상 및 혜택", "link": "http://example.com/1", "content": "만 19세~34세 이하 청년 중 개인소득 7500만원 이하, 가구소득 중위 180% 이하인 경우 가입 가능하며 정부 기여금 혜택이 주어집니다."},
        {"title": "청년내일저축계좌 신청 방법", "link": "http://example.com/2", "content": "단독가구 기준 월 10만원 저축 시 정부가 10만원을 추가 매칭해주는 제도로 복지로 웹사이트에서 온라인 신청이 가능합니다."}
    ]
    
    logging.info(f"Generating content using Gemini API for keyword: {keyword}...")
    # Use gemini to write the blog post
    generated_data = generate_blog_post(keyword, dummy_articles)
    
    if not generated_data:
        logging.error("Content generation failed.")
        return
        
    logging.info(f"Generated text post. Title: {generated_data['title']}")
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    wp_url = os.getenv("WP_URL", "").rstrip('/')
    wp_username = os.getenv("WP_USERNAME")
    wp_password = os.getenv("WP_PASSWORD")
    
    token = get_wp_token(wp_url, wp_username, wp_password)
    if not token:
        logging.error("Failed to get WP JWT token.")
        return
        
    logging.info("Generating thumbnail using Gemini Imagen 4...")
    image_path = generate_thumbnail(gemini_api_key, keyword)
    media_id = None
    
    body_html = generated_data['content']
    title = generated_data['title']
    
    if image_path:
        logging.info("Uploading thumbnail to WordPress...")
        media_id, img_url = upload_media_to_wp(wp_url, token, image_path)

    success = publish_to_wp(wp_url, token, title, body_html, media_id=media_id)
    
    if success:
        logging.info("Post with Image in the middle published successfully!")
    else:
        logging.error("Failed to publish post.")

if __name__ == "__main__":
    run_quick_post()
