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
python3 scraper/run_all.py || echo "Warning: Some scrapers may have failed."

echo "[3/3] Running AI Semantic Clustering directly from CSVs..."
python3 cluster_from_csvs.py

echo "==========================================="
echo "Pipeline Complete!"
echo "Download dashboard_viewer/clusters.json to your local machine."
echo "==========================================="
