import extractor

url = "https://partner.nonamejose.sx/69acc497/7738feef/404ced5a"
print(f"Testing: {url}")

# Step 1: fetch the page
print("\n[1] Fetching page with browser...")
html = extractor._fetch_with_browser(url)
print(f"    HTML length: {len(html)}")

# Step 2: parse metadata
print("\n[2] Parsing metadata...")
meta = extractor._parse_next_data(html)
print(f"    Meta: {meta}")

# Step 3: look for any iframe in raw HTML
import re
iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
print(f"\n[3] Raw iframe search: {iframes}")

# Step 4: look for any embed URLs
embeds = re.findall(r'https?://[^\s"\'<>]+(?:embed|player|stream)[^\s"\'<>]*', html, re.I)
print(f"\n[4] Embed URLs: {embeds[:5]}")

# Step 5: look for any m3u8
m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html, re.I)
print(f"\n[5] M3U8 URLs: {m3u8s}")

# Save full HTML for inspection
with open('debug_live.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("\n[6] Saved full HTML to debug_live.html")
