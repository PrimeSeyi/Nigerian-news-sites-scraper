import os
import json

base_dir = os.path.dirname(os.path.abspath(__file__))
viewer_dir = os.path.join(base_dir, "dashboard_viewer")
export_dir = os.path.join(viewer_dir, "notebooklm_exports")
os.makedirs(export_dir, exist_ok=True)

clusters_path = os.path.join(viewer_dir, "clusters.json")
bias_path = os.path.join(viewer_dir, "bias_metrics.json")

if not os.path.exists(clusters_path) or not os.path.exists(bias_path):
    print("Error: clusters.json or bias_metrics.json missing.")
    exit(1)

with open(clusters_path, "r", encoding="utf-8") as f:
    clusters_data = json.load(f)

with open(bias_path, "r", encoding="utf-8") as f:
    bias_data = json.load(f)

# Map cluster_id -> (state, cluster object)
all_clusters = {}
for state, sdata in clusters_data.get("states", {}).items():
    for c in sdata.get("clusters", []):
        all_clusters[c["cluster_id"]] = (state, c)

buckets = ["Elite/VIP", "Kinetic/Rural", "Other/General"]

for bucket in buckets:
    cids = bias_data.get(bucket, {}).get("cluster_ids", [])
    filename = bucket.lower().replace("/", "_") + "_clusters.txt"
    filepath = os.path.join(export_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as out:
        out.write(f"================================================================================\n")
        out.write(f" NOTEBOOK LM AUDIT EXPORT // NARRATIVE CATEGORY: {bucket.upper()}\n")
        out.write(f" TOTAL CLUSTERS IN CATEGORY: {len(cids)}\n")
        out.write(f"================================================================================\n\n")
        out.write(f"INSTRUCTIONS FOR NOTEBOOK LM:\n")
        out.write(f"Analyze the narrative clusters below. Evaluate if any cluster has been mischaracterized\n")
        out.write(f"into this category based on its representative headline and underlying article titles.\n")
        out.write(f"Identify potential keyword false positives or framing mutations.\n\n")
        
        for idx, cid in enumerate(cids, 1):
            if cid not in all_clusters:
                continue
            state, c = all_clusters[cid]
            out.write(f"--------------------------------------------------------------------------------\n")
            out.write(f"[{idx}] CLUSTER ID: {cid} | LOCATION: {state}\n")
            out.write(f"HEADLINE: {c.get('rep_title')}\n")
            out.write(f"METRICS: {c.get('report_count')} Articles | {c.get('distinct_domains_count')} Publishers | {c.get('lifespan_hours')}h Lifespan\n")
            out.write(f"DATE: {c.get('most_recent_date')}\n")
            out.write(f"UNDERLYING ARTICLES:\n")
            for art in c.get("articles", []):
                out.write(f"  - ({art.get('source')}): {art.get('title')}\n")
            out.write(f"\n")

print(f"Exported clean audit text files to: {export_dir}")
