import subprocess
import sys

def run_script(script_name):
    print(f"\n{'='*50}\nRunning {script_name}...\n{'='*50}")
    try:
        subprocess.run([sys.executable, f"scraper/{script_name}"], check=True)
        print(f"\n[SUCCESS] {script_name} completed.")
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] {script_name} failed with exit code {e.returncode}.")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error running {script_name}: {e}")

if __name__ == "__main__":
    scripts = [
        "run_wp_scrapers.py",
        "run_rss_scrapers.py",
        "run_domain_scrapers.py",
        "run_all_deep_scrapers.py"
    ]
    
    print("Starting all scraping jobs...")
    for script in scripts:
        run_script(script)
        
    print("\nAll scraping tasks finished! Ready for ingestion.")
