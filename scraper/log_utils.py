import os
import time
import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraper_execution.log")

def log_execution(category, name, duration, count=None, error=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "SUCCESS" if error is None else "FAILED"
    msg = f"[{timestamp}] [{category.upper()}:{name.upper()}] {status} - Time: {duration:.2f}s"
    if count is not None:
        msg += f" | Articles: {count}"
    if error:
        msg += f" | Error: {error}"
    msg += "\n"
    print(msg.strip())
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg)
    except Exception as e:
        print(f"Failed to write log: {e}")
