import os
import glob

base_dir = os.path.dirname(os.path.abspath(__file__))
scraper_dir = os.path.join(base_dir, "scraper")

def patch_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    modified = False
    
    if 'STATE_FILE = "data/deep_scraper_states.json"' in content:
        content = content.replace('STATE_FILE = "data/deep_scraper_states.json"', 'import os\nBASE_DIR = os.path.dirname(os.path.abspath(__file__))\nDATA_DIR = os.path.join(BASE_DIR, "data")\nSTATE_FILE = os.path.join(DATA_DIR, "deep_scraper_states.json")')
        modified = True
        
    if 'os.makedirs("data", exist_ok=True)' in content:
        if 'DATA_DIR = os.path.join(BASE_DIR, "data")' in content:
            content = content.replace('os.makedirs("data", exist_ok=True)', 'os.makedirs(DATA_DIR, exist_ok=True)')
        else:
            content = content.replace('os.makedirs("data", exist_ok=True)', 'os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"), exist_ok=True)')
        modified = True

    if 'base_name = f"data/{site_name}_rss_{today_str}"' in content:
        content = content.replace('base_name = f"data/{site_name}_rss_{today_str}"', 'base_name = os.path.join(DATA_DIR, f"{site_name}_rss_{today_str}")')
        modified = True
        
    if 'filename = f"data/{site_name}_rss_{execution_time_str}"' in content:
        content = content.replace('filename = f"data/{site_name}_rss_{execution_time_str}"', 'filename = os.path.join(DATA_DIR, f"{site_name}_rss_{execution_time_str}")')
        modified = True
        
    if 'filename = f"data/{prefix}{site_name}_rss_{execution_time_str}"' in content:
        content = content.replace('filename = f"data/{prefix}{site_name}_rss_{execution_time_str}"', 'filename = os.path.join(DATA_DIR, f"{prefix}{site_name}_rss_{execution_time_str}")')
        modified = True

    if 'csv_filename = f"data/scraped_news_' in content:
        content = content.replace('csv_filename = f"data/scraped_news_', 'csv_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", f"scraped_news_')
        content = content.replace(').csv"', ').csv")')
        modified = True

    if modified:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Patched {filepath}")

for root, _, files in os.walk(scraper_dir):
    for file in files:
        if file.endswith('.py'):
            patch_file(os.path.join(root, file))
