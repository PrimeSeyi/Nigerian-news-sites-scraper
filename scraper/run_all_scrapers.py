import time
import csv
import uuid
import datetime
import os

# Import all 12 scrapers
from wp_api.punch_scraper import PunchScraper
from rss.premium_times_scraper import PremiumTimesScraper
from domain_structure.channels_scraper import ChannelsScraper
from domain_structure.legit_scraper import LegitScraper
from wp_api.daily_post_scraper import DailyPostScraper
from domain_structure.pulse_scraper import PulseScraper
from domain_structure.sahara_scraper import SaharaScraper
from wp_api.thisday_scraper import ThisDayScraper
from rss.arise_scraper import AriseScraper
from wp_api.businessday_scraper import BusinessDayApiScraper
from rss.thecable_scraper import TheCableScraper
from wp_api.dailytrust_scraper import DailyTrustScraper
from rss.vanguard_scraper import VanguardScraper
from rss.leadership_scraper import LeadershipScraper
from rss.tribune_scraper import TribuneScraper
from rss.channelstv_scraper import ChannelsTVRSSScraper

def main():
    print("=== NGN News Full Scraper ===")
    
    # Initialize all 12 scrapers
    scrapers = [
        PunchScraper(),
        PremiumTimesScraper(),
        ChannelsScraper(),
        LegitScraper(),
        DailyPostScraper(),
        PulseScraper(),
        SaharaScraper(),
        ThisDayScraper(),
        AriseScraper(),
        BusinessDayApiScraper(),
        TheCableScraper(),
        DailyTrustScraper(),
        VanguardScraper(),
        LeadershipScraper(),
        TribuneScraper(),
        ChannelsTVRSSScraper(),
        PremiumTimesScraper()
    ]
    
    # Ensure data directory exists
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"), exist_ok=True)
    csv_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"scraped_news_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    # Open CSV file for writing
    with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        # Write headers
        writer.writerow(['ID', 'UID', 'media_source', 'link', 'title', 'date_time'])
        
        global_id = 1
        
        # Iterate through each scraper
        for scraper in scrapers:
            site_name = scraper.__class__.__name__.lower().replace('scraper', '')
            print(f"\nFetching latest news from {site_name}...")
            
            # Get the latest links from Page 1 (Handle both signatures)
            try:
                links = scraper.get_latest_news_links(page_number=1)
            except TypeError:
                links = scraper.get_latest_news_links()
                
            print(f"-> Found {len(links)} links. Fetching metadata for the top 5...")
            
            # Extract metadata for the top 5 articles (can be increased later)
            for link in links[:5]:
                time.sleep(1) # Be polite
                
                # Handle both the old interface (extract_article_metadata) and new interface (parse_article)
                metadata = None
                if hasattr(scraper, 'extract_article_metadata'):
                    metadata = scraper.extract_article_metadata(link)
                    if metadata:
                        # Normalize keys for writer
                        metadata_normalized = {
                            'source': metadata.get('source', site_name),
                            'url': metadata.get('url', link),
                            'title': metadata.get('title', 'No Title'),
                            'date': metadata.get('published_date', 'No Date')
                        }
                elif hasattr(scraper, 'parse_article'):
                    metadata = scraper.parse_article(link)
                    if metadata:
                        metadata_normalized = {
                            'source': metadata.get('media_source', site_name),
                            'url': metadata.get('link', link),
                            'title': metadata.get('title', 'No Title'),
                            'date': metadata.get('date_time', 'No Date')
                        }

                if metadata and 'metadata_normalized' in locals():
                    uid = str(uuid.uuid4())
                    
                    # Write row to CSV
                    writer.writerow([
                        global_id,
                        uid,
                        metadata_normalized['source'],
                        metadata_normalized['url'],
                        metadata_normalized['title'],
                        metadata_normalized['date']
                    ])
                    print(f"   [+] Saved: {metadata_normalized['title'][:50]}...")
                    global_id += 1
                else:
                    print(f"   [-] Failed metadata extraction for: {link}")

    print(f"\n=== Scraping Complete: Saved {global_id - 1} articles to {csv_filename} ===")

    
if __name__ == "__main__":
    main()
