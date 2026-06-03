import glob

files = glob.glob("/home/seyi/Documents/Antigravity/NGN site/scraper/wp_api/*_deep_scraper.py")

old_code = """                    # Check time threshold
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
                            pass"""

new_code = """                    # Check time threshold
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
                            pass"""

for file_path in files:
    with open(file_path, "r") as f:
        content = f.read()

    # Inject old_posts_count = 0 before the loop
    if "old_posts_count = 0" not in content:
        content = content.replace("stop_scraping = False\n", "stop_scraping = False\n    old_posts_count = 0\n")
        
    if old_code in content:
        content = content.replace(old_code, new_code)
        
    with open(file_path, "w") as f:
        f.write(content)
        
print("Sticky post fix applied to all 6 scrapers.")
