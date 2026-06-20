#!/bin/bash
set -e

echo "==========================================="
echo "   ANTIGRAVITY PIPELINE (SERVER-SIDE)      "
echo "==========================================="

echo "[1/4] Setting up environment..."
cd "$(dirname "$0")"
if [ ! -d "scraper/venv" ]; then
    python3 -m venv scraper/venv
fi
source scraper/venv/bin/activate
pip install -q --no-cache-dir pandas sentence-transformers scikit-learn pymysql cryptography requests beautifulsoup4 feedparser lxml python-dateutil cloudscraper

echo "[2/4] Running Scrapers for 2 weeks..."
# Run the master orchestrator
# Note: Ensure the orchestrator scripts fetch historical data if pagination is supported.
python3 scraper/run_all_scrapers.py || echo "Warning: Some scrapers may have failed."

echo "[3/4] Running AI Semantic Clustering (db_ingestor.py)..."
python3 scraper/db_ingestor.py

echo "[4/4] Exporting clustered database to Dashboard JSON..."
python3 export_dashboard.py

echo "==========================================="
echo "Pipeline Complete!"
echo "Download dashboard_viewer/clusters.json to your local machine."
echo "==========================================="
