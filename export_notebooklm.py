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

elite_kw = ['tinubu', 'presidency', 'minister', 'senate', 'reps', 'apc', 'pdp', 'court', 'governor', 'zulum', 'soludo', 'shettima', 'fubara', 'wike', 'atiku', 'obi', 'lawal']
kinetic_kw = ['kill', 'dead', 'abduct', 'kidnap', 'gunmen', 'bandit', 'terror', 'attack', 'massacre', 'casualty', 'invade', 'ambush', 'slain', 'hostage', 'boko haram', 'iswap']

all_clusters = {}
for state, sdata in clusters_data.get("states", {}).items():
    for c in sdata.get("clusters", []):
        all_clusters[c["cluster_id"]] = (state, c)

buckets = ["Elite/VIP", "Kinetic/Rural", "Other/General"]

# Track hijacked chains for dedicated export
hijacked_chains_export = []

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
        out.write(f"Pay special attention to Bureaucratic Hijack Rate (BHR) tags where rural massacres\n")
        out.write(f"are co-opted by VIP media theater.\n\n")
        
        for idx, cid in enumerate(cids, 1):
            if cid not in all_clusters:
                continue
            state, c = all_clusters[cid]
            
            # Compute BHR status if Kinetic
            bhr_tag = ""
            if bucket == "Kinetic/Rural":
                children = [all_clusters[ch_id][1] for ch_id in c.get('child_cluster_ids', []) if ch_id in all_clusters]
                elite_children = [ch for ch in children if any(k in ch.get('rep_title', '').lower() for k in elite_kw)]
                if elite_children:
                    bhr_tag = f"⚠️ [BHR STATUS: HIJACKED TO VIP THEATER ({len(elite_children)} VIP Follow-up Clusters)]"
                    hijacked_chains_export.append((state, c, elite_children))
                else:
                    bhr_tag = "✅ [BHR STATUS: ORGANIC GROUND REALITY (Un-hijacked)]"

            out.write(f"--------------------------------------------------------------------------------\n")
            out.write(f"[{idx}] CLUSTER ID: {cid} | LOCATION: {state}\n")
            if bhr_tag:
                out.write(f"{bhr_tag}\n")
            out.write(f"HEADLINE: {c.get('rep_title')}\n")
            out.write(f"METRICS: {c.get('report_count')} Articles | {c.get('distinct_domains_count')} Publishers | {c.get('lifespan_hours')}h Lifespan\n")
            out.write(f"DATE: {c.get('most_recent_date')}\n")
            out.write(f"UNDERLYING ARTICLES:\n")
            for art in c.get("articles", []):
                out.write(f"  - ({art.get('source')}): {art.get('title')}\n")
            out.write(f"\n")

# 4th File: Dedicated BHR Hijack Audit
bhr_path = os.path.join(export_dir, "bureaucratic_hijack_rate_audit.txt")
with open(bhr_path, "w", encoding="utf-8") as out:
    out.write(f"================================================================================\n")
    out.write(f" NOTEBOOK LM FORENSIC AUDIT // BUREAUCRATIC HIJACK RATE (BHR) CHAINS\n")
    out.write(f" TOTAL HIJACKED INCIDENT CHAINS: {len(hijacked_chains_export)}\n")
    out.write(f"================================================================================\n\n")
    out.write(f"INSTRUCTIONS FOR NOTEBOOK LM:\n")
    out.write(f"Below are the exact Kinetic/Rural tragedy incidents that mutated into political VIP theater.\n")
    out.write(f"Examine the Patriarch incident headline and its downstream Elite VIP child clusters.\n")
    out.write(f"Determine if the media co-opted the tragedy for political point-scoring or bureaucratic optics.\n\n")
    
    for idx, (state, pat, elites) in enumerate(hijacked_chains_export, 1):
        out.write(f"================================================================================\n")
        out.write(f"CHAIN #{idx} // PATRIARCH INCIDENT (GROUND REALITY) | LOCATION: {state}\n")
        out.write(f"PATRIARCH HEADLINE: {pat.get('rep_title')}\n")
        out.write(f"PATRIARCH METRICS: {pat.get('report_count')} Articles | {pat.get('lifespan_hours')}h Lifespan\n")
        out.write(f"PATRIARCH ARTICLES:\n")
        for art in pat.get("articles", []):
            out.write(f"  * ({art.get('source')}): {art.get('title')}\n")
        out.write(f"\n   ↓↓↓ MUTATED DOWNSTREAM INTO ELITE THEATER ({len(elites)} FOLLOW-UPS) ↓↓↓\n\n")
        for e_idx, ech in enumerate(elites, 1):
            out.write(f"   [Follow-up #{e_idx}] ELITE HEADLINE: {ech.get('rep_title')}\n")
            out.write(f"   METRICS: {ech.get('report_count')} Articles | {ech.get('lifespan_hours')}h Lifespan\n")
            out.write(f"   ARTICLES:\n")
            for eart in ech.get("articles", []):
                out.write(f"     - ({eart.get('source')}): {eart.get('title')}\n")
            out.write(f"\n")

# 5th File: Keywords Taxonomy Reference
kw_path = os.path.join(export_dir, "keywords_taxonomy.txt")
with open(kw_path, "w", encoding="utf-8") as out:
    out.write("================================================================================\n")
    out.write(" NOTEBOOK LM FORENSIC AUDIT REFERENCE // KEYWORD TAXONOMY & SORTING VECTORS\n")
    out.write("================================================================================\n\n")
    out.write("1. ELITE / VIP POLITICAL THEATER VECTORS (elite_kw):\n")
    for k in elite_kw: out.write(f"  * {k}\n")
    out.write("\n2. KINETIC / RURAL MASSACRES VECTORS (kinetic_kw):\n")
    for k in kinetic_kw: out.write(f"  * {k}\n")
    out.write("\n3. OTHER / GENERAL NEWS:\n  * Any headline triggering neither vector list.\n\n")
    out.write("FORENSIC WARNING: Flat string vectors without NER are vulnerable to metaphorical\n")
    out.write("false positives (e.g. pop-culture 'attacks' or election 'bandits').\n")

print(f"Exported clean audit text files + BHR telemetry + Keywords Taxonomy to: {export_dir}")
