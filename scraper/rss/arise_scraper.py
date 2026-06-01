import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper

import xml.etree.ElementTree as ET

class AriseScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://www.arise.tv")

    def get_latest_news_links(self, page_number: int):
        """
        Fetches links using the RSS feed to bypass HTML pagination overlap.
        """
        url = f"{self.base_url}/feed/?paged={page_number}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            root = ET.fromstring(response.text)
            links = []
            
            for item in root.findall('.//item'):
                link_elem = item.find('link')
                if link_elem is not None and link_elem.text:
                    link = link_elem.text.strip()
                    if "arise.tv" in link and link not in links:
                        links.append(link)
                        
            return links
            
        except Exception as e:
            print(f"Error fetching links from {self.name}: {e}")
            return []

    def extract_article_metadata(self, article_url: str):
        soup = self.fetch_html(article_url)
        if not soup:
            return None
            
        title_meta = soup.find('meta', property='og:title')
        title = title_meta['content'] if title_meta else soup.title.string if soup.title else 'No title'
        
        date_meta = soup.find('meta', property='article:published_time')
        if not date_meta:
            date_meta = soup.find('meta', property='og:article:published_time')
        published_date = date_meta['content'] if date_meta else None
        
        return {
            "source": "Arise News",
            "url": article_url,
            "title": title,
            "published_date": published_date
        }

if __name__ == "__main__":
    scraper = AriseScraper()
    print("Testing AriseScraper - Fetching Page 1 Links")
    links = scraper.get_latest_news_links(1)
    print(f"Found {len(links)} links on page 1.")
    
    if links:
        print(f"\\nTesting metadata extraction for: {links[0]}")
        meta = scraper.extract_article_metadata(links[0])
        print(meta)
