import argparse
import datetime
import re
import concurrent.futures

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
    parser = argparse.ArgumentParser(description="Unified WP API Scraper")
    parser.add_argument("--site", type=str, default="all", help="Specify a site to scrape (businessday, dailytrust, punch, guardian, thisday, instablog9ja, channelstv) or 'all'")
    parser.add_argument("-m", "--manual", action="store_true", help="Manual mode: skips state tracking and outputs to manual_ file")
    parser.add_argument("-t", "--time", type=str, default=None, help="Time limit filter (e.g. 1h, 24h, 1d)")
    args = parser.parse_args()

    time_threshold = parse_time_filter(args.time)
    is_manual = args.manual

    print("=== Unified WP API Scraper ===")
    
    total_new = 0
    from wp_api.businessday_deep_scraper import run_businessday_deep_scrape
    from wp_api.dailytrust_deep_scraper import run_dailytrust_deep_scrape
    from wp_api.punch_deep_scraper import run_punch_deep_scrape
    from wp_api.guardian_deep_scraper import run_guardian_deep_scrape
    from wp_api.thisday_deep_scraper import run_thisday_deep_scrape
    from wp_api.instablog9ja_deep_scraper import run_instablog9ja_deep_scrape
    from wp_api.channelstv_deep_scraper import run_channelstv_deep_scrape
    
    targets = []
    if args.site == "businessday" or args.site == "all":
        targets.append(("BUSINESSDAY", run_businessday_deep_scrape))
    if args.site == "dailytrust" or args.site == "all":
        targets.append(("DAILYTRUST", run_dailytrust_deep_scrape))
    if args.site == "punch" or args.site == "all":
        targets.append(("PUNCH", run_punch_deep_scrape))
    if args.site == "guardian" or args.site == "all":
        targets.append(("GUARDIAN", run_guardian_deep_scrape))
    if args.site == "thisday" or args.site == "all":
        targets.append(("THISDAY", run_thisday_deep_scrape))
    if args.site == "instablog9ja" or args.site == "all":
        targets.append(("INSTABLOG9JA", run_instablog9ja_deep_scrape))
    if args.site == "channelstv" or args.site == "all":
        targets.append(("CHANNELS TV", run_channelstv_deep_scrape))
        
    if not targets:
        print(f"Error: Site '{args.site}' not recognized for WP API.")
        return

    print(f"Starting {len(targets)} WP API scrapers with max_workers=3...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(func, is_manual=is_manual, time_threshold=time_threshold): name for name, func in targets}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                new_count = future.result()
                if new_count:
                    total_new += new_count
            except Exception as exc:
                print(f"!!! Error running {name}: {exc}")

    print(f"\n=== All Done! Deep Scraped {total_new} total new articles across {len(targets)} WP sites. ===")

if __name__ == "__main__":
    main()
