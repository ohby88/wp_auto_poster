import feedparser
import requests
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_google_news_rss(keyword, limit=5):
    """
    Google News RSS를 검색하여 특정 키워드에 대한 최신 뉴스 링크와 제목을 가져옵니다.
    """
    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(url)
    
    articles = []
    for entry in feed.entries[:limit]:
        articles.append({
            'title': entry.title,
            'link': entry.link,
            'published': entry.get('published', '')
        })
    return articles

def fetch_article_content(url):
    """
    뉴스 기사 URL에 접속하여 본문 텍스트를 추출합니다.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Google News RSS 링크는 보통 리다이렉션을 포함함
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 본문 내용을 담고 있을 확률이 높은 태그들을 탐색
        paragraphs = soup.find_all('p')
        text = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        return text
    except Exception as e:
        logging.error(f"Error fetching content from {url}: {e}")
        return ""

def get_news_data(keywords_str, max_articles_per_keyword=3):
    """
    여러 키워드에 대해 뉴스를 검색하고 내용을 가져옵니다.
    """
    if not keywords_str:
        return []
        
    keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
    all_news = []
    
    for kw in keywords:
        logging.info(f"Crawling news for keyword: '{kw}'")
        articles = get_google_news_rss(kw, limit=max_articles_per_keyword)
        
        for article in articles:
            logging.info(f"Fetching content for: {article['title']}")
            content = fetch_article_content(article['link'])
            time.sleep(1.5) # 과도한 요청 방지
            
            if content:
                article['content'] = content
                article['keyword'] = kw
                all_news.append(article)
            else:
                logging.warning(f"Failed to extract content for '{article['title']}'")
                
    return all_news

if __name__ == "__main__":
    # 간단한 테스트
    logging.info("Testing crawler...")
    news = get_news_data("인공지능", max_articles_per_keyword=2)
    for idx, n in enumerate(news):
        print(f"\n--- Article {idx+1} ---")
        print(f"Keyword: {n['keyword']}")
        print(f"Title: {n['title']}")
        print(f"Link: {n['link']}")
        print(f"Content snippet: {n['content'][:200]}...")
