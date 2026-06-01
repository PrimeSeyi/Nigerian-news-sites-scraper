import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper

class LegitScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://www.legit.ng")
        self.news_url = "https://www.legit.ng/latest"

    def get_latest_news_links(self, page_number: int):
        """
        Fetches the news list page and extracts article URLs.
        Legit uses ?page={N}
        """
        if page_number == 1:
            url = f"{self.news_url}/"
        else:
            url = f"{self.news_url}/?page={page_number}"
            
        soup = self.fetch_html(url)
        if not soup:
            return []
            
        links = []
        articles = soup.find_all('article')
        for article in articles:
            a_tag = article.find('a')
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href')
                if href not in links and "legit.ng" in href:
                    links.append(href)
                    
        return links

    def extract_article_metadata(self, article_url: str):
        """
        Extracts metadata.
        """
        soup = self.fetch_html(article_url)
        if not soup:
            return None
            
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else soup.title.string if soup.title else 'No title'
        
        # Legit uses article:published_time or <time> tag
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            published_date = date_meta['content']
        else:
            time_tag = soup.find('time')
            published_date = time_tag['datetime'] if time_tag and time_tag.has_attr('datetime') else None
        
        return {
            "source": "Legit.ng",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = LegitScraper()
    scraper.run_standalone(max_pages=1)
