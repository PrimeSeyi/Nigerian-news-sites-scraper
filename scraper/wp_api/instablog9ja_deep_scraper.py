import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scraper_base import BaseNewsScraper
import csv
import json
import time
import datetime
import html
import argparse
import cloudscraper
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "data", "deep_scraper_states.json")
KEYWORDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.json")

MAX_ROWS_PER_FILE = 300
MAX_PAGES = 200

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def load_keywords():
    if os.path.exists(KEYWORDS_FILE):
        with open(KEYWORDS_FILE, "r") as f:
            return json.load(f)
    return []

def fetch_category_map(session):
    print("[instablog9ja] Fetching category mapping...")
    category_map = {}
    page = 1
    while True:
        url = f"https://instablog9ja.com/wp-json/wp/v2/categories?per_page=100&page={page}"
        try:
            res = session.get(url, timeout=15)
            if res.status_code != 200:
                break
            data = res.json()
            if not data:
                break
            for c in data:
                category_map[c['id']] = c['name']
            page += 1
        except Exception as e:
            print(f"Error fetching categories page {page}: {e}")
            break
    print(f"[instablog9ja] Successfully mapped {len(category_map)} categories.")
    return category_map

def run_instablog9ja_deep_scrape(is_manual=False, time_threshold=None):
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    global_state = load_state()
    
    if "instablog9ja" not in global_state:
        global_state["instablog9ja"] = {
            "last_seen_guid": None,
            "date": None,
            "today_count": 0
        }
    
    site_state = global_state["instablog9ja"]
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if site_state.get("date") != today_str:
        site_state["date"] = today_str
        site_state["today_count"] = 0

    execution_time_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    scraper = cloudscraper.create_scraper()
    
    category_map = fetch_category_map(scraper)
    
    # Load keywords and compile regex
    keywords = load_keywords()
    if not keywords:
        print("[instablog9ja] Warning: No keywords loaded. All articles will be skipped.")
        keyword_pattern = None
    else:
        # Use word boundaries for exact word matches to prevent partial matching (e.g., 'hit' in 'white')
        pattern_str = r'\b(?:' + '|'.join(re.escape(k) for k in keywords) + r')\b'
        keyword_pattern = re.compile(pattern_str, re.IGNORECASE)
    
    first_guid_this_run = None
    stop_scraping = False
    old_posts_count = 0
    new_rows_count = 0
    all_articles = []
    
    api_url = "https://instablog9ja.com/wp-json/wp/v2/posts"

    try:
        for page in range(1, MAX_PAGES + 1):
            if stop_scraping:
                break
                
            print(f"[instablog9ja] Fetching API page {page}...")
            url = f"{api_url}?per_page=100&page={page}"
            try:
                response = scraper.get(url, timeout=(10, 30))
                if response.status_code != 200:
                    print(f"Failed to fetch page {page}. Status: {response.status_code}")
                    break
                    
                data = response.json()
                if not data:
                    print("No more items found. Reached end of API.")
                    break
                    
                for post in data:
                    guid = post.get('guid', {}).get('rendered', '')
                    
                    if not guid:
                        continue
                        
                    # Delta Scraping Check
                    if not is_manual and guid == site_state.get("last_seen_guid"):
                        print(f"-> Encountered last remembered GUID ({guid}). Stopping delta scrape.")
                        stop_scraping = True
                        break
                        
                    # We record the first guid we see on page 1 regardless of keyword match
                    # so that future runs know where to stop
                    if first_guid_this_run is None:
                        first_guid_this_run = guid
                        
                    date_time = post.get('date_gmt', post.get('date', ''))
                    
                    # Check time threshold early
                    if time_threshold and date_time:
                        try:
                            post_dt = datetime.datetime.fromisoformat(date_time)
                            if post_dt.tzinfo is None:
                                post_dt = post_dt.replace(tzinfo=datetime.timezone.utc)
                                
                            if post_dt < time_threshold:
                                old_posts_count += 1
                                if old_posts_count >= 3:
                                    print(f"-> Reached time limit ({date_time}). Stopping.")
                                    stop_scraping = True
                                    break
                                continue # Skip old post but keep checking in case it's a sticky post
                            else:
                                old_posts_count = 0
                        except ValueError:
                            pass
                    
                    if not keyword_pattern:
                        continue # Skip everything if no keywords defined
                    
                    # Extract fields
                    post_id = str(post.get('id', ''))
                    slug = post.get('slug', '')
                    title = html.unescape(post.get('title', {}).get('rendered', 'No title'))
                    excerpt = html.unescape(post.get('excerpt', {}).get('rendered', ''))
                    
                    text_to_search = f"{title} {excerpt}"
                    
                    # Keyword check
                    if not keyword_pattern.search(text_to_search):
                        continue
                    
                    link = post.get('link', '')
                    
                    # Map categories
                    cat_ids = post.get('categories', [])
                    cat_names = [category_map.get(cid, str(cid)) for cid in cat_ids]
                    category_str = ", ".join(cat_names)
                    
                    all_articles.append([post_id, guid, slug, title, link, category_str, date_time])
                        
            except Exception as e:
                print(f"Error parsing page {page}: {e}")
                break
                
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n[!] Scraper manually interrupted by user on page {page}.")

    all_articles.reverse()
    
    current_file_rows = 0
    file_suffix = 0
    f = None
    writer = None
    
    def open_new_file(suffix):
        nonlocal current_file_rows
        prefix = "manual_" if is_manual else ""
        filename = os.path.join(BASE_DIR, "data", f"{prefix}instablog9ja_api_{execution_time_str}")
        if suffix > 0:
            filename = f"{filename}-{suffix:02d}.csv"
        else:
            filename = f"{filename}.csv"
            
        new_f = open(filename, mode='w', newline='', encoding='utf-8')
        new_writer = csv.writer(new_f)
        new_writer.writerow(['uuid', 'guid', 'slug', 'title', 'link', 'category', 'date_time'])
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
            
    if not is_manual and first_guid_this_run is not None:
        site_state["last_seen_guid"] = first_guid_this_run
        
    save_state(global_state)
    print(f"Finished instablog9ja! Scraped {new_rows_count} new keyword-matching articles.")
    return new_rows_count

if __name__ == "__main__":
    print("=== Instablog9ja Deep API Scraper ===")
    run_instablog9ja_deep_scrape()
