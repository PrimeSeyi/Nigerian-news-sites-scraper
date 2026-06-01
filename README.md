# Nigerian News Sites Scraper

A robust, highly optimized, and WAF-resilient Python web scraping infrastructure designed to aggregate historical and real-time news data across 15 major Nigerian news domains.

This repository features advanced engineering techniques—including WordPress REST API (`/wp-json/`) pivots and Cloudflare JS-Challenge bypasses—to safely extract thousands of chronologically ordered articles into clean, standardized CSV files.

## 📁 Architecture & Supported Domains

The scraper infrastructure is cleanly separated into three modular sub-directories based on the extraction strategy required for each domain. This guarantees that API-driven logic is isolated from fragile HTML parsers.

### 1. `scraper/wp_api/` (WordPress JSON API Engines)
These scrapers natively bypass Cloudflare WAF restrictions by tapping directly into the site's hidden REST API, translating internal category IDs to human-readable strings on the fly.
*   **BusinessDay**
*   **Daily Trust**
*   **Punch**
*   **The Guardian**
*   **ThisDay**
*   **Daily Post**

### 2. `scraper/rss/` (XML RSS Engines)
These scrapers utilize robust XML parsing with built-in chronological memory reversal to extract paginated historical data natively.
*   **TheCable**
*   **Premium Times**
*   **Vanguard**
*   **Leadership**
*   **Tribune**
*   **Arise TV**

### 3. `scraper/domain_structure/` (HTML Parsing Engines)
Traditional web scrapers dependent on HTML structural extraction.
*   **Channels TV** (Iterates via calendar-based URLs)
*   **Sahara Reporters** (Query-parameter HTML pagination)
*   **Pulse** (Query-parameter HTML pagination)
*   **Legit.ng** (Currently stagnant at Page 1 due to strict Cloudflare blocking)

---

## 🛠️ Prerequisites & Setup

### 1. Requirements
*   **Python 3.8+**
*   **Git**

### 2. Environment Setup
It is highly recommended to isolate the project's dependencies using a Python Virtual Environment (`venv`).

```bash
# Clone the repository
git clone git@github.com:PrimeSeyi/Nigerian-news-sites-scraper.git
cd Nigerian-news-sites-scraper

# Create a virtual environment named "venv"
python3 -m venv venv

# Activate the virtual environment
# On Linux / macOS:
source venv/bin/activate
# On Windows:
venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```
*(Note: Ensure you have `cloudscraper`, `beautifulsoup4`, and `lxml` installed).*

---

## 💻 How to Run the Scrapers

All deep crawlers are unified under a single, powerful execution engine: `run_all_deep_scrapers.py`.

### Running Specific Scrapers
Navigate to the `scraper/` directory and execute the engine by passing the `--site` flag:

```bash
cd scraper

# Run BusinessDay only
python run_all_deep_scrapers.py --site businessday

# Run Punch only
python run_all_deep_scrapers.py --site punch
```

### Running All Scrapers Simultaneously
To trigger a massive concurrent deep crawl across all supported domains:

```bash
python run_all_deep_scrapers.py --site all
```

### Output
All extracted data is instantly formatted into CSV files and saved in the `scraper/data/` directory. Each file is isolated via execution-timestamping (e.g., `punch_api_2026-05-31_10-38-00.csv`) to strictly prevent data corruption.

---

## ⚠️ Important Things to Note

1.  **Delta Scraping (State Tracking):** The crawlers utilize a memory tracker located at `scraper/data/deep_scraper_states.json`. Once a scraper encounters a `guid` (Article ID) it has seen in a previous run, it will instantly **STOP** scraping. This prevents infinite loops and duplicate data ingestion.
    *   *Tip:* If you want to force a domain to deep crawl from scratch, delete its entry from the `deep_scraper_states.json` file.
2.  **Chronology:** Every generated CSV file is meticulously sorted in reverse chronological order (**Oldest to Newest**). This ensures safe, collision-free migration into downstream databases like MongoDB.
3.  **WAF Rate Limiting:** While the WP-JSON and RSS endpoints are highly resilient, running scrapers aggressively may still trigger temporary Cloudflare bans. The engine has built-in `time.sleep()` delays to mimic polite human behavior.

---
*Engineered for high-volume, structural data integrity.*
