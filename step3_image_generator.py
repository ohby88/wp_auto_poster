import os
import requests
import json
from dotenv import load_dotenv

def generate_blog_image_with_gemini(topic_keyword: str, output_filename: str = "blog_image.png"):
    """
    Google Gemini (Imagen) API를 사용하여 블로그용 이미지를 생성합니다.
    사용자가 제공한 SEO 블로그 이미지 생성 프롬프트를 바탕으로 이미지를 생성합니다.
    """
    load_dotenv()
    
    # .env 파일에 GEMINI_API_KEY 가 먼저 필요합니다.
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ 오류: .env 파일에 GEMINI_API_KEY가 설정되어 있지 않습니다.")
        print("구글 AI Studio에서 API 키를 발급받아 추가해주세요.")
        return None

    # 프롬프트 파일 읽기
    try:
        with open("gemini_image_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
    except Exception as e:
        print(f"❌ 프롬프트 파일을 읽을 수 없습니다: {e}")
        system_prompt = "블로그에 쓸 고품질의 깔끔한 이미지를 하나 생성해줘."

    # Gemini에게 전달할 최종 프롬프트 조합
    final_prompt = f"{system_prompt}\n\n[요청 주제]: {topic_keyword}"

    print(f"🎨 Gemini를 통해 '{topic_keyword}' 관련 블로그 이미지를 생성 중입니다...")

    # 주의: Gemini 라이브러리의 최신 버전(google-genai)을 사용하거나 
    # v1beta REST API의 predict 엔드포인트를 사용해 Imagen 모델 호출
    # 여기서는 REST API 방식 예시를 작성합니다. (Gemini 1.5 Pro/Flash는 텍스트 모델이므로 
    # 이미지 생성에는 별도의 Imagen 엔드포인트가 필요할 수 있으나, 
    # 최근 통합된 Gemini 구조에 맞춘 로직입니다.)
    
    # 구글 Imagen 3 API 엔드포인트 설정 (gemini API의 경우)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={api_key}"
    
    payload = {
        "instances": [
            {"prompt": final_prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9", # 기본값 16:9 요청
            "outputOptions": {
                "mimeType": "image/jpeg"
            }
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result_data = response.json()
            predictions = result_data.get("predictions", [])
            
            if predictions and "bytesBase64Encoded" in predictions[0]:
                import base64
                image_data = base64.b64decode(predictions[0]["bytesBase64Encoded"])
                
                with open(output_filename, "wb") as f:
                    f.write(image_data)
                
                print(f"✅ 이미지 생성 완료! '{output_filename}'로 저장되었습니다.")
                return output_filename
            else:
                print("❌ API 응답에 이미지 데이터가 없습니다.")
                print(response.text)
                return None
        else:
            print(f"❌ API 호출 실패 (상태 코드: {response.status_code})")
            print(f"👉 서버 메시지: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 네트워크 또는 처리 오류 발생: {e}")
        return None

if __name__ == "__main__":
    # 테스트 실행
    print("Gemini 이미지 생성 스크립트 테스트")
    generate_blog_image_with_gemini("온라인 부업으로 돈 버는 직장인", "test_gemini_image.jpg")
