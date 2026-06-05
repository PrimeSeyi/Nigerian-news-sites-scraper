import os
import csv
import re
import shutil
import pymysql

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
            
    conn.close()
    print("\n=== Ingestion Complete ===")

if __name__ == "__main__":
    main()
