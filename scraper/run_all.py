import subprocess
import sys
import time
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from log_utils import log_execution

def run_script(script_name):
    print(f"\n{'='*50}\nRunning {script_name}...\n{'='*50}")
    start = time.time()
    try:
        subprocess.run([sys.executable, f"scraper/{script_name}"], check=True)
        duration = time.time() - start
        log_execution("ORCHESTRATOR", script_name, duration)
        print(f"\n[SUCCESS] {script_name} completed.")
    except subprocess.CalledProcessError as e:
        duration = time.time() - start
        log_execution("ORCHESTRATOR", script_name, duration, error=f"Exit code {e.returncode}")
        print(f"\n[ERROR] {script_name} failed with exit code {e.returncode}.")
    except Exception as e:
        duration = time.time() - start
        log_execution("ORCHESTRATOR", script_name, duration, error=str(e))
        print(f"\n[ERROR] Unexpected error running {script_name}: {e}")

if __name__ == "__main__":
    scripts = [
        "run_wp_scrapers.py",
        "run_rss_scrapers.py",
        "run_domain_scrapers.py"
    ]
    
    print("Starting all scraping jobs...")
    for script in scripts:
        run_script(script)
        
    print("\nAll scraping tasks finished! Ready for ingestion.")
