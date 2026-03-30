import os
import logging
from dotenv import load_dotenv

from crawler import get_news_data
from content_generator import generate_blog_post
from wp_poster import post_to_wordpress

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_pipeline():
    """
    뉴스 크롤링 -> AI 콘텐츠 생성 -> 워드프레스 포스팅 과정을 실행합니다.
    """
    load_dotenv()
    keywords_str = os.getenv("KEYWORDS", "AI, 인공지능")
    
    # 1. 크롤링 대상 키워드 파싱
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    logging.info(f"Target keywords: {keywords}")
    
    for kw in keywords:
        logging.info(f"\n{'='*50}\nProcessing keyword: {kw}\n{'='*50}")
        
        # 2. 뉴스 검색 및 크롤링
        logging.info("Step 1/3: Crawling news...")
        articles = get_news_data(kw, max_articles_per_keyword=3)
        
        if not articles:
            logging.warning(f"No articles found for '{kw}'. Skipping...")
            continue
            
        logging.info(f"Crawled {len(articles)} articles.")
        
        # 3. Gemini 명세에 따라 컨텐츠 생성
        logging.info("Step 2/3: Generating content with Gemini AI...")
        generated_data = generate_blog_post(kw, articles)
        
        if not generated_data:
            logging.error(f"Content generation failed for '{kw}'. Skipping...")
            continue
            
        logging.info("Content generated successfully. Title: " + generated_data['title'])
        
        # 4. 워드프레스에 업로드
        logging.info("Step 3/3: Posting to WordPress...")
        
        # 기본은 draft 유지, 환경변수 POST_STATUS가 publish면 즉시 발행
        post_status = os.getenv("POST_STATUS", "draft") 
        
        success = post_to_wordpress(
            title=generated_data['title'],
            content=generated_data['content'],
            status=post_status
        )
        
        if success:
            logging.info(f"Pipeline completed successfully for '{kw}'!")
        else:
            logging.error(f"Pipeline failed at posting stage for '{kw}'.")

if __name__ == "__main__":
    logging.info("Starting WP Auto Poster Pipeline...")
    run_pipeline()
    logging.info("All tasks finished.")
