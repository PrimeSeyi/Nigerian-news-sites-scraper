from scraper_base import BaseNewsScraper
import re

class ThisDayScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://www.thisdaylive.com")
        self.news_url = "https://www.thisdaylive.com/category/nigeria"

    def get_latest_news_links(self, page_number: int):
        """
        Fetches article links from the RSS feed for flawless pagination.
        ThisDay RSS: https://www.thisdaylive.com/feed/?paged=N
        """
        import xml.etree.ElementTree as ET
        
        url = f"{self.base_url}/feed/?paged={page_number}"
            
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            links = []
            
            for item in root.findall('.//item'):
                link_elem = item.find('link')
                if link_elem is not None and link_elem.text:
                    link = link_elem.text.strip()
                    if "thisdaylive.com" in link and link not in links:
                        links.append(link)
                        
            return links
        except Exception as e:
            print(f"Error fetching RSS links for ThisDay: {e}")
            return []

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
            "source": "ThisDay",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = ThisDayScraper()
    scraper.run_standalone(max_pages=5)
