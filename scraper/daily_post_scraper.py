from scraper_base import BaseNewsScraper

class DailyPostScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://dailypost.ng")
        # Daily Post uses a structured JSON API for their archive/category pagination
        # category 1 is usually news/general. 
        self.api_url = "https://dailypost.ng/wp-json/wp/v2/posts"

    def get_latest_news_links(self, page_number: int):
        """
        Fetches the news using the WP JSON API.
        """
        # We can pass ?page=N
        url = f"{self.api_url}?page={page_number}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            links = []
            for post in data:
                if 'link' in post:
                    links.append(post['link'])
            return links
        except Exception as e:
            print(f"API Error fetching {url}: {e}")
            return []

    def extract_article_metadata(self, article_url: str):
        """
        We still fetch the HTML for the article to get the full title and date,
        or we could modify get_latest_news_links to return the JSON dict directly,
        but to keep the BaseNewsScraper interface consistent, we fetch HTML here.
        """
        soup = self.fetch_html(article_url)
        if not soup:
            return None
            
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else soup.title.string if soup.title else 'No title'
        
        date_meta = soup.find('meta', property='article:published_time')
        published_date = date_meta['content'] if date_meta else None
        
        return {
            "source": "Daily Post",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = DailyPostScraper()
    scraper.run_standalone(max_pages=5)
