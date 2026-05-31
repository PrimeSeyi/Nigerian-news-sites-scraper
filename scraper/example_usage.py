import time
from punch_scraper import PunchScraper
from channels_scraper import ChannelsScraper
from daily_post_scraper import DailyPostScraper

def main():
    print("=== NGN News Scraper Demo ===")
    
    # 1. Initialize the scrapers you want to use
    scrapers = [
        PunchScraper(),
        ChannelsScraper(),
        DailyPostScraper()
    ]
    
    all_articles = []
    
    # 2. Iterate through each scraper
    for scraper in scrapers:
        print(f"\\nFetching latest news from {scraper.__class__.__name__}...")
        
        # 3. Get the latest links (just Page 1 for this example)
        links = scraper.get_latest_news_links(page_number=1)
        print(f"-> Found {len(links)} links. Fetching metadata for the top 3...")
        
        # 4. Extract metadata for the top 3 articles
        for link in links[:3]:
            # Be polite to the servers: add a small delay between requests
            time.sleep(1)
            
            metadata = scraper.extract_article_metadata(link)
            if metadata:
                all_articles.append(metadata)
                print(f"   [+] {metadata['title'][:50]}... ({metadata['published_date']})")
            else:
                print(f"   [-] Failed to extract metadata for {link}")

    print(f"\\n=== Demo Complete: Aggregated {len(all_articles)} articles ===")
    
if __name__ == "__main__":
    main()
