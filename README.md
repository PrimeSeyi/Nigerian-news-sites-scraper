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
*   **Instablog9ja** *(Implements localized keyword-matching logic)*
*   **Channels TV**

### 2. `scraper/rss/` (XML RSS Engines)
These scrapers utilize robust XML parsing with built-in chronological memory reversal to extract paginated historical data natively.
*   **TheCable**
*   **Premium Times**
*   **Vanguard**
*   **Leadership**
*   **Tribune**
*   **Arise TV**
*   **Channels TV**

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

All deep crawlers are unified under a single, powerful execution engine: `run_all.py` (Master Orchestrator) or script-specific orchestrators like `run_all_deep_scrapers.py`.

### Running Everything Automatically
To trigger a massive concurrent deep crawl across all supported domains sequentially (WP API, RSS, Domain Structure, Deep XML):

```bash
cd scraper
python run_all.py
```

### Running Specific Scrapers
Navigate to the `scraper/` directory and execute the engine by passing the `--site` flag to specific runners:

```bash
# Run BusinessDay only (WP API)
python run_wp_scrapers.py --site businessday

# Run Punch only (WP API)
python run_wp_scrapers.py --site punch
```

### Advanced CLI Controls
The orchestrator supports advanced flags for highly targeted scraping without corrupting your delta tracking states:

*   **Manual Mode (`-m` or `--manual`)**: Completely bypasses the memory tracker (`deep_scraper_states.json` / `wp_scraper_states.json`). Use this for ad-hoc sweeps without polluting the automated state. Outputs are safely saved with a `manual_` prefix.
*   **Time Filtering (`-t` or `--time`)**: Caps the chronological depth of your sweep relative to the exact moment of execution (e.g., `1h`, `24h`, `1d`, `400d`). Includes built-in bypass logic for "Sticky/Pinned" posts to avoid premature halts.

```bash
# Example: Run Instablog9ja manually, capped to the last 7 days
python run_wp_scrapers.py --site instablog9ja -m -t 7d
```

### Output
All extracted data is instantly formatted into CSV files and saved in the `scraper/data/` directory. Each file is isolated via execution-timestamping (e.g., `punch_api_2026-05-31_10-38-00.csv`) to strictly prevent data corruption.

---

## 🗄️ Database Ingestion Pipeline

Once the CSVs are generated in the `scraper/data/` directory, they must be securely loaded into the database using the unified ingestor.

### 1. Database Requirements
The ingestor expects a running **MySQL** or **MariaDB** instance. It is highly recommended to run this inside an isolated Docker container:

```bash
# Spin up a lightweight MariaDB 10.5 instance
docker run --name mysql-db -e MYSQL_ROOT_PASSWORD=rootpassword -e MYSQL_DATABASE=news_db -p 3306:3306 -d mariadb:10.5
```

### 2. Running the Ingestor
To push the CSV data into the database safely:

```bash
cd scraper
python db_ingestor.py
```

### 3. Ingestion Features
*   **Idempotent Loading:** The ingestor utilizes `INSERT IGNORE INTO` with strict `UNIQUE` constraints on URLs/GUIDs. You can run the ingestor multiple times over the same CSVs without ever duplicating data.
*   **Dynamic Table Routing:** The script dynamically parses the CSV headers and routes the data into the correct strict SQL schema automatically (`deep_rss`, `wp_api`, or `generic_rss`).
*   **Safe Archiving:** Once a CSV is mathematically verified as 100% ingested, it is safely moved from `scraper/data/` to `scraper/data/archive/` to keep your workspace clean.

---

## ⚠️ Important Things to Note

1.  **Delta Scraping (State Tracking):** The crawlers utilize memory trackers located at `scraper/data/*.json` (like `deep_scraper_states.json`). Once a scraper encounters a `guid` (Article ID) it has seen in a previous run, it will instantly **STOP** scraping. This prevents infinite loops and duplicate data ingestion.
    *   *Tip:* If you want to force a domain to deep crawl from scratch, delete its `.json` tracking file.
2.  **Chronology:** Every generated CSV file is meticulously sorted in reverse chronological order (**Oldest to Newest**). This ensures safe, collision-free migration into downstream databases.
3.  **Graceful Terminations (`Ctrl+C`):** You can safely abort *any* running scraper at any time using `Ctrl+C`. The engine intercepts the kill signal, completely halts pagination, perfectly reverses the data array to preserve chronology, and instantly saves all accumulated data to a CSV before exiting. Zero data loss.
4.  **WAF Rate Limiting:** While the WP-JSON and RSS endpoints are highly resilient, running scrapers aggressively may still trigger temporary Cloudflare bans. The engine has built-in `time.sleep()` delays to mimic polite human behavior.

---
*Engineered for high-volume, structural data integrity.*


## 🧠 Semantic Incident Clustering & Zero-Shot NLP

The pipeline features an advanced AI clustering engine (`cluster_from_csvs.py`) that deduplicates raw news reports into discrete security incidents and assigns accurate geographic taxonomy.

- **Global Semantic Clustering**: Uses `SentenceTransformers` (`all-MiniLM-L6-v2`) and `AgglomerativeClustering` (precision `0.40` distance threshold) combined with custom penalties for temporal distance (>24hrs) and conflicting geographic boundaries.
- **Hierarchical Geographic Resolution**: Automatically resolves incident geography across 3 tiers (State level, Geopolitical Zone level, and Broad Regional level) using strict regex word boundaries (`\bState\b`).
- **Zero-Shot NLP & Local Overrides**: Completely eliminates the legacy "Unresolved Region" fallback. Un-geocoded articles are dynamically partitioned into **"National / General Nigerian"** or **"Abroad / International"** via semantic distance computation against runtime string prototypes. A mandatory override config (`domestic_keywords.json`) ensures domestic agencies (*Tinubu, EFCC, NCDC, DSS*) never leak into international clusters.

---

## 📊 Macro-Attention Fingerprinting (MAF) & Megaphone Index

Beyond simple article counting, the intelligence engine quantifies **systemic editorial attention bias** across Nigerian publishing houses.

### 1. Megaphone Index (MI)
The Megaphone Index measures media amplification relative to actual incident frequency:
$$\text{MI} = \frac{\text{Total Scraped Articles}}{\text{Distinct Verified Incidents}}$$
- **High MI ($\ge 5.0$)**: *Urban Syndication Skew*. Indicates massive editorial repetition and think-pieces dedicated to a small number of events.
- **Low MI ($\le 1.5$)**: *Hinterland Isolation*. Indicates under-reported kinetic events where rural tragedies receive almost zero national follow-up coverage.

### 2. Macro-Attention Fingerprinting (MAF)
Every story cluster is categorized into socio-political buckets (`ELITE / VIP PATRIARCHS` vs `KINETIC / RURAL MASSACRES`) to calculate three forensic indicators:
*   **`ART` (Reach)**: Average number of articles per incident. Proves immediate newsroom staff allocation.
*   **`DOM` (Consensus)**: Average number of distinct news publishers covering the story.
*   **`LIFESPAN` (Durability)**: Time delta (in hours) between initial report and final follow-up. Proves news cycle attention span.

---

## 🖥️ Brutalist Forensics Dashboard (`dashboard_viewer/`)

The platform features a lightning-fast, zero-dependency visualizer (`dashboard_viewer/index.html`) engineered following strict AlphaSignal brutalist aesthetics (zero border-radius, high-contrast monospace layout).

- **Bias Forensics Directory**: Dedicated sidebar tree (`// BIAS FORENSICS [DIR]`) allowing one-click isolation of Elite/VIP political patriarchs vs. Kinetic/Rural massacre threads.
- **Pure-CSS Comparative Charting**: Renders multi-color visual bar charts and stacked percentage tracks comparing attention reach, narrative durability, and macro focus share directly in vanilla CSS without external graphing libraries.
- **Paper-White Light Mode**: Built-in instant theme toggle (`[☀ LIGHT]` / `[☾ DARK]`) supporting high-contrast charcoal typography on paper-white background cards.

---

## ⚙️ Configuration & Automated Deployment

*   `keywords.json`: Centralized dictionary of security/crime terms used to filter raw scraped CSVs.
*   `domestic_keywords.json`: Configurable whitelist of domestic entities used to bypass Zero-Shot classification.
*   `server_pipeline.sh`: One-click deployment shell script that ingests CSVs, runs AI clustering, exports JSON telemetry (`clusters.json` & `bias_metrics.json`), and serves the dashboard locally.

