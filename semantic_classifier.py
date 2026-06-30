import os
import json
import time
import urllib.request
import urllib.error
import re

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

# Precompile word-bounded regex patterns for fallback heuristic matching
OPINION_RX = re.compile(
    r"\b(opinion|editorial|column|sugar and ants|how nigerians kill mathematics|voting bandits|infrastructure attack|assaults on doctors)\b",
    re.IGNORECASE
)
ELITE_RX = re.compile(
    r"\b(tinubu|presidency|minister|senate|reps|apc|pdp|court|governor|zulum|soludo|shettima|fubara|wike|atiku|obi|lawal|inec|agf|arraign|charge|prosecute|suit)\b",
    re.IGNORECASE
)
KINETIC_RX = re.compile(
    r"\b(kill|dead|abduct|kidnap|gunmen|bandit|terror|massacre|casualty|invade|ambush|slain|hostage|boko haram|iswap|air strike|gun duel|shootout)\b",
    re.IGNORECASE
)

def fallback_classify(title):
    """Fallback heuristic using strict word boundaries and Axiom A vs Axiom B rules."""
    tl = title.lower()
    if OPINION_RX.search(tl):
        return "OTHER/GENERAL"
    if ELITE_RX.search(tl):
        return "ELITE/VIP"
    if KINETIC_RX.search(tl):
        return "KINETIC/RURAL"
    return "OTHER/GENERAL"

def classify_batch_via_llm(batch_dict, api_key, model, base_url, system_prompt):
    """Calls OpenAI-compatible /v1/chat/completions endpoint with exponential backoff on 429/503."""
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
    
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
                content_str = resp_body["choices"][0]["message"]["content"]
                parsed = json.loads(content_str)
                return parsed
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and attempt < 3:
                sleep_sec = (attempt + 1) * 15
                print(f"⏳ API quota/throttled (HTTP {e.code}). Retrying in {sleep_sec}s...")
                time.sleep(sleep_sec)
                continue
            print(f"⚠️ LLM HTTP Error ({e}). Using OSINT fallback for batch...")
            return {cid: fallback_classify(title) for cid, title in batch_dict.items()}, True
        except Exception as e:
            print(f"⚠️ LLM API Error ({e}). Using OSINT fallback for batch...")
            return {cid: fallback_classify(title) for cid, title in batch_dict.items()}, True
    return {cid: fallback_classify(title) for cid, title in batch_dict.items()}, True

def classify_clusters(all_clusters_map):
    """
    Main entrypoint called by cluster_from_csvs.py.
    Loads cache, isolates unclassified clusters, queries LLM gatekeeper, updates cache.
    Returns: dict mapping cluster_id -> 'ELITE/VIP' | 'KINETIC/RURAL' | 'OTHER/GENERAL'
    """
    load_env()
    api_key = os.environ.get("LLM_API_KEY", "")
    model = os.environ.get("LLM_MODEL", "mimo-v2.5")
    base_url = os.environ.get("LLM_BASE_URL", "https://api.xiaomimimo.com/v1/")
    
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
            # Batch in chunks of 120
            items = list(unclassified.items())
            chunk_size = 120
            api_exhausted = False
            for i in range(0, len(items), chunk_size):
                chunk = dict(items[i:i + chunk_size])
                if api_exhausted:
                    for cid, title in chunk.items():
                        cache[cid] = fallback_classify(title)
                    # Progressive save even in fallback mode
                    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
                    with open(CACHE_FILE, "w", encoding="utf-8") as f:
                        json.dump(cache, f, indent=2)
                    continue
                print(f"-> Sending batch {i//chunk_size + 1} ({len(chunk)} items) to LLM ({model})...")
                res_tuple = classify_batch_via_llm(chunk, api_key, model, base_url, system_prompt)
                if isinstance(res_tuple, tuple):
                    res, is_fb = res_tuple
                else:
                    res, is_fb = res_tuple, False
                    
                if is_fb:
                    print("⚡ Circuit Breaker Triggered: Quota/balance exhausted. Instant OSINT fallback active for remaining archive...")
                    api_exhausted = True
                else:
                    time.sleep(1.0)
                
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
                
                # Progressive delta save after each batch
                os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f, indent=2)

        # Final guarantee save of cache database
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2)

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
