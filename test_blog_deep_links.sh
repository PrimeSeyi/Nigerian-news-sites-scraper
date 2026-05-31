#!/bin/bash

BLOGS=(
  "https://www.bellanaija.com/"
  "https://www.lindaikejisblog.com/"
  "https://www.zikoko.com/"
  "https://techcabal.com/"
  "https://techpoint.africa/"
  "https://www.ogbongeblog.com/"
  "https://ynaija.com/"
  "https://tooxclusive.com/"
  "https://notjustok.com/"
  "https://www.36ng.ng/"
  "https://www.stelladimokokorkus.com/"
  "https://instablog9ja.com/"
)

echo "Testing Deep Links for ${#BLOGS[@]} Top Nigerian Blogs..."
echo "--------------------------------------------------------"

for site in "${BLOGS[@]}"; do
  # Fetch the homepage
  homepage_html=$(curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" -m 15 "$site")
  
  # Extract the longest absolute link
  article_url=$(echo "$homepage_html" | grep -oP 'href="\K'"$site"'[^"]+' | grep -v -E '\.(css|js|png|jpg|jpeg|gif|svg|ico)$' | awk '{ print length, $0 }' | sort -n | tail -n 1 | cut -d" " -f2)
  
  # If we couldn't find an absolute link, try relative links and prepend the domain
  if [ -z "$article_url" ]; then
      domain=$(echo "$site" | grep -oP '^https?://[^/]+')
      rel_link=$(echo "$homepage_html" | grep -oP 'href="\K/[^"]+' | grep -v -E '\.(css|js|png|jpg|jpeg|gif|svg|ico)$' | awk '{ print length, $0 }' | sort -n | tail -n 1 | cut -d" " -f2)
      if [ -n "$rel_link" ]; then
          article_url="${domain}${rel_link}"
      fi
  fi
  
  if [ -z "$article_url" ]; then
      echo "[ERROR] $site - Could not extract an article link from homepage."
      continue
  fi

  echo "Site: $site"
  echo "Link: $article_url"
  
  # Curl the article link
  response=$(curl -s -L -D - -o /dev/null -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36" -m 15 "$article_url" || echo "CURL_ERROR")
  
  if [[ "$response" == *"CURL_ERROR"* ]]; then
     echo "  -> [ERROR] Could not connect or timed out"
     echo ""
     continue
  fi

  http_code=$(echo "$response" | grep -i "^HTTP/" | tail -n 1 | awk '{print $2}')
  
  if echo "$response" | grep -iq "server: cloudflare"; then
     cloudflare="Yes"
  else
     cloudflare="No"
  fi

  if [[ "$http_code" == "403" && "$cloudflare" == "Yes" ]]; then
     echo "  -> [BLOCKED] HTTP $http_code (Cloudflare Block Detected)"
  elif [[ "$http_code" == "403" || "$http_code" == "503" ]]; then
     echo "  -> [BLOCKED] HTTP $http_code"
  else
     echo "  -> [OK] HTTP $http_code"
  fi
  echo ""
done
