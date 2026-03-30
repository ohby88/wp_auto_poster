import os
import requests
import base64
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def post_to_wordpress(title, content, status="draft"):
    """
    워드프레스 REST API를 통해 포스트를 작성합니다.
    status: 'publish' (즉시 발행) 또는 'draft' (임시 저장)
    """
    load_dotenv()
    
    wp_url = os.getenv("WP_URL")
    wp_user = os.getenv("WP_USER")
    wp_app_password = os.getenv("WP_APP_PASSWORD")
    
    if not all([wp_url, wp_user, wp_app_password]) or wp_app_password == "your_application_password_here":
        logging.error("WordPress credentials are not set properly in .env")
        return False
        
    # 워드프레스 REST API URL 구성
    wp_url = wp_url.rstrip('/')
    api_url = f"{wp_url}/wp-json/wp/v2/posts"
    
    # 인증 토큰 생성
    credentials = f"{wp_user}:{wp_app_password}"
    token = base64.b64encode(credentials.encode()).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': 'application/json'
    }
    
    # 워드프레스 포스트 데이터
    data = {
        'title': title,
        'content': content,
        'status': status
    }
    
    try:
        logging.info(f"Uploading post to WordPress '{wp_url}' (Status: {status})")
        response = requests.post(api_url, headers=headers, json=data, timeout=15)
        
        if response.status_code == 201:
            post_id = response.json().get('id')
            post_link = response.json().get('link')
            logging.info(f"Successfully posted! Post ID: {post_id}, Link: {post_link}")
            return True
        else:
            logging.error(f"Failed to post. Status Code: {response.status_code}, Response: {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error during WordPress uploading: {e}")
        return False

if __name__ == "__main__":
    # 간단한 테스트
    logging.info("Testing WP Poster...")
    test_title = "API 테스트 임시저장 포스트"
    test_content = "<h1>테스트</h1><p>이것은 워드프레스 자동화 테스트입니다.</p>"
    
    # 이 스크립트를 직접 실행하려면 .env 파일에 올바른 워드프레스 정보가 세팅되어 있어야 합니다.
    post_to_wordpress(test_title, test_content, status="draft")
