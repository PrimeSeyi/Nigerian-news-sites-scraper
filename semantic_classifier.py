import os
import json
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")
PROMPT_FILE = os.path.join(BASE_DIR, "classifier_prompt.txt")
CACHE_FILE = os.path.join(BASE_DIR, "dashboard_viewer", "semantic_cache.json")

def load_env():
    """Simple zero-dependency .env parser."""
    if not os.path.exists(ENV_FILE):
        return
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ[k] = v

def fallback_classify(title):
    """Fallback heuristic if LLM API key is missing or network times out."""
    tl = title.lower()
    elite_kw = ['tinubu', 'presidency', 'minister', 'senate', 'reps', 'apc', 'pdp', 'court', 'governor', 'zulum', 'soludo', 'shettima', 'fubara', 'wike', 'atiku', 'obi', 'lawal', 'efcc', 'police', 'military', 'inec', 'agf']
    kinetic_kw = ['kill', 'dead', 'abduct', 'kidnap', 'gunmen', 'bandit', 'terror', 'massacre', 'casualty', 'invade', 'ambush', 'slain', 'hostage', 'boko haram', 'iswap']
    if any(k in tl for k in elite_kw): return "ELITE/VIP"
    if any(k in tl for k in kinetic_kw): return "KINETIC/RURAL"
    return "OTHER/GENERAL"

def classify_batch_via_llm(batch_dict, api_key, model, base_url, system_prompt):
    """Calls OpenAI-compatible /v1/chat/completions endpoint."""
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(batch_dict)}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0
    }
    
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
            content_str = resp_body["choices"][0]["message"]["content"]
            parsed = json.loads(content_str)
            return parsed
    except Exception as e:
        print(f"⚠️ LLM API Error ({e}). Using fallback classification for batch...")
        return {cid: fallback_classify(title) for cid, title in batch_dict.items()}

def classify_clusters(all_clusters_map):
    """
    Main entrypoint called by cluster_from_csvs.py.
    Loads cache, isolates unclassified clusters, queries LLM gatekeeper, updates cache.
    Returns: dict mapping cluster_id -> 'ELITE/VIP' | 'KINETIC/RURAL' | 'OTHER/GENERAL'
    """
    load_env()
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "gemini-2.5-flash-lite")
    base_url = os.environ.get("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    
    system_prompt = ""
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            system_prompt = f.read()

    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    unclassified = {}
    for cid, cdata in all_clusters_map.items():
        if cid not in cache:
            unclassified[cid] = cdata.get("rep_title", "")

    if unclassified:
        print(f"Gatekeeper: Found {len(unclassified)} new unclassified clusters.")
        if not api_key:
            print("ℹ️ No LLM_API_KEY configured in .env. Using OSINT fallback classification...")
            for cid, title in unclassified.items():
                cache[cid] = fallback_classify(title)
        else:
            # Batch in chunks of 50
            items = list(unclassified.items())
            chunk_size = 50
            for i in range(0, len(items), chunk_size):
                chunk = dict(items[i:i + chunk_size])
                print(f"-> Sending batch {i//chunk_size + 1} ({len(chunk)} items) to LLM ({model})...")
                res = classify_batch_via_llm(chunk, api_key, model, base_url, system_prompt)
                
                # Normalize response keys & values
                for cid, cat in res.items():
                    cat_upper = str(cat).upper().replace(" ", "")
                    if "ELITE" in cat_upper or "VIP" in cat_upper:
                        cache[cid] = "ELITE/VIP"
                    elif "KINETIC" in cat_upper or "RURAL" in cat_upper:
                        cache[cid] = "KINETIC/RURAL"
                    else:
                        cache[cid] = "OTHER/GENERAL"
                
                # Catch any missed IDs in chunk
                for cid, title in chunk.items():
                    if cid not in cache:
                        cache[cid] = fallback_classify(title)

        # Save delta cache
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)
        print(f"Gatekeeper: Saved updated delta cache ({len(cache)} total items) to {CACHE_FILE}")

    # Map output keys to standard bucket names (Elite/VIP, Kinetic/Rural, Other/General)
    normalized_cache = {}
    for cid, cat in cache.items():
        if cat == "ELITE/VIP": normalized_cache[cid] = "Elite/VIP"
        elif cat == "KINETIC/RURAL": normalized_cache[cid] = "Kinetic/Rural"
        else: normalized_cache[cid] = "Other/General"
        
    return normalized_cache

if __name__ == "__main__":
    # Dry-run test
    dummy_clusters = {
        "test-1": {"rep_title": "Brymo attacks Big 3 narrative, says it stifles new talent"},
        "test-2": {"rep_title": "Tinubu condemns death of retired general Rabe in kidnappers’ custody"},
        "test-3": {"rep_title": "Boko Haram Kills Eight Soldiers in Borno Base Attack"}
    }
    res = classify_clusters(dummy_clusters)
    print("Test Results:", json.dumps(res, indent=2))
