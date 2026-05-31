from scraper_base import BaseNewsScraper

class PulseScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://www.pulse.ng")
        self.news_url = "https://www.pulse.ng/news/local"

    def get_latest_news_links(self, page_number: int):
        """
        Pulse uses ?page={N} or infinite load. Typically ?page=N works.
        """
        if page_number == 1:
            url = f"{self.news_url}"
        else:
            url = f"{self.news_url}?page={page_number}"
            
        soup = self.fetch_html(url)
        if not soup:
            return []
            
        links = []
        articles = soup.find_all('a')
        for a_tag in articles:
            href = a_tag.get('href')
            if href and "/story/" in href and href not in links:
                if href.startswith('http'):
                    links.append(href)
                else:
                    links.append(self.base_url + href)
                    
        return links

    def extract_article_metadata(self, article_url: str):
        soup = self.fetch_html(article_url)
        if not soup:
            return None
            
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else soup.title.string if soup.title else 'No title'
        
        date_meta = soup.find('meta', property='article:published_time')
        published_date = date_meta['content'] if date_meta else None
        
        return {
            "source": "Pulse",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = PulseScraper()
    scraper.run_standalone(max_pages=5)
