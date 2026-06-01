import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper

class PunchScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://punchng.com")
        self.news_url = "https://punchng.com/topics/news"

    def get_latest_news_links(self, page_number: int):
        """
        Fetches the news list page and extracts article URLs.
        Punch uses /topics/news/page/{N}/
        """
        if page_number == 1:
            url = self.news_url
        else:
            url = f"{self.news_url}/page/{page_number}/"
            
        soup = self.fetch_html(url)
        if not soup:
            return []
            
        links = []
        # Punch articles on list page are typically in <article> tags or have specific post classes
        articles = soup.find_all('article')
        for article in articles:
            a_tag = article.find('a')
            if a_tag and a_tag.get('href'):
                href = a_tag.get('href')
                if href not in links and "punchng.com" in href:
                    links.append(href)
                    
        return links

    def extract_article_metadata(self, article_url: str):
        """
        Extracts metadata using standard meta tags.
        """
        soup = self.fetch_html(article_url)
        if not soup:
            return None
            
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else soup.title.string if soup.title else 'No title'
        
        # Punch uses article:published_time 
        date_meta = soup.find('meta', property='article:published_time')
        published_date = date_meta['content'] if date_meta else None
        
        return {
            "source": "Punch",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = PunchScraper()
    scraper.run_standalone(max_pages=1)
