import cloudscraper
import xml.etree.ElementTree as ET
import csv
import json
import os
import datetime
from urllib.parse import urlparse
import time
import argparse
import re

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
STATE_FILE = os.path.join(DATA_DIR, "deep_scraper_states.json")

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
MAX_ROWS_PER_FILE = 300
MAX_PAGES = 200

# Supported RSS sites
SITES = {
    "thecable": "https://www.thecable.ng",
    "arise": "https://www.arise.tv",
    "vanguard": "https://www.vanguardngr.com",
    "leadership": "https://leadership.ng",
    "tribune": "https://tribuneonlineng.com",
    "premiumtimes": "https://www.premiumtimesng.com"
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=4)

def get_subdomain(url):
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname:
            parts = hostname.split('.')
            if len(parts) >= 3:
                return parts[0]
        return 'unknown'
    except:
        return 'unknown'

def get_current_csv_info(site_name, today_str):
    """Finds the active CSV file for today and its current row count for a specific site."""
    base_name = os.path.join(DATA_DIR, f"{site_name}_rss_{today_str}")
    
    # Check base file
    filename = f"{base_name}.csv"
    if not os.path.exists(filename):
        return filename, 0
        
    with open(filename, 'r') as f:
        count = sum(1 for line in f) - 1 # exclude header
        
    if count < MAX_ROWS_PER_FILE:
        return filename, max(0, count)
        
    # Check suffixed files
    suffix = 1
    while True:
        filename = f"{base_name}-{suffix:02d}.csv"
        if not os.path.exists(filename):
            return filename, 0
        with open(filename, 'r') as f:
            count = sum(1 for line in f) - 1
        if count < MAX_ROWS_PER_FILE:
            return filename, max(0, count)
        suffix += 1

def run_deep_scraper_for_site(site_name, base_url, global_state, today_str):
    print(f"\\n=== Deep Scraping {site_name.upper()} ===")
    
    # Initialize state for site if it doesn't exist
    if site_name not in global_state:
        global_state[site_name] = {
            "last_seen_guid": None,
            "date": None,
            "today_count": 0
        }
        
    site_state = global_state[site_name]
    
    # Reset stats if it's a new day
    if site_state.get("date") != today_str:
        site_state["date"] = today_str
        site_state["today_count"] = 0

    execution_time_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    scraper = cloudscraper.create_scraper()
    
    first_guid_this_run = None
    stop_scraping = False
    new_rows_count = 0
    all_articles = []

    for page in range(1, MAX_PAGES + 1):
        if stop_scraping:
            break
            
        print(f"[{site_name}] Fetching page {page}...")
        url = f"{base_url}/feed/?paged={page}"
        try:
            response = scraper.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch page {page}. Status: {response.status_code}")
                break
                
            root = ET.fromstring(response.text)
            items = root.findall('.//item')
            
            if not items:
                print("No items found. Reached end of feed.")
                break
                
            for item in items:
                guid_elem = item.find('guid')
                
                # Fallback to 'link' if 'guid' is completely missing
                if guid_elem is not None and guid_elem.text:
                    guid = guid_elem.text.strip()
                else:
                    link_elem_fallback = item.find('link')
                    guid = link_elem_fallback.text.strip() if link_elem_fallback is not None else None
                
                if not guid:
                    continue
                    
                # Stop if we hit the last remembered GUID from a previous run
                if guid == site_state.get("last_seen_guid"):
                    print(f"-> Encountered last remembered GUID ({guid}). Stopping delta scrape.")
                    stop_scraping = True
                    break
                    
                # Save the very first GUID we process so we can remember it for tomorrow
                if first_guid_this_run is None:
                    first_guid_this_run = guid
                    
                # Extract other fields
                title_elem = item.find('title')
                title = title_elem.text.strip() if title_elem is not None else "No Title"
                
                link_elem = item.find('link')
                link = link_elem.text.strip() if link_elem is not None else ""
                
                date_elem = item.find('pubDate')
                pub_date = date_elem.text.strip() if date_elem is not None else ""
                
                categories = [c.text for c in item.findall('category') if c.text]
                category_str = ", ".join(categories)
                
                subdomain = get_subdomain(link)
                
                # Collect item in memory instead of writing to CSV immediately
                all_articles.append([category_str, title, link, guid, pub_date, subdomain])
                    
        except Exception as e:
            print(f"Error parsing page {page}: {e}")
            break
            
        time.sleep(1)

    # Now that we have all articles for this run, reverse them so oldest comes first
    all_articles.reverse()
    
    current_file_rows = 0
    file_suffix = 0
    f = None
    writer = None
    
    def open_new_file(suffix):
        nonlocal current_file_rows
        # Base name with execution timestamp instead of just date
        filename = os.path.join(DATA_DIR, f"{site_name}_rss_{execution_time_str}")
        if suffix > 0:
            filename = f"{filename}-{suffix:02d}.csv"
        else:
            filename = f"{filename}.csv"
            
        new_f = open(filename, mode='w', newline='', encoding='utf-8')
        new_writer = csv.writer(new_f)
        new_writer.writerow(['category', 'title', 'link', 'guid', 'date_time', 'subdomain'])
        current_file_rows = 0
        return new_f, new_writer

    if all_articles:
        f, writer = open_new_file(file_suffix)
        
        for row in all_articles:
            if current_file_rows >= MAX_ROWS_PER_FILE:
                f.close()
                file_suffix += 1
                f, writer = open_new_file(file_suffix)
                
            writer.writerow(row)
            current_file_rows += 1
            site_state["today_count"] += 1
            new_rows_count += 1
            
        if f:
            f.close()
            
        time.sleep(1)

    # Update state only if we actually processed new items
    if first_guid_this_run is not None:
        site_state["last_seen_guid"] = first_guid_this_run
        
    print(f"Finished {site_name}! Scraped {new_rows_count} new articles.")
    return new_rows_count

def main():
    parser = argparse.ArgumentParser(description="Unified Deep RSS Scraper")
    parser.add_argument("--site", type=str, default="all", help="Specify a site to scrape (thecable, arise, vanguard, leadership, tribune, premiumtimes, channelstv) or 'all'")
    parser.add_argument("-m", "--manual", action="store_true", help="Manual mode: skips state tracking and outputs to manual_ file")
    parser.add_argument("-t", "--time", type=str, default=None, help="Time limit filter (e.g. 1h, 24h, 1d)")
    args = parser.parse_args()

    time_threshold = parse_time_filter(args.time)
    is_manual = args.manual

    print("=== Unified Deep RSS Scraper ===")
    
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    
    global_state = load_state()
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    total_new = 0
    from wp_api.businessday_deep_scraper import run_businessday_deep_scrape
    from wp_api.dailytrust_deep_scraper import run_dailytrust_deep_scrape
    from wp_api.punch_deep_scraper import run_punch_deep_scrape
    from wp_api.guardian_deep_scraper import run_guardian_deep_scrape
    from wp_api.thisday_deep_scraper import run_thisday_deep_scrape
    from wp_api.instablog9ja_deep_scraper import run_instablog9ja_deep_scrape
    from wp_api.channelstv_deep_scraper import run_channelstv_deep_scrape
    
    if args.site == "businessday" or args.site == "all":
        print(f"\n=== Deep API Scraping BUSINESSDAY ===")
        total_new += run_businessday_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)

    if args.site == "dailytrust" or args.site == "all":
        print(f"\n=== Deep API Scraping DAILYTRUST ===")
        total_new += run_dailytrust_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)
        
    if args.site == "punch" or args.site == "all":
        print(f"\n=== Deep API Scraping PUNCH ===")
        total_new += run_punch_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)
        
    if args.site == "guardian" or args.site == "all":
        print(f"\n=== Deep API Scraping GUARDIAN ===")
        total_new += run_guardian_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)
        
    if args.site == "thisday" or args.site == "all":
        print(f"\n=== Deep API Scraping THISDAY ===")
        total_new += run_thisday_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)
        
    if args.site == "instablog9ja" or args.site == "all":
        print(f"\n=== Deep API Scraping INSTABLOG9JA ===")
        total_new += run_instablog9ja_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)
        
    if args.site == "channelstv" or args.site == "all":
        print(f"\n=== Deep API Scraping CHANNELS TV ===")
        total_new += run_channelstv_deep_scrape(is_manual=is_manual, time_threshold=time_threshold)
    
    targets = SITES.items() if args.site == "all" else {k: v for k, v in SITES.items() if k == args.site}.items()
    
    if not targets:
        if args.site not in ["businessday", "dailytrust", "punch", "guardian", "thisday", "instablog9ja", "channelstv"]:
            print(f"Error: Site '{args.site}' not recognized. Valid options: {list(SITES.keys())} or 'all'")
            return
        
    for site_name, base_url in targets:
        new_count = run_deep_scraper_for_site(site_name, base_url, global_state, today_str)
        total_new += new_count
        save_state(global_state) # Save after each site
        
    print(f"\\n=== All Done! Deep Scraped {total_new} total new articles across {len(targets)} sites. ===")

if __name__ == "__main__":
    main()
