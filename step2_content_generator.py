import os
import json
import requests
from dotenv import load_dotenv

def generate_blog_post():
    """
    Anthropic (Claude) API를 통해 블로그 포스트를 자동으로 생성합니다.
    사용자의 요청대로:
    1. 주제 선택
    2. 제목 생성
    3. 글 생성 (서론, 3~4개 소제목/본론, 관련 그림 추가)
    단계를 거쳐 결과물을 반환합니다.
    """
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    theme = os.getenv("BLOG_THEME", "IT 및 기술 트렌드")
    
    if not api_key:
        print("❌ 오류: .env 파일에 ANTHROPIC_API_KEY가 설정되어 있지 않습니다.")
        return None
        
    print(f"🤖 '{theme}' 테마를 바탕으로 AI가 글을 작성하기 시작합니다...")
    
    # Claude API 엔드포인트 및 헤더
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    # 프롬프트: 사용자가 요청한 단계별 처리 및 HTML 포맷 요구, 이미지 추가 방법 명시
    system_prompt = "당신은 SEO에 최적화된 블로그 포스팅 전문가입니다."
    user_prompt = f"""
    블로그 테마: '{theme}'
    위 테마와 관련된 블로그 포스트를 작성해 주세요. 아래 단계(1~3)를 반드시 순차적으로 따르고, 최종 결과물은 제공된 JSON 포맷에 맞게만 출력하세요.

    [단계 1] 테마와 관련된 사람들의 이목을 끄는 구체적인 첫 번째 '주제'를 선택하세요.
    [단계 2] 1단계에서 선택한 주제를 바탕으로 검색엔진에 최적화되고 눈길을 사로잡는 매력적인 '제목'을 생성하세요.
    [단계 3] 2단계의 제목에 맞춰 HTML 구조로 작성된 '본문(content)'을 생성하세요. 본문의 규칙은 다음과 같습니다:
      - 서론 (한 문단 이상)
      - 본론: 3~4개의 소제목(<h2>)과 각각에 대한 구체적인 내용(<p>)
      - 결론 (마무리 멘트)
      - 관련 그림 추가: 본문의 적절한 위치에 최소 1개 이상의 관련된 이미지를 삽입하세요.
        이미지는 무료 AI 이미지 생성 API인 pollinations를 활용합니다.
         예시 형태: <img src="https://image.pollinations.ai/prompt/영어로_된_이미지_묘사?width=800&height=400&nologo=true" alt="이미지 설명" style="max-width:100%; border-radius:8px;">

    아래 JSON 형식에 맞추어 답변해주시고, JSON 이외의 다른 텍스트는 출력하지 마세요.

    {{
      "topic": "1단계에서 선택된 주제",
      "title": "2단계에서 생성된 제목",
      "content": "3단계에서 생성된 전체 HTML 본문 코드가 들어갑니다. (줄바꿈이나 따옴표 등에 유의하여 유효한 JSON 문자열로 작성하세요)"
    }}
    """
    
    payload = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result_json = response.json()
            message_content = result_json['content'][0]['text']
            
            # 클로드가 마크다운 코드블록(```json ... ```)으로 감싸서 리턴하는 경우 대비
            if message_content.startswith("```json"):
                message_content = message_content.replace("```json", "").replace("```", "").strip()
            elif message_content.startswith("```"):
                message_content = message_content.replace("```", "").strip()
                
            data = json.loads(message_content)
            print("\n✅ 블로그 콘텐츠 생성이 완료되었습니다!")
            print(f"- 선택된 주제: {data.get('topic')}")
            print(f"- 생성된 제목: {data.get('title')}")
            
            return data
            
        else:
            print(f"❌ API 호출 실패 (상태 코드: {response.status_code})")
            print(f"👉 서버 메시지: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 요청 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: 반환된 결과가 올바른 JSON 형식이 아닙니다. ({e})")
        print(f"응답 원본: {message_content}")
        return None

if __name__ == "__main__":
    result = generate_blog_post()
    if result:
        # 생성된 HTML 콘텐츠를 파일로 임시 저장 (테스트용)
        test_file = "generated_post.html"
        with open(test_file, "w", encoding="utf-8") as f:
            # 워드프레스 포스팅할 때 제목이 본문에 중복되지 않도록 본문만 저장
            f.write(result['content'])
        print(f"\n📂 생성된 본문이 '{test_file}' 파일에 저장되었습니다.")
