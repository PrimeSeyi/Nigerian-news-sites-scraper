import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from domain_structure.channels_scraper import ChannelsScraper
from domain_structure.legit_scraper import LegitScraper
from domain_structure.pulse_scraper import PulseScraper
from domain_structure.sahara_scraper import SaharaScraper

def main():
    print("=== NGN News Domain Structure / HTML Scrapers ===")
    print("Initializing domain structure scrapers...")
    
    scrapers = [
        ChannelsScraper(),
        LegitScraper(),
        PulseScraper(),
        SaharaScraper()
    ]
    
    print(f"Loaded {len(scrapers)} domain structure scrapers.")
    print("Starting full structural data extraction...")
    print("-" * 50)
    
    for scraper in scrapers:
        print(f"\n>>> Running {scraper.__class__.__name__}...")
        try:
            # Domain scrapers usually rely on standalone logic since they don't have the API loop
            scraper.run_standalone(max_pages=20)
        except Exception as e:
            print(f"!!! Error running {scraper.__class__.__name__}: {e}")
            
    print("\n" + "="*50)
    print("All Domain Structure Scrapes Completed Successfully!")
    print("="*50)

if __name__ == "__main__":
    main()
