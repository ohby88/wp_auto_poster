import os
import requests
import json
from dotenv import load_dotenv

def _get_jwt_token(wp_url: str, username: str, password: str) -> str:
    """JWT 토큰을 발급받습니다."""
    token_url = f"{wp_url}/wp-json/jwt-auth/v1/token"
    try:
        resp = requests.post(token_url, json={
            "username": username,
            "password": password
        }, timeout=15)
        if resp.status_code == 200:
            return resp.json().get("token")
        else:
            print(f"❌ JWT 토큰 발급 실패: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"❌ JWT 토큰 요청 중 오류: {e}")
        return None

def publish_post(title: str, content_file_path: str):
    """
    JWT 인증을 사용하여 워드프레스 REST API를 통해 포스트를 즉시 발행합니다.
    UTF-8 인코딩을 명시하여 한글 깨짐을 방지합니다.
    """
    load_dotenv()
    
    # 1. 환경변수에서 인증 정보 로드
    wp_url = os.getenv("WP_URL", "").rstrip('/')
    wp_username = os.getenv("WP_USERNAME")  
    wp_password = os.getenv("WP_PASSWORD")  # 일반 로그인 비밀번호 사용
    
    if not all([wp_url, wp_username, wp_password]):
        print("❌ 오류: .env 파일에서 WP_URL, WP_USERNAME, WP_PASSWORD를 확인해주세요.")
        return False
        
    api_url = f"{wp_url}/wp-json/wp/v2/posts"
    
    # 2. 본문 내용 읽기 (UTF-8 명시)
    try:
        with open(content_file_path, "r", encoding="utf-8") as file:
            content = file.read()
    except FileNotFoundError:
        print(f"❌ 오류: '{content_file_path}' 파일을 찾을 수 없습니다.")
        return False
    except Exception as e:
        print(f"❌ 파일 읽기 오류: {e}")
        return False
        
    # 3. JWT 토큰 발급 요청
    print(f"🔐 JWT 인증 토큰 발급 중...")
    token = _get_jwt_token(wp_url, wp_username, wp_password)
    if not token:
        print("❌ 인증을 진행할 수 없어 포스팅을 종료합니다.")
        return False
    
    # 4. 헤더 및 페이로드 설정 (UTF-8 인코딩 명시 및 Bearer 토큰)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "Accept": "application/json"
    }
    
    payload = {
        "title": title,
        "content": content,
        "status": "publish"  # 즉시 발행 설정
    }
    
    print(f"📤 워드프레스에 포스트 업로드 중... (제목: {title})")
    try:
        # 데이터가 안전하게 UTF-8로 전달되도록 명시적 인코딩 처리
        encoded_data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        
        response = requests.post(
            api_url, 
            headers=headers, 
            data=encoded_data, 
            timeout=30
        )
        
        # 응답 인코딩 설정
        response.encoding = 'utf-8'
        
        if response.status_code in (200, 201):
            post_info = response.json()
            print("✅ 워드프레스 포스트 발행 성공!")
            print(f"🔗 포스트 링크: {post_info.get('link')}")
            return True
        else:
            print(f"❌ 포스트 발행 실패! (상태 코드: {response.status_code})")
            print(f"👉 서버 메시지: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 요청 오류 발생: {e}")
        return False

if __name__ == "__main__":
    # 테스트용 마크다운/HTML 파일 생성 (UTF-8 명시)
    test_file = "test_content.html"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("<h1>자동화 포스팅 테스트</h1>\n<p>HTTPBasicAuth와 UTF-8 인코딩을 적용한 본문입니다.</p>")
        
    # 발행 실행
    publish_post("API 테스트: 즉시 발행 포스트", test_file)
