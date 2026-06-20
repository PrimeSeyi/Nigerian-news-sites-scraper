import re

with open("cluster_from_csvs.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Zone and Region Mapping
imports_end = content.find("GEO_ZONES = [")
new_mappings = """ZONE_MAPPING = {
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
"""
content = content[:imports_end] + new_mappings + "\n" + content[imports_end:]

# 2. Update the conflict loop
old_conflict = """            # Penalty 2: Conflicting State Check
            state_i = states[i]
            state_j = states[j]
            if state_i is not None and state_j is not None and state_i != state_j:
                custom_distances[i, j] = 2.0
            else:
                custom_distances[i, j] = base_distances[i, j]"""

new_conflict = """            # Penalty 2: Conflicting State Check
            state_i = states[i]
            state_j = states[j]
            if state_i is not None and state_j is not None and check_geographic_conflict(state_i, state_j):
                custom_distances[i, j] = 2.0
            else:
                custom_distances[i, j] = base_distances[i, j]"""

content = content.replace(old_conflict, new_conflict)

with open("cluster_from_csvs.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated cluster_from_csvs.py")

# NOW UPDATE db_ingestor.py (which needs the exact same logic)
with open("scraper/db_ingestor.py", "r", encoding="utf-8") as f:
    db_content = f.read()
    
imports_end_db = db_content.find("NIGERIAN_STATES = [")
db_content = db_content[:imports_end_db] + new_mappings + "\n" + db_content[imports_end_db:]

# Add extract_state level 1, 2, 3 changes from patch_v3 to db_ingestor
extract_state_old_db = """    # Then check exact state names
    for state in NIGERIAN_STATES:
        if re.search(rf'\\b{re.escape(state.lower())}\\b', title_lower):
            return state
            
    return None"""

extract_state_new_db = """    # Then check exact state names (Level 1)
    for state in NIGERIAN_STATES:
        if re.search(rf'\\b{re.escape(state.lower())}\\b', title_lower):
            return state
            
    # Then check Geo-Political Zones (Level 2)
    for zone in GEO_ZONES:
        if re.search(rf'\\b{re.escape(zone.lower())}\\b', title_lower):
            return zone
            
    # Then check Broad Regions (Level 3)
    for region in BROAD_REGIONS:
        region_clean = region.replace("The ", "").lower()
        if re.search(rf'\\bthe {re.escape(region_clean)}\\b', title_lower) or re.search(rf'\\bnorthern nigeria\\b', title_lower):
            if "north" in region_clean: return "The North"
            if "south" in region_clean: return "The South"
            if "east" in region_clean: return "The East"
            if "west" in region_clean: return "The West"
        if re.search(rf'\\bmiddle belt\\b', title_lower):
            return "Middle Belt"
            
    return None"""

db_content = db_content.replace(extract_state_old_db, extract_state_new_db)
db_content = db_content.replace(old_conflict, new_conflict)

with open("scraper/db_ingestor.py", "w", encoding="utf-8") as f:
    f.write(db_content)
print("Updated scraper/db_ingestor.py")

