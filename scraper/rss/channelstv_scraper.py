import cloudscraper
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper
import time

class ChannelsTVRSSScraper(BaseNewsScraper):
    def __init__(self):
        super().__init__("https://www.channelstv.com")
        self.news_url = "https://www.channelstv.com"
        self.rss_url = "https://www.channelstv.com/feed/?paged=1"
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        }

    def get_latest_news_links(self, limit=5):
        """Fetches latest news links using the RSS feed."""
        links = []
        try:
            response = self.scraper.get(self.rss_url, headers=self.headers)
            if response.status_code == 200:
                root = ET.fromstring(response.text)
                
                # Each news article is inside an <item> tag in RSS
                items = root.findall('.//item')
                for item in items[:limit]:
                    link_elem = item.find('link')
                    if link_elem is not None and link_elem.text:
                        links.append(link_elem.text.strip())
            else:
                print(f"Failed to fetch Channels TV RSS RSS feed. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error fetching Channels TV RSS links: {e}")
            
        return links

    def extract_article_metadata(self, url):
        """Fetches and extracts metadata from an article."""
        article_data = {
            "title": "No Title",
            "date_time": "No Date",
            "category": "News",
            "content": "",
            "link": url,
            "subdomain": self.get_subdomain(url),
            "media_source": "Channels TV"
        }
        
        try:
            response = self.scraper.get(url, headers=self.headers)
            if response.status_code != 200:
                print(f"Failed to fetch Channels TV RSS article: {url}")
                return article_data
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Title
            title_tag = soup.find('h1', class_='entry-title')
            if title_tag:
                article_data['title'] = title_tag.text.strip()
                
            # Date
            date_tag = soup.find('time', class_='entry-date')
            if date_tag and date_tag.has_attr('datetime'):
                article_data['date_time'] = date_tag['datetime']
            elif date_tag:
                article_data['date_time'] = date_tag.text.strip()
                
            # Category
            cat_tag = soup.find('span', class_='cat-links')
            if cat_tag:
                article_data['category'] = cat_tag.text.strip()
                
        except Exception as e:
            print(f"Error parsing Channels TV RSS article {url}: {e}")
            
        time.sleep(1) # Be polite
        return article_data

    def get_subdomain(self, url):
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if hostname:
                parts = hostname.split('.')
                if len(parts) >= 3 and parts[0] != 'www':
                    return parts[0]
                elif len(parts) >= 3 and parts[0] == 'www':
                    return 'www'
            return 'unknown'
        except:
            return 'unknown'
