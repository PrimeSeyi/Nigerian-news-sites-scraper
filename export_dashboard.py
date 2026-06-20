import os
import json
import pymysql
import re
from collections import defaultdict, Counter

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "rootpassword")
DB_NAME = os.environ.get("DB_NAME", "news_db")

NIGERIAN_STATES = [
    "Abia", "Adamawa", "Akwa Ibom", "Anambra", "Bauchi", "Bayelsa", "Benue", "Borno", 
    "Cross River", "Delta", "Ebonyi", "Edo", "Ekiti", "Enugu", "Gombe", "Imo", "Jigawa", 
    "Kaduna", "Kano", "Katsina", "Kebbi", "Kogi", "Kwara", "Lagos", "Nasarawa", "Niger", 
    "Ogun", "Ondo", "Osun", "Oyo", "Plateau", "Rivers", "Sokoto", "Taraba", "Yobe", "Zamfara",
    "FCT"
]

GEO_ZONES = [
    "North West", "North East", "North Central",
    "South West", "South East", "South South"
]

BROAD_REGIONS = [
    "The North", "The South", "The East", "The West", "Middle Belt"
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

def extract_state(title):
    title_lower = title.lower()
    for city, state in CITY_TO_STATE.items():
        if re.search(rf'\b{re.escape(city)}\b', title_lower):
            return state
    for state in NIGERIAN_STATES:
        if re.search(rf'\b{re.escape(state.lower())}\b', title_lower):
            return state
    for zone in GEO_ZONES:
        if re.search(rf'\b{re.escape(zone.lower())}\b', title_lower):
            return zone
    for region in BROAD_REGIONS:
        region_clean = region.replace("The ", "").lower()
        if re.search(rf'\bthe {re.escape(region_clean)}\b', title_lower) or re.search(rf'\bnorthern nigeria\b', title_lower):
            if "north" in region_clean: return "The North"
            if "south" in region_clean: return "The South"
            if "east" in region_clean: return "The East"
            if "west" in region_clean: return "The West"
        if re.search(rf'\bmiddle belt\b', title_lower):
            return "Middle Belt"
    return None

def main():
    print("Connecting to database...")
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        return

    cluster_dict = defaultdict(list)
    total_articles = 0
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM incidents")
        for row in cursor.fetchall():
            row['extracted_state'] = extract_state(row['headline'])
            cluster_dict[row['cluster_id']].append(row)
            total_articles += 1

    final_clusters_by_state = defaultdict(dict)

    for cluster_id, items in cluster_dict.items():
        level1_states = [s['extracted_state'] for s in items if s['extracted_state'] in NIGERIAN_STATES]
        level2_zones = [s['extracted_state'] for s in items if s['extracted_state'] in GEO_ZONES]
        level3_regions = [s['extracted_state'] for s in items if s['extracted_state'] in BROAD_REGIONS]
        
        resolved_state = None
        if level1_states:
            resolved_state = Counter(level1_states).most_common(1)[0][0]
        elif level2_zones:
            resolved_state = Counter(level2_zones).most_common(1)[0][0]
        elif level3_regions:
            resolved_state = Counter(level3_regions).most_common(1)[0][0]
        else:
            resolved_state = "Unresolved Region"

        cluster_key = f"{resolved_state}-C{cluster_id}"
        items.sort(key=lambda x: str(x['published_date']), reverse=True)
        final_clusters_by_state[resolved_state][cluster_key] = items

    output_data = {
        "metadata": {
            "total_articles": total_articles,
            "filtered_articles": total_articles,
            "total_clusters": len(cluster_dict)
        },
        "states": {}
    }

    sorted_states = sorted(final_clusters_by_state.keys(), key=lambda s: len(final_clusters_by_state[s]), reverse=True)
    for state in sorted_states:
        clusters = final_clusters_by_state[state]
        sorted_clusters_list = sorted(clusters.items(), key=lambda c: len(c[1]), reverse=True)
        
        state_clusters = []
        state_reports = 0
        
        for c_id, c_items in sorted_clusters_list:
            cluster_articles = []
            for item in c_items:
                cluster_articles.append({
                    "title": item['headline'],
                    "url": item['url'],
                    "date": str(item['published_date']),
                    "source": item['source_table']
                })
            
            most_recent_date = cluster_articles[0]['date'] if cluster_articles else "Unknown"
            
            state_clusters.append({
                "cluster_id": c_id,
                "report_count": len(cluster_articles),
                "most_recent_date": most_recent_date,
                "articles": cluster_articles
            })
            state_reports += len(cluster_articles)
            
        output_data["states"][state] = {
            "total_clusters": len(state_clusters),
            "total_reports": state_reports,
            "clusters": state_clusters
        }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_viewer")
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    json_path = os.path.join(out_dir, "clusters.json")
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
        
    print(f"Successfully exported {len(cluster_dict)} clusters to {json_path}")

if __name__ == "__main__":
    main()
