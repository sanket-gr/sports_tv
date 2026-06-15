---
last_mapped_date: 2026-06-15
---

# 🔌 Integrations

## External Services
- **Web Scraping Targets**: The system relies heavily on scraping external sports streaming sites (e.g., `watchmmafull.com`, `vidplayer.live`) to extract HLS (m3u8) URLs.
- **Deobfuscation & Bypasses**: The backend contains specific logic (`deobfuscator.js`, `decrypt_player.js`, `extract_deobfuscator.py`) to bypass Cloudflare and reverse-engineer token/encryption keys from external players.

## Internal APIs
- The Python backend exposes REST API endpoints that the Android TV app consumes via Retrofit.
- These endpoints deliver the curated stream catalog, metadata, and proxy configurations necessary to play the parsed HLS streams.

## Third-Party Libraries
- **Playwright**: Used as an integration to spin up headless/headful browsers to evaluate JavaScript, solve anti-bot challenges, and capture network requests for raw media URLs.
