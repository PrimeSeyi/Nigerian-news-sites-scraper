import requests
import cloudscraper
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

class BaseNewsScraper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = cloudscraper.create_scraper()

    def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """Fetches the HTML content of a URL and returns a BeautifulSoup object."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_latest_news_links(self, page_number: int) -> List[str]:
        """
        Given a page number, returns a list of article URLs on that page.
        MUST BE IMPLEMENTED BY CHILD CLASS.
        """
        raise NotImplementedError("Child classes must implement get_latest_news_links")

    def extract_article_metadata(self, article_url: str) -> Dict[str, Any]:
        """
        Given an article URL, returns metadata (title, date, content snippet).
        MUST BE IMPLEMENTED BY CHILD CLASS.
        """
        raise NotImplementedError("Child classes must implement extract_article_metadata")

    def run_standalone(self, max_pages: int = 5):
        """Runs the scraper standalone and saves everything to a dedicated CSV."""
        import csv
        import os
        import uuid
        import time
        import datetime

        site_name = self.__class__.__name__.lower().replace('scraper', '')
        os.makedirs("data", exist_ok=True)
        execution_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_filename = f"data/{site_name}_data_{execution_time_str}.csv"
        
        all_metadata = []
        
        for page in range(1, max_pages + 1):
            print(f"[{site_name}] Fetching page {page}...")
            
            try:
                links = self.get_latest_news_links(page_number=page)
            except TypeError:
                links = self.get_latest_news_links() # For those that don't take page_number
                if page > 1:
                    print(f"[{site_name}] does not support pagination. Stopping at page 1.")
                    break
            
            if not links:
                print(f"[{site_name}] No links found on page {page}. Stopping.")
                break
                
            print(f"[{site_name}] Found {len(links)} links. Extracting metadata...")
            
            for link in links:
                time.sleep(1) # Be polite
                
                metadata = None
                if hasattr(self, 'extract_article_metadata'):
                    metadata = self.extract_article_metadata(link)
                    if metadata:
                        metadata_normalized = {
                            'source': metadata.get('source', site_name),
                            'url': metadata.get('url', link),
                            'title': metadata.get('title', 'No Title'),
                            'date': metadata.get('published_date', 'No Date')
                        }
                elif hasattr(self, 'parse_article'):
                    metadata = self.parse_article(link)
                    if metadata:
                        metadata_normalized = {
                            'source': metadata.get('media_source', site_name),
                            'url': metadata.get('link', link),
                            'title': metadata.get('title', 'No Title'),
                            'date': metadata.get('date_time', 'No Date')
                        }

                if metadata and 'metadata_normalized' in locals():
                    uid = str(uuid.uuid4())
                    all_metadata.append([
                        uid,
                        metadata_normalized['url'],
                        metadata_normalized['title'],
                        metadata_normalized['date'],
                        metadata_normalized['source']
                    ])
                    print(f"   [+] Fetched: {metadata_normalized['title'][:50]}...")
                else:
                    print(f"   [-] Failed metadata extraction for: {link}")
                    
        # Reverse to ensure oldest is first
        all_metadata.reverse()
        
        # Save to CSV
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['id', 'url', 'title', 'date_time', 'source'])
            for row in all_metadata:
                writer.writerow(row)
                
        print(f"\\n=== Finished! Saved {len(all_metadata)} articles to {csv_filename} ===")
