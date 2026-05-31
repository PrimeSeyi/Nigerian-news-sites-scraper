import os
import csv
import time
import datetime
import html
import cloudscraper

class BusinessDayApiScraper:
    def __init__(self):
        self.api_url = "https://businessday.ng/wp-json/wp/v2/posts"
        self.session = cloudscraper.create_scraper()

    def fetch_all(self, max_pages=20, per_page=100):
        os.makedirs("data", exist_ok=True)
        execution_time_str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_filename = f"data/businessday_api_{execution_time_str}.csv"
        
        all_articles = []
        
        for page in range(1, max_pages + 1):
            print(f"[businessday] Fetching API page {page}...")
            url = f"{self.api_url}?per_page={per_page}&page={page}"
            
            try:
                response = self.session.get(url, timeout=15)
                
                if response.status_code != 200:
                    print(f"Failed to fetch page {page}. Status code: {response.status_code}")
                    break
                    
                data = response.json()
                if not data:
                    print("No more items returned.")
                    break
                    
                print(f"[businessday] Fetched {len(data)} items on page {page}.")
                
                for post in data:
                    # Extract requested metadata
                    post_id = str(post.get('id', ''))
                    guid = post.get('guid', {}).get('rendered', '')
                    slug = post.get('slug', '')
                    
                    title = post.get('title', {}).get('rendered', 'No title')
                    title = html.unescape(title) # Decode HTML entities like &#8217;
                    
                    link = post.get('link', '')
                    
                    # Category is left empty as requested
                    category = ""
                    
                    all_articles.append([post_id, guid, slug, title, link, category])
                    
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
                
            time.sleep(1) # Be polite
            
        print("\\nReversing chronological order (Oldest -> Newest)...")
        all_articles.reverse()
        
        print(f"Saving {len(all_articles)} items to {csv_filename}...")
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['uuid', 'guid', 'slug', 'title', 'link', 'category'])
            for row in all_articles:
                writer.writerow(row)
                
        print("=== Finished! ===")

if __name__ == "__main__":
    scraper = BusinessDayApiScraper()
    # 20 pages * 100 items = 2000 items
    scraper.fetch_all(max_pages=20, per_page=100)
