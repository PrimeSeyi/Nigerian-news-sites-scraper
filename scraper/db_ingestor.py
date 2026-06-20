import os
import csv
import re
import json
import shutil
import pymysql
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
import numpy as np
from datetime import datetime, timezone


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
        region_clean = region.replace("The ", "").lower()
        if re.search(rf'\bthe {re.escape(region_clean)}\b', title_lower) or re.search(rf'\bnorthern nigeria\b', title_lower):
            if "north" in region_clean: return "The North"
            if "south" in region_clean: return "The South"
            if "east" in region_clean: return "The East"
            if "west" in region_clean: return "The West"
        if re.search(rf'\bmiddle belt\b', title_lower):
            return "Middle Belt"
            
    return None

# --- Configuration ---
DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("DB_PORT", 3306))
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "rootpassword")
DB_NAME = os.environ.get("DB_NAME", "news_db")

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")

def get_db_connection():
    # Connect without DB first to ensure it exists
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        autocommit=True
    )
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME};")
    conn.close()

    # Now connect to the actual DB
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )

def parse_table_name(filename):
    """
    Strips 'manual_', trailing dates, and '.csv' to generate the clean table name.
    Example: manual_instablog9ja_api_2026-06-03_12-28-21.csv -> instablog9ja_api
    """
    name = filename.replace("manual_", "")
    name = re.sub(r'_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.csv$', '', name)
    name = name.replace(".csv", "")
    return name.lower()

def identify_csv_type(headers):
    """
    Returns the schema type based on the CSV headers.
    """
    headers = [h.strip().lower() for h in headers]
    if "uuid" in headers and "slug" in headers:
        return "wp_api"
    elif "guid" in headers and "subdomain" in headers:
        return "deep_rss"
    elif "url" in headers and "source" in headers:
        return "generic_rss"
    else:
        return "unknown"

def create_table_if_not_exists(cursor, table_name, csv_type):
    if csv_type == "wp_api":
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uuid BIGINT,
                guid VARCHAR(768),
                slug VARCHAR(768),
                title TEXT,
                link VARCHAR(768) UNIQUE,
                category TEXT,
                date_time VARCHAR(255)
            );
        """)
    elif csv_type == "deep_rss":
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category TEXT,
                title TEXT,
                link VARCHAR(768),
                guid VARCHAR(768) UNIQUE,
                date_time VARCHAR(255),
                subdomain VARCHAR(255)
            );
        """)
    elif csv_type == "generic_rss":
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                uid VARCHAR(255),
                url VARCHAR(768) UNIQUE,
                title TEXT,
                date_time VARCHAR(255),
                source VARCHAR(255)
            );
        """)
    else:
        raise ValueError(f"Unknown CSV type '{csv_type}' for table '{table_name}'")

def process_csv_file(conn, file_path, filename):
    table_name = parse_table_name(filename)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print(f"[-] {filename} is empty. Skipping.")
            return

        csv_type = identify_csv_type(headers)
        if csv_type == "unknown":
            print(f"[-] Could not identify schema for {filename}. Headers: {headers}. Skipping.")
            return

        with conn.cursor() as cursor:
            create_table_if_not_exists(cursor, table_name, csv_type)
            
            rows_processed = 0
            rows_inserted = 0
            
            for row in reader:
                if not row: continue
                
                # Normalize row length to match headers exactly
                if len(row) < len(headers):
                    row.extend([""] * (len(headers) - len(row)))
                elif len(row) > len(headers):
                    row = row[:len(headers)]
                    
                if csv_type == "wp_api":
                    # ['uuid', 'guid', 'slug', 'title', 'link', 'category', 'date_time']
                    uuid_val = row[0] if row[0].isdigit() else 0
                    query = f"INSERT IGNORE INTO `{table_name}` (uuid, guid, slug, title, link, category, date_time) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    affected = cursor.execute(query, (uuid_val, row[1], row[2], row[3], row[4], row[5], row[6]))
                    
                elif csv_type == "deep_rss":
                    # ['category', 'title', 'link', 'guid', 'date_time', 'subdomain']
                    query = f"INSERT IGNORE INTO `{table_name}` (category, title, link, guid, date_time, subdomain) VALUES (%s, %s, %s, %s, %s, %s)"
                    affected = cursor.execute(query, (row[0], row[1], row[2], row[3], row[4], row[5]))
                    
                elif csv_type == "generic_rss":
                    # ['id', 'url', 'title', 'date_time', 'source']
                    query = f"INSERT IGNORE INTO `{table_name}` (uid, url, title, date_time, source) VALUES (%s, %s, %s, %s, %s)"
                    affected = cursor.execute(query, (row[0], row[1], row[2], row[3], row[4]))
                
                rows_processed += 1
                rows_inserted += affected
                
            conn.commit()
            
            # Archive verified file
            os.makedirs(ARCHIVE_DIR, exist_ok=True)
            archive_path = os.path.join(ARCHIVE_DIR, filename)
            shutil.move(file_path, archive_path)
            
            print(f"[+] Processed {filename} -> `{table_name}` | Rows: {rows_processed} | Inserted (New): {rows_inserted}")

def cluster_recent_incidents(conn):
    print("\n--- Running Semantic Incident Clustering ---")
    
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `incidents` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                cluster_id INT,
                headline TEXT,
                source_table VARCHAR(50),
                article_id INT,
                url VARCHAR(768),
                published_date DATETIME,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY `unique_article` (`source_table`, `article_id`)
            );
        """)
        conn.commit()

    all_articles = []
    
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = [row['Tables_in_' + DB_NAME] for row in cursor.fetchall()]
        
        for table in tables:
            if table == 'incidents': continue
            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = [c['Field'] for c in cursor.fetchall()]
            
            if 'uuid' in columns and 'slug' in columns:
                cursor.execute(f"SELECT id, title, link as url, date_time FROM `{table}`")
                for row in cursor.fetchall():
                    all_articles.append({'id': row['id'], 'title': row['title'], 'url': row['url'], 'date_time': row['date_time'], 'source_table': table})
            elif 'guid' in columns and 'subdomain' in columns:
                cursor.execute(f"SELECT id, title, link as url, date_time FROM `{table}`")
                for row in cursor.fetchall():
                    all_articles.append({'id': row['id'], 'title': row['title'], 'url': row['url'], 'date_time': row['date_time'], 'source_table': table})
            elif 'source' in columns and 'uid' in columns:
                cursor.execute(f"SELECT id, title, url, date_time FROM `{table}`")
                for row in cursor.fetchall():
                    all_articles.append({'id': row['id'], 'title': row['title'], 'url': row['url'], 'date_time': row['date_time'], 'source_table': table})

    print(f"Total articles extracted from DB for clustering: {len(all_articles)}")
    if not all_articles:
        return

    keywords_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "keywords.json")
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
                a['extracted_state'] = extract_state(title)
                filtered_articles.append(a)
            except Exception:
                pass
                
    print(f"Filtered down to {len(filtered_articles)} security-related articles.")
    if len(filtered_articles) < 2:
        print("Not enough security articles to cluster.")
        return

    print("Loading SentenceTransformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
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
            if state_i is not None and state_j is not None and check_geographic_conflict(state_i, state_j):
                custom_distances[i, j] = 2.0
            else:
                custom_distances[i, j] = base_distances[i, j]

    print("Running Agglomerative Clustering globally with strict 0.35 threshold...")
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.35,
        metric='precomputed',
        linkage='average'
    )
    labels = clustering_model.fit_predict(custom_distances)

    with conn.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE `incidents`")
        inserted = 0
        for i, label in enumerate(labels):
            a = filtered_articles[i]
            query = """
                INSERT INTO `incidents` 
                (cluster_id, headline, source_table, article_id, url, published_date) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (int(label), a['title'], a['source_table'], a['id'], a['url'], a['parsed_date']))
            inserted += 1
        conn.commit()
        
    print(f"Stored {inserted} incidents grouped into {len(set(labels))} unique clusters in the DB.")

def main():
    print("=== MySQL Database Ingestor ===")
    
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found.")
        return

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    
    if not csv_files:
        print("No CSV files found in data directory.")
        return

    print(f"Found {len(csv_files)} CSV files. Connecting to database...")
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"Database connection failed: {e}")
        return

    print("Connected successfully. Beginning ingestion...\n")
    for filename in csv_files:
        file_path = os.path.join(DATA_DIR, filename)
        try:
            process_csv_file(conn, file_path, filename)
        except Exception as e:
            print(f"[-] Error processing {filename}: {e}")
            conn.rollback()
            
    cluster_recent_incidents(conn)
    conn.close()
    print("\n=== Ingestion Complete ===")

if __name__ == "__main__":
    main()
