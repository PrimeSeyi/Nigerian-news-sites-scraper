import sys
import os
import argparse
import datetime
import re
import concurrent.futures
import time
from log_utils import log_execution

def timed_domain_run(scraper, name, **kwargs):
    start = time.time()
    try:
        res = scraper.run_standalone(**kwargs)
        duration = time.time() - start
        log_execution("DOMAIN", name, duration)
        return res
    except Exception as exc:
        duration = time.time() - start
        log_execution("DOMAIN", name, duration, error=str(exc))
        raise exc

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from domain_structure.channels_scraper import ChannelsScraper
from domain_structure.legit_scraper import LegitScraper
from domain_structure.pulse_scraper import PulseScraper
from domain_structure.sahara_scraper import SaharaScraper

def parse_time_filter(time_str):
    if not time_str:
        return None
    match = re.match(r'^(\d+)([hHdD])$', time_str.strip())
    if not match:
        print(f"Warning: Invalid time format '{time_str}'. Expected formats like '1h', '24h', '1d'. Ignoring time filter.")
        return None
        
    value = int(match.group(1))
    unit = match.group(2).lower()
    
    if unit == 'h':
        delta = datetime.timedelta(hours=value)
    elif unit == 'd':
        delta = datetime.timedelta(days=value)
        
    return datetime.datetime.now(datetime.timezone.utc) - delta

def main():
    parser = argparse.ArgumentParser(description="Unified Domain Structure News Scraper")
    parser.add_argument("-m", "--manual", action="store_true", help="Run in manual mode (saves as manual_ prefix)")
    parser.add_argument("-t", "--time", type=str, help="Time limit filter (e.g., '1h', '24h', '1d')")
    parser.add_argument("--site", type=str, default="all", help="Specify a site to scrape or 'all'")
    args = parser.parse_args()

    time_threshold = parse_time_filter(args.time)

    print("=== NGN News Domain Structure / HTML Scrapers ===")
    print(f"Manual Mode: {args.manual}")
    print(f"Time Threshold: {time_threshold if time_threshold else 'None (Full Scrape)'}")
    print("Initializing domain structure scrapers...")
    
    all_scrapers = {
        "legit": LegitScraper(),
        "pulse": PulseScraper(),
        "sahara": SaharaScraper()
    }
    
    if args.site != "all":
        if args.site.lower() not in all_scrapers:
            print(f"Error: Site '{args.site}' not recognized for Domain Scrapers. Valid options: {list(all_scrapers.keys())} or 'all'")
            return
        scrapers_to_run = [all_scrapers[args.site.lower()]]
    else:
        scrapers_to_run = list(all_scrapers.values())
    
    print(f"Loaded {len(scrapers_to_run)} domain structure scrapers.")
    print("Starting full structural data extraction with max_workers=3...")
    print("-" * 50)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(timed_domain_run, scraper, scraper.__class__.__name__, max_pages=100, time_threshold=time_threshold, is_manual=args.manual): scraper.__class__.__name__ for scraper in scrapers_to_run}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                future.result()
            except Exception as e:
                print(f"!!! Error running {name}: {e}")
            
    print("\n" + "="*50)
    print("All Domain Structure Scrapes Completed Successfully!")
    print("="*50)

if __name__ == "__main__":
    main()
