#!/bin/bash

SITES=(
  "https://www.vanguardngr.com/"
  "https://punchng.com/"
  "https://www.legit.ng/"
  "https://www.premiumtimesng.com/"
  "https://dailypost.ng/"
  "https://guardian.ng/"
  "https://leadership.ng/"
  "https://www.pulse.ng/"
  "https://saharareporters.com/"
  "https://www.thisdaylive.com/"
  "https://www.nairaland.com/"
  "https://www.channelstv.com/"
  "https://www.arise.tv/"
  "https://lindaikejisblog.com/"
  "https://www.informationng.com/"
  "https://www.naijaloaded.com.ng/"
  "https://businessday.ng/"
  "https://www.thecable.ng/"
  "https://dailytrust.com/"
  "https://tribuneonlineng.com/"
)

echo "Testing 20 Nigerian news sites..."
echo "-----------------------------------"

for site in "${SITES[@]}"; do
  response=$(curl -s -L -D - -o /dev/null -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" -m 15 "$site" || echo "CURL_ERROR")
  
  if [[ "$response" == *"CURL_ERROR"* ]]; then
     echo "[ERROR] $site - Could not connect or timed out"
     continue
  fi

  http_code=$(echo "$response" | grep -i "^HTTP/" | tail -n 1 | awk '{print $2}')
  
  if echo "$response" | grep -iq "server: cloudflare"; then
     cloudflare="Yes"
  else
     cloudflare="No"
  fi

  if [[ "$http_code" == "403" && "$cloudflare" == "Yes" ]]; then
     echo "[BLOCKED] $site - HTTP $http_code (Cloudflare Block Detected)"
  elif [[ "$http_code" == "403" || "$http_code" == "503" ]]; then
     echo "[BLOCKED] $site - HTTP $http_code (Cloudflare: $cloudflare)"
  else
     echo "[OK] $site - HTTP $http_code (Cloudflare: $cloudflare)"
  fi
done
