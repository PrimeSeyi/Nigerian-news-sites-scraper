import cloudscraper
import xml.etree.ElementTree as ET
import csv
import json
import os
import datetime
from urllib.parse import urlparse
import time

STATE_FILE = "thecable_state.json"
MAX_ROWS_PER_FILE = 300
MAX_PAGES = 200
BASE_URL = "https://www.thecable.ng"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        "last_seen_guid": None,
        "date": None,
        "today_count": 0
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def get_subdomain(url):
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname:
            parts = hostname.split('.')
            if len(parts) >= 3:
                return parts[0] # e.g. 'www', 'factcheck', 'lifestyle'
        return 'unknown'
    except:
        return 'unknown'

def get_current_csv_info(today_str):
    """Finds the active CSV file for today and its current row count."""
    base_name = f"thecable_rss_{today_str}"
    
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

def main():
    print("=== TheCable Deep RSS Scraper ===")
    
    state = load_state()
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Reset stats if it's a new day
    if state["date"] != today_str:
        state["date"] = today_str
        state["today_count"] = 0

    csv_filename, current_file_rows = get_current_csv_info(today_str)
    
    scraper = cloudscraper.create_scraper()
    
    first_guid_this_run = None
    stop_scraping = False
    new_rows_count = 0
    
    # Open CSV in append mode
    f = open(csv_filename, mode='a', newline='', encoding='utf-8')
    writer = csv.writer(f)
    if current_file_rows == 0:
        writer.writerow(['category', 'title', 'link', 'guid', 'date_time', 'subdomain'])

    for page in range(1, MAX_PAGES + 1):
        if stop_scraping:
            break
            
        print(f"Fetching page {page}...")
        url = f"{BASE_URL}/feed/?paged={page}"
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
                guid = guid_elem.text.strip() if guid_elem is not None else None
                
                if not guid:
                    continue
                    
                # Stop if we hit the last remembered GUID from a previous run
                if guid == state["last_seen_guid"]:
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
                
                # Write to CSV
                writer.writerow([category_str, title, link, guid, pub_date, subdomain])
                state["today_count"] += 1
                new_rows_count += 1
                current_file_rows += 1
                
                # Handle file rotation
                if current_file_rows >= MAX_ROWS_PER_FILE:
                    f.close()
                    csv_filename, current_file_rows = get_current_csv_info(today_str)
                    f = open(csv_filename, mode='a', newline='', encoding='utf-8')
                    writer = csv.writer(f)
                    writer.writerow(['category', 'title', 'link', 'guid', 'date_time', 'subdomain'])
                    
        except Exception as e:
            print(f"Error parsing page {page}: {e}")
            break
            
        # Be polite to servers
        time.sleep(1)

    f.close()

    # Update state only if we actually processed new items
    if first_guid_this_run is not None:
        state["last_seen_guid"] = first_guid_this_run
    save_state(state)
    
    print(f"\\n=== Finished! Scraped {new_rows_count} new articles. ===")
    print(f"Today's total row count across all files: {state['today_count']}")

if __name__ == "__main__":
    main()
