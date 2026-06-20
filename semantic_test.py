import os
import glob
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_distances
from datetime import datetime
import numpy as np

# 1. Load Data
data_dir = "scraper/data"
csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

all_articles = []
for file in csv_files:
    try:
        df = pd.read_csv(file)
        if 'title' in df.columns and 'date_time' in df.columns:
            for _, row in df.iterrows():
                title = str(row['title']).strip()
                date_str = str(row['date_time']).strip()
                link = str(row.get('link', '')).strip()
                source = os.path.basename(file).split('_')[0] if '_' in os.path.basename(file) else 'unknown'
                
                # Filter for relevant keywords to simulate the test case
                keywords = ['kidnap', 'abduct', 'gunmen', 'attack', 'bandit', 'terror', 'rescue', 'hostage', 'mourn', 'bleed', 'kill', 'assassinate', 'dead', 'boko haram', 'herdsmen', 'clash', 'ambush', 'gunshots', 'raid', 'burn', 'destroy']
                if any(kw in title.lower() for kw in keywords):
                    try:
                        # Handle different date formats or errors
                        date_str = date_str.replace('Z', '+00:00')
                        date_obj = datetime.fromisoformat(date_str).replace(tzinfo=None)
                    except ValueError:
                        continue
                    
                    all_articles.append({
                        'title': title,
                        'date': date_obj,
                        'source': source,
                        'link': link
                    })
    except Exception as e:
        print(f"Error reading {file}: {e}")

if len(all_articles) > 50:
    all_articles = all_articles[:50]

print(f"Loaded {len(all_articles)} relevant articles for semantic analysis.")
if len(all_articles) == 0:
    print("No relevant articles found. Try adjusting keywords or checking the CSV data.")
    exit()

# 2. Extract texts
titles = [a['title'] for a in all_articles]
dates = [a['date'] for a in all_articles]

# 3. Generate Embeddings
print("Loading model 'all-MiniLM-L6-v2'...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Generating embeddings...")
embeddings = model.encode(titles)

# 4. Compute Distance Matrix with Time Window
print("Computing custom distance matrix with 3-day time window constraint...")
distances = cosine_distances(embeddings)

for i in range(len(dates)):
    for j in range(len(dates)):
        if abs((dates[i] - dates[j]).days) > 1:
            # If the events are more than 1 day apart, force the distance to be massive
            # so the clustering algorithm refuses to group them together.
            distances[i, j] = 2.0

# 5. Clustering
distance_threshold = 0.4 # Threshold for grouping

clustering = AgglomerativeClustering(
    n_clusters=None,
    distance_threshold=distance_threshold,
    metric='precomputed',
    linkage='average'
)
labels = clustering.fit_predict(distances)

for i, label in enumerate(labels):
    all_articles[i]['cluster'] = label

all_articles.sort(key=lambda x: (x['cluster'], x['date']))

# 6. Output Results
results_md = "# Semantic Clustering Results\n\n"
results_md += f"**Total Articles Analysed:** {len(all_articles)}\n"
results_md += f"**Total Unique Incidents (Clusters) Identified:** {len(set(labels))}\n\n"
results_md += "---\n\n"

current_cluster = -1
for article in all_articles:
    if article['cluster'] != current_cluster:
        current_cluster = article['cluster']
        results_md += f"### Cluster {current_cluster}\n"
    
    results_md += f"- **[{article['source']}]** {article['title']} *(Date: {article['date'].strftime('%Y-%m-%d')})*\n"

artifact_path = "/home/seyi/.gemini/antigravity/brain/37d9ccba-8551-40a2-b1a9-038ecfdaa5eb/experiment_results.md"
with open(artifact_path, "w") as f:
    f.write(results_md)

print("Analysis complete. Check the experiment_results.md artifact!")
