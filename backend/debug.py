import json, re

html = open('debug.html', encoding='utf-8').read()

# 1. Check __NEXT_DATA__
m = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.S)
if m:
    data = json.loads(m.group(1))
    props = data.get("props", {}).get("pageProps", {})
    page_data = props.get("data", props)
    print("=== NEXT_DATA top-level keys:", page_data.keys())
    print("=== Full pageProps (trimmed):")
    print(json.dumps(props, indent=2)[:3000])
else:
    print("No __NEXT_DATA__ found")

# 2. Look for any iframe src in raw HTML
iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
print("\n=== IFRAMES FOUND:", iframes)

# 3. Look for any m3u8 urls
m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html, re.I)
print("\n=== M3U8 URLs FOUND:", m3u8s)

# 4. Look for any 'stream' related keys in scripts
streams = re.findall(r'"stream[^"]*"\s*:\s*"([^"]+)"', html, re.I)
print("\n=== STREAM KEYS:", streams[:10])

# 5. Look for source or file keys
sources = re.findall(r'(?:source|file|src)\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html, re.I)
print("\n=== SOURCE/FILE KEYS:", sources)

# 6. check for any embed/player URLs
embeds = re.findall(r'https?://[^\s"\'<>]+(?:embed|player|stream)[^\s"\'<>]*', html, re.I)
print("\n=== EMBED URLs:", embeds[:10])
