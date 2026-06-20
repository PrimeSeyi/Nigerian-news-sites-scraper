#!/bin/bash
# Wait for the background SSH command (running inside the agent's environment) to complete
# Instead of tracking the exact PID, we can simply poll the server to see if export_dashboard.py generated clusters.json

while true; do
    if ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_azure azure@52.152.146.13 "[ -f ~/antigravity_pipeline/dashboard_viewer/clusters.json ]"; then
        echo "Found clusters.json! Copying to local machine..."
        scp -o StrictHostKeyChecking=no -i ~/.ssh/id_azure azure@52.152.146.13:~/antigravity_pipeline/dashboard_viewer/clusters.json "./dashboard_viewer/clusters.json"
        
        # Inject the new JSON into the HTML safely
        python3 -c '
import re

html_path = "dashboard_viewer/index.html"
json_path = "dashboard_viewer/clusters.json"

with open(json_path, "r", encoding="utf-8") as f:
    cluster_data = f.read()

with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

pattern = re.compile(r"(let dashboardData = )\{.*?\}(;\n\s*const ZONE_MAPPING)", re.DOTALL)
match = pattern.search(html_content)

if match:
    new_html = html_content[:match.start()] + f"let dashboardData = {cluster_data};\n        const ZONE_MAPPING" + html_content[match.end():]
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(new_html)
'
        break
    fi
    sleep 15
done
