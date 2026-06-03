import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rss.arise_scraper import AriseScraper
from rss.leadership_scraper import LeadershipScraper
from rss.premium_times_scraper import PremiumTimesScraper
from rss.thecable_scraper import TheCableScraper
from rss.tribune_scraper import TribuneScraper
from rss.vanguard_scraper import VanguardScraper
from rss.channelstv_scraper import ChannelsTVRSSScraper

def main():
    print("=== NGN News RSS Feed Scrapers ===")
    print("Initializing RSS scrapers...")
    
    scrapers = [
        AriseScraper(),
        LeadershipScraper(),
        PremiumTimesScraper(),
        TheCableScraper(),
        TribuneScraper(),
        VanguardScraper(),
        ChannelsTVRSSScraper()
    ]
    
    print(f"Loaded {len(scrapers)} RSS scrapers.")
    print("Starting full RSS data extraction...")
    print("-" * 50)
    
    for scraper in scrapers:
        print(f"\n>>> Running {scraper.__class__.__name__}...")
        try:
            scraper.run_standalone(max_pages=20)
        except Exception as e:
            print(f"!!! Error running {scraper.__class__.__name__}: {e}")
            
    print("\n" + "="*50)
    print("All RSS Feed Scrapes Completed Successfully!")
    print("="*50)

if __name__ == "__main__":
    main()
