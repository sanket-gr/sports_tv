---
last_mapped_date: 2026-06-15
---

# ⚠️ Concerns

## Technical Debt & Fragility
- **Scraper Reliability**: The core functionality depends entirely on external websites (`watchmmafull.com`, `vidplayer.live`, etc.). Any DOM changes, new anti-bot mechanisms (like Cloudflare Turnstile updates), or URL structure changes will instantly break streams.
- **Obfuscation Cat-and-Mouse**: The bypass scripts (`deobfuscator.js`, `decrypt_player.js`) are inherently fragile because they rely on specific JS variable names, regex patterns, or `eval()` behavior on the host site.
- **MIME Types**: ExoPlayer strictly demands correct MIME types for HLS (`application/x-mpegURL`). Bypassing this requires manual override in `PlaybackActivity.kt` because some stream hosts use `.txt` extensions.

## Security
- **Arbitrary Code Execution**: Bypassing obfuscated players often involves executing untrusted JS via Playwright or Python's JS engines (`execjs`). While currently contained, parsing malicious JS could be a vector.
- **Header Forgery**: Bypassing CORS and Referer policies by proxying traffic or injecting headers works but may violate the external service's Terms of Service and could result in IP bans.

## Performance
- **Playwright Overhead**: Spinning up a browser instance to extract an m3u8 URL is extremely slow compared to native HTTP requests. This causes significant latency when starting a stream on the TV.
- **Android TV Resource Limits**: Older smart TVs have very limited memory and weak GPUs. Complex UI overlays or heavy JS processing on the client side must be strictly avoided. (E.g., Custom `ObjectAnimator` for the ticker had to be removed in favor of native marquee).
