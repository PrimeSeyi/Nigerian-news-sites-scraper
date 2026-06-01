import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper
import datetime
import re

class ChannelsScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://www.channelstv.com")
        self.news_url = "https://www.channelstv.com/category/local"

    def get_latest_news_links(self, page_number: int):
        """
        Fetches all news for a specific day.
        page_number=1 means today, page_number=2 means yesterday, etc.
        """
        days_ago = page_number - 1
        target_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        date_str = target_date.strftime("%Y/%m/%d")
        
        all_links = []
        current_page = 1
        
        print(f"[channels] Scanning all articles for date: {date_str}...")
        
        while True:
            if current_page == 1:
                url = f"{self.base_url}/{date_str}/"
            else:
                url = f"{self.base_url}/{date_str}/page/{current_page}/"
                
            soup = self.fetch_html(url)
            if not soup:
                break
                
            page_links = []
            articles = soup.find_all('article')
            for article in articles:
                a_tag = article.find('a')
                if a_tag and a_tag.get('href'):
                    href = a_tag.get('href')
                    if href not in page_links and "channelstv.com" in href:
                        page_links.append(href)
            
            if not page_links:
                break
                
            for link in page_links:
                if link not in all_links:
                    all_links.append(link)
                    
            print(f"   -> Found {len(page_links)} links on {date_str} (Page {current_page})")
            current_page += 1
            
        return all_links

    def extract_article_metadata(self, article_url: str):
        """
        Extracts metadata. For Channels, we can extract the date from the URL directly!
        URL format: https://www.channelstv.com/2026/05/30/article-title/
        """
        # Try to extract date from URL
        date_match = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', article_url)
        published_date = None
        if date_match:
            year, month, day = date_match.groups()
            published_date = f"{year}-{month}-{day}"
        
        soup = self.fetch_html(article_url)
        if not soup:
            return None
            
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else soup.title.string if soup.title else 'No title'
        
        # If date isn't in URL, fallback to meta
        if not published_date:
            date_meta = soup.find('meta', property='article:published_time')
            published_date = date_meta['content'] if date_meta else None
        
        return {
            "source": "Channels TV",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = ChannelsScraper()
    scraper.run_standalone(max_pages=5)
