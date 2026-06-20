import re
with open("scraper/db_ingestor.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Insert NIGERIAN_STATES, CITY_TO_STATE, and extract_state after imports
imports_end = content.find("\n# --- Configuration ---")
if imports_end != -1:
    state_logic = """
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
        if re.search(rf'\\b{re.escape(city)}\\b', title_lower):
            return state
            
    # Then check exact state names
    for state in NIGERIAN_STATES:
        if re.search(rf'\\b{re.escape(state.lower())}\\b', title_lower):
            return state
            
    return None
"""
    content = content[:imports_end] + "\n" + state_logic + content[imports_end:]

# 2. Add extracted_state assignment
content = content.replace("a['parsed_date'] = dt", "a['parsed_date'] = dt\n                a['extracted_state'] = extract_state(title)")

# 3. Replace the clustering matrix loop
old_loop = """    titles = [a['title'] for a in filtered_articles]
    dates = [a['parsed_date'] for a in filtered_articles]
    
    print("Encoding sentences...")
    embeddings = model.encode(titles)

    print("Computing custom distance matrix with 24-hour constraint...")
    base_distances = cosine_distances(embeddings)
    n_samples = len(filtered_articles)
    custom_distances = np.zeros((n_samples, n_samples))

    for i in range(n_samples):
        for j in range(n_samples):
            if i == j:
                custom_distances[i, j] = 0.0
                continue
            time_diff = abs((dates[i] - dates[j]).total_seconds() / 3600)
            if time_diff > 24:
                custom_distances[i, j] = 2.0
            else:
                custom_distances[i, j] = base_distances[i, j]

    print("Running Agglomerative Clustering...")
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.70,
        metric='precomputed',
        linkage='average'
    )"""

new_loop = """    titles = [a['title'] for a in filtered_articles]
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
            if state_i is not None and state_j is not None and state_i != state_j:
                custom_distances[i, j] = 2.0
            else:
                custom_distances[i, j] = base_distances[i, j]

    print("Running Agglomerative Clustering globally with strict 0.35 threshold...")
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=0.35,
        metric='precomputed',
        linkage='average'
    )"""

content = content.replace(old_loop, new_loop)

with open("scraper/db_ingestor.py", "w", encoding="utf-8") as f:
    f.write(content)
print("db_ingestor.py successfully synchronized with V2 clustering logic.")
