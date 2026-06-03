import os
import csv
import json
import time
import datetime
import html
import argparse
import cloudscraper

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, "data", "deep_scraper_states.json")
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

def fetch_category_map(session):
    print("[thisday] Fetching category mapping...")
    category_map = {}
    page = 1
    while True:
        url = f"https://www.thisdaylive.com/wp-json/wp/v2/categories?per_page=100&page={page}"
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
    print(f"[thisday] Successfully mapped {len(category_map)} categories.")
    return category_map

def run_thisday_deep_scrape(is_manual=False, time_threshold=None):
    os.makedirs("data", exist_ok=True)
    global_state = load_state()
    
    if "thisday" not in global_state:
        global_state["thisday"] = {
            "last_seen_guid": None,
            "date": None,
            "today_count": 0
        }
    
    site_state = global_state["thisday"]
    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    
    if site_state.get("date") != today_str:
        site_state["date"] = today_str
        site_state["today_count"] = 0

    execution_time_str = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    scraper = cloudscraper.create_scraper()
    
    category_map = fetch_category_map(scraper)
    
    first_guid_this_run = None
    stop_scraping = False
    new_rows_count = 0
    all_articles = []
    
    api_url = "https://www.thisdaylive.com/wp-json/wp/v2/posts"

    try:
        for page in range(1, MAX_PAGES + 1):
            if stop_scraping:
                break
                
            print(f"[thisday] Fetching API page {page}...")
            url = f"{api_url}?per_page=100&page={page}"
            try:
                response = scraper.get(url, timeout=15)
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
                        
                    if first_guid_this_run is None:
                        first_guid_this_run = guid
                        
                    # Extract fields
                    post_id = str(post.get('id', ''))
                    slug = post.get('slug', '')
                    title = html.unescape(post.get('title', {}).get('rendered', 'No title'))
                    link = post.get('link', '')
                    
                    # Map categories
                    cat_ids = post.get('categories', [])
                    cat_names = [category_map.get(cid, str(cid)) for cid in cat_ids]
                    category_str = ", ".join(cat_names)
                    
                    date_time = post.get('date_gmt', post.get('date', ''))
                    
                    # Check time threshold
                    if time_threshold and date_time:
                        try:
                            post_dt = datetime.datetime.fromisoformat(date_time)
                            if post_dt.tzinfo is None:
                                post_dt = post_dt.replace(tzinfo=datetime.timezone.utc)
                                
                            if post_dt < time_threshold:
                                print(f"-> Reached time limit ({date_time}). Stopping.")
                                stop_scraping = True
                                break
                        except ValueError:
                            pass
                    
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
        filename = os.path.join(BASE_DIR, "data", f"{prefix}thisday_api_{execution_time_str}")
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
    print(f"Finished thisday! Scraped {new_rows_count} new articles.")
    return new_rows_count

if __name__ == "__main__":
    print("=== ThisDay Deep API Scraper ===")
    run_thisday_deep_scrape()
