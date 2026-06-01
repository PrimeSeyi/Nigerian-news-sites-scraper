import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper

import re

class SaharaScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://saharareporters.com")
        self.news_url = "https://saharareporters.com/news"

    def get_latest_news_links(self, page_number: int):
        page_index = page_number - 1
        if page_index == 0:
            url = f"{self.news_url}"
        else:
            url = f"{self.news_url}?page={page_index}"
            
        soup = self.fetch_html(url)
        if not soup:
            return []
            
        links = []
        articles = soup.find_all('a')
        for a_tag in articles:
            href = a_tag.get('href')
            # Sahara reporters puts date in URL like /2026/05/30/
            if href and re.search(r'/\d{4}/\d{2}/\d{2}/', href):
                if href.startswith("/"):
                    href = self.base_url + href
                if href not in links and "saharareporters.com" in href:
                    links.append(href)
                    
        return links

    def extract_article_metadata(self, article_url: str):
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
        
        if not published_date:
            date_meta = soup.find('meta', property='article:published_time')
            published_date = date_meta['content'] if date_meta else None
        
        return {
            "source": "Sahara Reporters",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = SaharaScraper()
    scraper.run_standalone(max_pages=5)
