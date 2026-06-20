import re

with open("cluster_from_csvs.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add GEO_ZONES and BROAD_REGIONS
imports_end = content.find("NIGERIAN_STATES = [")
new_constants = """GEO_ZONES = [
    "North West", "North East", "North Central",
    "South West", "South East", "South South"
]

BROAD_REGIONS = [
    "The North", "The South", "The East", "The West", "Middle Belt"
]

"""
content = content[:imports_end] + new_constants + content[imports_end:]

# 2. Update extract_state to catch zones and regions
extract_state_old = """    # Then check exact state names
    for state in NIGERIAN_STATES:
        if re.search(rf'\\b{re.escape(state.lower())}\\b', title_lower):
            return state
            
    return None  # None means "Unresolved Region" or lazy journalism"""

extract_state_new = """    # Then check exact state names (Level 1)
    for state in NIGERIAN_STATES:
        if re.search(rf'\\b{re.escape(state.lower())}\\b', title_lower):
            return state
            
    # Then check Geo-Political Zones (Level 2)
    for zone in GEO_ZONES:
        if re.search(rf'\\b{re.escape(zone.lower())}\\b', title_lower):
            return zone
            
    # Then check Broad Regions (Level 3)
    for region in BROAD_REGIONS:
        # handle "the north" vs just "north" safely. If they say "attack in the north", we catch it.
        # to avoid catching "North" randomly when it means North Korea, we require "The North" or "Northern Nigeria".
        # For simplicity, we just check the region text.
        region_clean = region.replace("The ", "").lower()
        if re.search(rf'\\bthe {re.escape(region_clean)}\\b', title_lower) or re.search(rf'\\bnorthern nigeria\\b', title_lower):
            if "north" in region_clean: return "The North"
            if "south" in region_clean: return "The South"
            if "east" in region_clean: return "The East"
            if "west" in region_clean: return "The West"
        if re.search(rf'\\bmiddle belt\\b', title_lower):
            return "Middle Belt"
            
    return None  # Unresolved"""

content = content.replace(extract_state_old, extract_state_new)

# 3. Update the Post-Cluster Geographic Resolution for Specificity Hierarchy
old_resolve = """        # Identify if any article in this cluster has a specific state
        resolved_state = None
        for item in cluster_items:
            if item['extracted_state'] is not None:
                resolved_state = item['extracted_state']
                break
                
        if resolved_state is None:
            resolved_state = "Unresolved Region"
"""

new_resolve = """        # Identify if any article in this cluster has a specific state using Specificity Hierarchy
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
            resolved_state = "Unresolved Region"
"""

content = content.replace(old_resolve, new_resolve)

with open("cluster_from_csvs.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated cluster_from_csvs.py")
