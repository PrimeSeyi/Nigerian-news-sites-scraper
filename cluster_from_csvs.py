import os
import csv
import json
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
import numpy as np
from collections import defaultdict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraper", "data")
DASHBOARD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_viewer")

ZONE_MAPPING = {
    "North West": ["Kaduna", "Kano", "Katsina", "Kebbi", "Jigawa", "Sokoto", "Zamfara"],
    "North East": ["Adamawa", "Bauchi", "Borno", "Gombe", "Taraba", "Yobe"],
    "North Central": ["Benue", "Kogi", "Kwara", "Nasarawa", "Niger", "Plateau", "FCT"],
    "South West": ["Ekiti", "Lagos", "Ogun", "Ondo", "Osun", "Oyo"],
    "South East": ["Abia", "Anambra", "Ebonyi", "Enugu", "Imo"],
    "South South": ["Akwa Ibom", "Bayelsa", "Cross River", "Delta", "Edo", "Rivers"]
}

REGION_MAPPING = {
    "The North": ["North West", "North East", "North Central"],
    "The South": ["South West", "South East", "South South"],
    "The West": ["South West"],
    "The East": ["South East", "North East"],
    "Middle Belt": ["North Central"]
}

def get_zone_for_state(state):
    for zone, states in ZONE_MAPPING.items():
        if state in states: return zone
    return None

def get_regions_for_zone(zone):
    regions = []
    for region, zones in REGION_MAPPING.items():
        if zone in zones: regions.append(region)
    return regions

def check_geographic_conflict(state1, state2):
    if state1 == state2:
        return False
        
    # Check if one is a state and one is its parent zone
    if state1 in NIGERIAN_STATES and state2 in GEO_ZONES:
        return get_zone_for_state(state1) != state2
    if state2 in NIGERIAN_STATES and state1 in GEO_ZONES:
        return get_zone_for_state(state2) != state1
        
    # Check if one is a state and one is its parent broad region
    if state1 in NIGERIAN_STATES and state2 in BROAD_REGIONS:
        z1 = get_zone_for_state(state1)
        if z1: return state2 not in get_regions_for_zone(z1)
    if state2 in NIGERIAN_STATES and state1 in BROAD_REGIONS:
        z2 = get_zone_for_state(state2)
        if z2: return state1 not in get_regions_for_zone(z2)
        
    # Check if one is a zone and one is its parent broad region
    if state1 in GEO_ZONES and state2 in BROAD_REGIONS:
        return state2 not in get_regions_for_zone(state1)
    if state2 in GEO_ZONES and state1 in BROAD_REGIONS:
        return state1 not in get_regions_for_zone(state2)
        
    # If they are both states, both zones, or both regions (and not equal), they conflict
    return True

GEO_ZONES = [
    "North West", "North East", "North Central",
    "South West", "South East", "South South"
]

BROAD_REGIONS = [
    "The North", "The South", "The East", "The West", "Middle Belt"
]

NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", 
    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", 
    "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", 
    "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
    "FCT"
]

CITY_TO_STATE = {
    'minna': 'Niger', 'ikeja': 'Lagos', 'lagos': 'Lagos', 'ibadan': 'Oyo',
    'maiduguri': 'Borno', 'benin': 'Edo', 'port harcourt': 'Rivers',
    'abuja': 'FCT', 'fct': 'FCT', 'jos': 'Plateau', 'kano': 'Kano',
    'kaduna': 'Kaduna', 'enugu': 'Enugu', 'asaba': 'Delta', 'warri': 'Delta',
    'onitsha': 'Anambra', 'awka': 'Anambra', 'aba': 'Abia', 'umuahia': 'Abia',
    'calabar': 'Cross River', 'uyo': 'Akwa Ibom', 'makurdi': 'Benue',
    'yola': 'Adamawa', 'bauchi': 'Bauchi', 'yenagoa': 'Bayelsa',
    'abakaliki': 'Ebonyi', 'ado ekiti': 'Ekiti', 'gombe': 'Gombe',
    'owerri': 'Imo', 'dutse': 'Jigawa', 'katsina': 'Katsina',
    'birnin kebbi': 'Kebbi', 'lokoja': 'Kogi', 'ilorin': 'Kwara',
    'lafia': 'Nasarawa', 'abeokuta': 'Ogun', 'akure': 'Ondo',
    'osogbo': 'Osun', 'sokoto': 'Sokoto', 'jalingo': 'Taraba',
    'damaturu': 'Yobe', 'gusau': 'Zamfara'
}

import re

def extract_state(title):
    title_lower = title.lower()
    
    # First check cities
    for city, state in CITY_TO_STATE.items():
        if re.search(rf'\b{re.escape(city)}\b', title_lower):
            return state
            
    # Then check exact state names (Level 1)
    for state in NIGERIAN_STATES:
        if re.search(rf'\b{re.escape(state.lower())}\b', title_lower):
            return state
            
    # Then check Geo-Political Zones (Level 2)
    for zone in GEO_ZONES:
        if re.search(rf'\b{re.escape(zone.lower())}\b', title_lower):
            return zone
            
    # Then check Broad Regions (Level 3)
    for region in BROAD_REGIONS:
        # handle "the north" vs just "north" safely. If they say "attack in the north", we catch it.
        # to avoid catching "North" randomly when it means North Korea, we require "The North" or "Northern Nigeria".
        # For simplicity, we just check the region text.
        region_clean = region.replace("The ", "").lower()
        if re.search(rf'\bthe {re.escape(region_clean)}\b', title_lower) or re.search(rf'\bnorthern nigeria\b', title_lower):
            if "north" in region_clean: return "The North"
            if "south" in region_clean: return "The South"
            if "east" in region_clean: return "The East"
            if "west" in region_clean: return "The West"
        if re.search(rf'\bmiddle belt\b', title_lower):
            return "Middle Belt"
            
    return None  # Unresolved

def main():
    if not os.path.exists(DASHBOARD_DIR):
        os.makedirs(DASHBOARD_DIR)

    print("Reading CSV files from", DATA_DIR)
    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    
    all_articles = []
    
    for filename in csv_files:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                continue
            
            headers = [h.strip().lower() for h in headers]
            
            for row in reader:
                if not row: continue
                if len(row) < len(headers):
                    row.extend([""] * (len(headers) - len(row)))
                elif len(row) > len(headers):
                    row = row[:len(headers)]
                    
                row_dict = dict(zip(headers, row))
                
                title = row_dict.get('title', '')
                url = row_dict.get('link', row_dict.get('url', ''))
                date_time = row_dict.get('date_time', '')
                
                all_articles.append({
                    'title': title,
                    'url': url,
                    'date_time': date_time,
                    'source': filename
                })

    # Deduplicate by URL
    unique_urls = set()
    deduped_articles = []
    for a in all_articles:
        url = a['url'].strip()
        if not url or url in unique_urls:
            continue
        unique_urls.add(url)
        deduped_articles.append(a)
    all_articles = deduped_articles

    print(f"Total unique raw articles read: {len(all_articles)}")
    
    keywords_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "keywords.json")
    try:
        with open(keywords_path, 'r', encoding='utf-8') as f:
            keywords = json.load(f)
            print(f"Loaded {len(keywords)} keywords from central file.")
    except Exception as e:
        print(f"Could not load keywords.json: {e}")
        return
    
    filtered_articles = []
    for a in all_articles:
        title = str(a['title']).strip()
        if any(kw.lower() in title.lower() for kw in keywords):
            try:
                date_str = str(a['date_time'])
                if not date_str or date_str.lower() == 'no date': continue
                dt = pd.to_datetime(date_str)
                if dt.tzinfo is not None:
                    dt = dt.tz_convert('UTC').tz_localize(None)
                a['parsed_date'] = dt
                a['date_formatted'] = dt.strftime('%Y-%m-%d %H:%M')
                a['extracted_state'] = extract_state(title)
                filtered_articles.append(a)
            except Exception:
                pass
                
    print(f"Filtered down to {len(filtered_articles)} security-related articles.")
    if len(filtered_articles) < 2:
        print("Not enough articles.")
        return
        
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Pre-compute prototypes for Zero-Shot classification of unresolved clusters
    p_local = "News about Nigeria, Nigerian politics, local states, domestic security, and national events."
    p_foreign = "International news about foreign countries, global events, the United States, Europe, Africa, and abroad."
    enc_local = model.encode([p_local])
    enc_foreign = model.encode([p_foreign])
    
    titles = [a['title'] for a in filtered_articles]
    dates = [a['parsed_date'] for a in filtered_articles]
    states = [a['extracted_state'] for a in filtered_articles]
    
    print("Encoding sentences...")
    embeddings = model.encode(titles)

    print("Computing custom distance matrix with Conflicting State and 24-hour penalties...")
    base_distances = cosine_distances(embeddings)
    n_samples = len(filtered_articles)
    custom_distances = np.zeros((n_samples, n_samples))

    for i in range(n_samples):
        for j in range(n_samples):
            if i == j:
                custom_distances[i, j] = 0.0
                continue
                
            # Penalty 1: Temporal Constraint (24 hours max)
            time_diff = abs((dates[i] - dates[j]).total_seconds() / 3600)
            if time_diff > 24:
                custom_distances[i, j] = 2.0
                continue
                
            # Penalty 2: Conflicting State Check
            state_i = states[i]
            state_j = states[j]
            
            # If both have explicit states and they don't match, NEVER cluster them.
            if state_i is not None and state_j is not None and state_i != state_j:
                custom_distances[i, j] = 2.0
            else:
                # One or both lack a specific state (The "Parent Method" exception)
                # Let the AI cosine distance decide
                custom_distances[i, j] = base_distances[i, j]

    print("Running Agglomerative Clustering globally with 0.40 threshold...")
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.40,  # Relaxed slightly from 0.35 to allow closely related articles
        metric='precomputed',
        linkage='average'
    )
    labels = clustering_model.fit_predict(custom_distances)
    
    # Group results into global clusters
    cluster_dict = defaultdict(list)
    for idx, label in enumerate(labels):
        cluster_dict[label].append(filtered_articles[idx])
        
    # Post-Cluster Geographic Resolution
    final_clusters_by_state = defaultdict(dict)
    
    for label, cluster_items in cluster_dict.items():
        # Identify if any article in this cluster has a specific state using Specificity Hierarchy
        level1_states = [s for s in cluster_items if s['extracted_state'] in NIGERIAN_STATES]
        level2_zones = [s for s in cluster_items if s['extracted_state'] in GEO_ZONES]
        level3_regions = [s for s in cluster_items if s['extracted_state'] in BROAD_REGIONS]
        
        resolved_state = None
        
        if level1_states:
            # Use the most frequent Level 1 state
            from collections import Counter
            counts = Counter([s['extracted_state'] for s in level1_states])
            resolved_state = counts.most_common(1)[0][0]
        elif level2_zones:
            # Fallback to most frequent Level 2 zone
            from collections import Counter
            counts = Counter([s['extracted_state'] for s in level2_zones])
            resolved_state = counts.most_common(1)[0][0]
        elif level3_regions:
            # Fallback to most frequent Level 3 region
            from collections import Counter
            counts = Counter([s['extracted_state'] for s in level3_regions])
            resolved_state = counts.most_common(1)[0][0]
        else:
            # Apply NLP Prototype Classification for unresolved clusters
            cluster_items.sort(key=lambda x: x['parsed_date'], reverse=True)
            top_title = cluster_items[0]['title']
            
            # Hard-coded Local Override to prevent false positives in "Abroad"
            strong_local_keywords = ["nigeria", "tinubu", "buhari", "efcc", "dss", "ncdc", "inec", "nlc", "ndlea", "nsitf", "fct", "abuja"]
            has_local_kw = False
            for item in cluster_items:
                if any(kw in item['title'].lower() for kw in strong_local_keywords):
                    has_local_kw = True
                    break
                    
            if has_local_kw:
                resolved_state = "National / General Nigerian"
            else:
                enc_title = model.encode([top_title])
                d_local = cosine_distances(enc_title, enc_local)[0][0]
                d_foreign = cosine_distances(enc_title, enc_foreign)[0][0]
                if d_local < d_foreign:
                    resolved_state = "National / General Nigerian"
                else:
                    resolved_state = "Abroad / International"
            
        # Assign this state to all items in the cluster and group it
        cluster_id = f"{resolved_state}-C{label}"
        
        # Sort cluster items by date descending
        cluster_items.sort(key=lambda x: x['parsed_date'], reverse=True)
        
        final_clusters_by_state[resolved_state][cluster_id] = cluster_items

    # Format output for JSON dashboard
    output_data = {
        "metadata": {
            "total_articles": len(all_articles),
            "filtered_articles": len(filtered_articles),
            "total_clusters": len(cluster_dict)
        },
        "states": {}
    }

    # Sort states by number of clusters (or incidents) descending
    sorted_states = sorted(final_clusters_by_state.keys(), key=lambda s: len(final_clusters_by_state[s]), reverse=True)
    
    for state in sorted_states:
        clusters = final_clusters_by_state[state]
        # Sort clusters within state by size descending
        sorted_clusters_list = sorted(clusters.items(), key=lambda c: len(c[1]), reverse=True)
        
        state_clusters = []
        for c_id, items in sorted_clusters_list:
            clean_items = []
            for item in items:
                clean_items.append({
                    "title": item["title"],
                    "url": item["url"],
                    "date": item["date_formatted"],
                    "source": item["source"]
                })
            state_clusters.append({
                "cluster_id": c_id,
                "report_count": len(items),
                "most_recent_date": clean_items[0]["date"],
                "articles": clean_items
            })
            
        output_data["states"][state] = {
            "total_clusters": len(clusters),
            "total_reports": sum(len(c) for c in clusters.values()),
            "clusters": state_clusters
        }

    output_path = os.path.join(DASHBOARD_DIR, "clusters.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Clustering complete. Processed {len(cluster_dict)} total clusters across {len(sorted_states)} resolved locations.")
    print(f"Results written to {output_path}")

if __name__ == "__main__":
    main()
