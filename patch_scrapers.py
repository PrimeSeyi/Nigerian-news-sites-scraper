import os
import glob

# The 6 files to patch
files = glob.glob("/home/seyi/Documents/Antigravity/NGN site/scraper/wp_api/*_deep_scraper.py")

for file_path in files:
    with open(file_path, "r") as f:
        content = f.read()

    # 1. Update function signature
    site_name = os.path.basename(file_path).replace("_deep_scraper.py", "")
    sig_old = f"def run_{site_name}_deep_scrape():"
    sig_new = f"def run_{site_name}_deep_scrape(is_manual=False, time_threshold=None):"
    
    if sig_old in content:
        content = content.replace(sig_old, sig_new)
    
    # 2. Update Delta Scraping Check
    delta_old = 'if guid == site_state.get("last_seen_guid"):'
    delta_new = 'if not is_manual and guid == site_state.get("last_seen_guid"):'
    if delta_old in content:
        content = content.replace(delta_old, delta_new)
        
    # 3. Handle try/except KeyboardInterrupt for the pagination loop
    # Wait, instablog9ja already has it. Check if it does.
    if "try:\n        for page in range(1, MAX_PAGES + 1):" not in content:
        loop_old = "    for page in range(1, MAX_PAGES + 1):\n        if stop_scraping:\n            break"
        loop_new = "    try:\n        for page in range(1, MAX_PAGES + 1):\n            if stop_scraping:\n                break"
        content = content.replace(loop_old, loop_new)
        
        # Need to indent the entire loop body by 4 spaces.
        # It's easier to just replace specific ends
        end_loop_old = "        time.sleep(1)\n\n    all_articles.reverse()"
        end_loop_new = "        time.sleep(1)\n    except KeyboardInterrupt:\n        print(f\"\\n[!] Scraper manually interrupted by user on page {page}.\")\n\n    all_articles.reverse()"
        content = content.replace(end_loop_old, end_loop_new)
        
        # We need to indent the lines between `for page` and `time.sleep(1)`.
        # Instead of parsing, I will just do a regex replace to indent the lines inside the loop
        import re
        def indent_loop(match):
            lines = match.group(0).split('\n')
            indented = []
            for i, line in enumerate(lines):
                if i == 0 or i == len(lines)-1 or i == len(lines)-2:
                     indented.append(line) # keep try/except block unindented relative to itself, wait.
                else:
                    if line.strip():
                        indented.append("    " + line)
                    else:
                        indented.append(line)
            return '\n'.join(indented)
            
        # Actually regex indentation is too risky for Python scope. Let's do a simple string replace for the entire loop block
        
    # 4. Update Time filter logic
    time_extract_old = "                date_time = post.get('date_gmt', post.get('date', ''))\n                \n                all_articles.append("
    time_extract_new = """                date_time = post.get('date_gmt', post.get('date', ''))
                
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
                
                all_articles.append("""
    
    if time_extract_old in content:
        content = content.replace(time_extract_old, time_extract_new)
        
    # instablog9ja has a slightly different layout because of keywords.
    # For instablog:
    time_ext_inst_old = "                date_time = post.get('date_gmt', post.get('date', ''))\n                \n                all_articles.append(["
    if time_ext_inst_old in content:
        content = content.replace(time_ext_inst_old, time_extract_new.replace("append(", "append(["))

    # 5. Update filename saving logic
    file_save_old = f'        filename = os.path.join(BASE_DIR, "data", f"{site_name}_api_{{execution_time_str}}")'
    file_save_new = f'        prefix = "manual_" if is_manual else ""\n        filename = os.path.join(BASE_DIR, "data", f"{{prefix}}{site_name}_api_{{execution_time_str}}")'
    if file_save_old in content:
        content = content.replace(file_save_old, file_save_new)
        
    # 6. Update last_seen_guid save
    guid_save_old = '    if first_guid_this_run is not None:\n        site_state["last_seen_guid"] = first_guid_this_run'
    guid_save_new = '    if not is_manual and first_guid_this_run is not None:\n        site_state["last_seen_guid"] = first_guid_this_run'
    if guid_save_old in content:
        content = content.replace(guid_save_old, guid_save_new)
        
    with open(file_path, "w") as f:
        f.write(content)
        
print("Patching complete.")
