# NGN News Aggregation - Master Engineering Status & Technical Findings

This document serves as the comprehensive engineering log and technical specification for all 15 supported Nigerian news domains. It details the exact data ingestion strategies, the specific Web Application Firewalls (WAF) encountered, and the architectural solutions engineered to achieve deep historical data crawling.

---

## 🟢 Category 1: The WordPress REST API (WP-JSON) Breakthrough
**Status:** Highly Optimal, Cloudflare Bypassed, Deep Crawl Supported

**The Engineering Problem:**
Several major domains (BusinessDay, Daily Trust, Punch, The Guardian) employ aggressive Cloudflare "I am under attack" or "Are you a robot" JavaScript challenges. These challenges actively intercepted and blocked standard `requests` and `cloudscraper` attempts to access both their HTML pages and their native RSS XML endpoints (`/feed`). This restricted our ability to paginate backward in time, trapping us at "Page 1".

**The Engineered Solution:**
We discovered a massive architectural loophole. Because these sites are built on WordPress, they natively expose the WordPress REST API at `/wp-json/wp/v2/`. Crucially, Cloudflare's WAF configuration on these domains completely ignores API requests directed at the `/wp-json/` routes. By pivoting our scrapers to this JSON backend, we unlocked completely unrestricted access to their entire databases. 

Furthermore, we implemented a dynamic category-mapping system: before crawling, the engine queries `/wp-json/wp/v2/categories?per_page=100` to build an in-memory dictionary. This allows us to instantly translate raw integer category IDs into human-readable strings for our CSV outputs.

### 1. BusinessDay
*   **Target Endpoint:** `https://businessday.ng/wp-json/wp/v2/posts`
*   **Engine Used:** Standalone `businessday_deep_scraper.py`
*   **Findings:** The RSS feed was failing heavily and producing malformed data. The WP-JSON API is entirely open. Testing revealed no API pagination limits; we successfully queried deep into Page 500 (50,000 articles) receiving HTTP 200 responses instantly. 
*   **Category System:** Discovered 232 active categories. Successfully mapped via the `/categories` endpoint.

### 2. Daily Trust
*   **Target Endpoint:** `https://dailytrust.com/wp-json/wp/v2/posts`
*   **Engine Used:** Standalone `dailytrust_deep_scraper.py`
*   **Findings:** The RSS crawler was previously getting hard-blocked by Cloudflare exactly at Page 29. By pivoting to WP-JSON, this limit vanished. We can now ingest thousands of articles at 100 articles per page.
*   **Category System:** Discovered 201 active categories. Successfully mapped.

### 3. Punch
*   **Target Endpoint:** `https://punchng.com/wp-json/wp/v2/posts`
*   **Engine Used:** Standalone `punch_deep_scraper.py`
*   **Findings:** Punch was notoriously the most locked-down site, rejecting all HTML/RSS pagination with a JS challenge. The WP-JSON API loophole works flawlessly here. We can now paginate to Page 200+ without any WAF interference.
*   **Category System:** Discovered 274 active categories. Successfully mapped.

### 4. The Guardian
*   **Target Endpoint:** `https://guardian.ng/wp-json/wp/v2/posts`
*   **Engine Used:** Standalone `guardian_deep_scraper.py`
*   **Findings:** Similar to Punch, The Guardian was returning strict 403 Forbidden errors on its RSS feeds. The WP-JSON REST API is fully exposed and immune to the WAF.
*   **Category System:** Discovered 165 active categories. Successfully mapped.

### 5. ThisDay
*   **Target Endpoint:** `https://www.thisdaylive.com/wp-json/wp/v2/posts`
*   **Engine Used:** Standalone `thisday_deep_scraper.py`
*   **Findings:** Transitioned from fragile RSS parsing to the robust WP-JSON architecture.
*   **Category System:** Discovered 24 active categories. Successfully mapped.

### 6. Daily Post
*   **Target Endpoint:** `https://dailypost.ng/wp-json/wp/v2/posts`
*   **Engine Used:** Standalone `daily_post_scraper.py`
*   **Findings:** Was the very first site we successfully deployed the WP-JSON architecture on. Runs smoothly with 100% reliability.

---

## 🟢 Category 2: Unrestricted XML Feeds (Flawless RSS)
**Status:** Highly Optimal, Native Pagination, Deep Crawl Supported

**The Engineering Problem & Solution:**
Unlike Category 1, these domains either do not use aggressive Cloudflare WAFs on their RSS feeds, or they have configured Cloudflare to whitelist the `/feed` routes. Because the XML feeds are openly accessible, we can natively append standard WordPress pagination parameters (e.g., `?paged=2`, `?paged=3`) to walk backward through time.

All of these sites are managed under a single, unified execution engine (`run_all_deep_scrapers.py`) which parses the XML structure (`<item>`, `<title>`, `<guid>`), reverses the batch chronologically (Oldest -> Newest), and outputs to our standard schema.

### 7. TheCable (`https://www.thecable.ng/feed`)
*   **Findings:** Extremely stable XML feed. Pagination parameter `?paged=N` works flawlessly. No WAF interference observed.

### 8. Premium Times (`https://www.premiumtimesng.com/feed`)
*   **Findings:** Standard WordPress XML feed. Easily handles deep pagination without throttling or triggering CAPTCHAs.

### 9. Vanguard (`https://www.vanguardngr.com/feed`)
*   **Findings:** Robust and reliable. Allows us to crawl thousands of articles via `?paged=N`.

### 10. Leadership (`https://leadership.ng/feed`)
*   **Findings:** Fully operational. The XML structure is clean and pagination works as expected.

### 11. Tribune (`https://tribuneonlineng.com/feed`)
*   **Findings:** Fully operational. RSS feed responds well to automated, sequential requests.

### 12. Arise TV (`https://www.arise.tv/feed`)
*   **Findings:** Fully operational. High volume of articles available via standard RSS pagination.

---

## 🟡 Category 3: Custom HTML Parsing
**Status:** Operational, HTML Scraping, Deep Crawl Supported

**The Engineering Problem & Solution:**
These sites either do not expose a WordPress JSON API, or their RSS feeds are broken (e.g., ignoring pagination commands and infinitely returning the same 20 articles). To circumvent this, we must scrape their actual HTML web pages using `BeautifulSoup`. 

### 13. Channels TV
*   **Target Strategy:** Date-based HTML Pagination (`https://www.channelstv.com/YYYY/MM/DD/page/N`)
*   **Findings:** The RSS feed is unreliable for deep crawling. However, Channels TV organizes its web archive strictly by calendar date. We engineered the scraper to iterate backward day-by-day, and then paginate within each specific day.
*   **Engine Used:** `channels_scraper.py`

### 14. Sahara Reporters
*   **Target Strategy:** Query-based HTML Pagination (`https://saharareporters.com/news?page=N`)
*   **Findings:** Their RSS feed (`/articles/rss-feed`) completely ignores pagination parameters, repeatedly serving the same recent items regardless of the page requested. We pivoted to scraping the `/news` web directory using HTML parsing, which successfully respects the `?page=` parameter.
*   **Engine Used:** `sahara_scraper.py`

### 15. Pulse
*   **Target Strategy:** Query-based HTML Pagination (`https://www.pulse.ng/?page=N`)
*   **Findings:** Successfully scraped via HTML. The structure is reliable and pagination works.
*   **Engine Used:** `pulse_scraper.py`

---

## 🔴 Category 4: Hard Blocked (The Final Boss)
**Status:** Stagnant, No Deep Crawl Supported

**The Engineering Problem:**
This domain represents the highest level of WAF restriction.

### 16. Legit.ng
*   **Target Strategy:** Blocked
*   **Findings:** 
    *   **HTML & RSS:** Cloudflare's JS Challenge intercepts all requests. `cloudscraper` is currently unable to bypass it.
    *   **WP-JSON:** We tested `https://www.legit.ng/wp-json/wp/v2/posts`. Unlike the Category 1 sites, Legit.ng does not use this architecture and returns a strict **404 Not Found** for this endpoint.
*   **Current Status:** We can only scrape the surface (latest articles on Page 1) using specialized headers, but we cannot paginate backward.
*   **Future Engineered Solution:** To unlock Legit.ng, we must abandon `cloudscraper` and deploy a headless browser (like Playwright or Selenium) that can physically render the DOM, execute the Cloudflare JavaScript, solve the challenge, and pass the resulting cookies to our scraper. Alternatively, a high-quality rotating proxy network is required.
